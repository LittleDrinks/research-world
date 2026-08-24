// THROWAWAY PROTOTYPE shared seed: deterministic in-memory mock world built from the real 125 questions.
// No fetch, no persistence, no backend. Every demo reads the same RW world so scale claims are comparable.
(function () {
  const R = (window.RW = window.RW || {});
  R.TOPIC_ZH = {
    "Mathematical Sciences": "数学",
    "Chemistry": "化学",
    "Medicine & Health": "医学与健康",
    "Biology": "生物学",
    "Astronomy": "天文学",
    "Physics": "物理学",
    "Engineering & Materials Science": "工程与材料",
    "Information Science": "信息科学",
    "Neuroscience": "神经科学",
    "Ecology": "生态学",
    "Energy Science": "能源科学",
    "Artificial Intelligence": "人工智能",
  };

  function mulberry32(seed) {
    return function () {
      seed |= 0; seed = (seed + 0x6D2B79F5) | 0;
      let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  const t0 = performance.now();
  const rnd = mulberry32(20260905);
  const pad = (n, w) => String(n).padStart(w, "0");
  const pick = (list) => list[Math.floor(rnd() * list.length)];

  const DEEP = {
    21: { tag: "SciFact 链", human: true },
    49: { tag: "JPL 星历 · 人工返回", human: true },
    89: { tag: "Matbench 链", human: false },
    98: { tag: "Sleep-EDF + 手表", human: true },
    112: { tag: "湿实验 · 首批制片", human: true },
  };

  // One record per real Science-125 question, matching research-world/projects/qNNN/project.json naming.
  R.PROJECTS = (R.QUESTIONS || []).map((q) => {
    const roll = rnd();
    const status = roll < 0.28 ? "running" : roll < 0.44 ? "attention" : roll < 0.54 ? "human" : roll < 0.82 ? "healthy" : "paused";
    const deep = DEEP[q.id] || null;
    const nodes = 6 + Math.floor(rnd() * 58);
    return {
      id: "q" + pad(q.id, 3),
      n: q.id,
      topic: q.topic,
      topicZh: R.TOPIC_ZH[q.topic] || q.topic,
      title: q.title,
      status: deep ? "human" : status,
      tag: deep ? deep.tag : null,
      auto: deep ? false : rnd() < 0.72,
      nodes,
      directions: 1 + Math.floor(nodes * 0.42),
      experiments: Math.floor(nodes * 0.30),
      ghosts: Math.floor(nodes * 0.14),
      workflows: 0,
      active_workflows: 0,
      minutes_ago: Math.floor(rnd() * 1440),
      cycles: Math.floor(rnd() * 40),
      budget_yuan: +(0.5 + rnd() * 14).toFixed(2),
      lineage_fuses: Math.floor(rnd() * 3),
    };
  });
  R.PROJECTS.forEach((p) => {
    p.workflows = p.cycles * 3 + Math.floor(rnd() * 9);
    p.active_workflows = p.status === "running" ? 1 + Math.floor(rnd() * 3) : p.status === "human" ? 1 : 0;
  });

  R.TOTAL = R.PROJECTS.reduce((acc, p) => {
    acc.nodes += p.nodes; acc.workflows += p.workflows; acc.active += p.active_workflows;
    acc.ghosts += p.ghosts; acc.human += (p.status === "human" ? 1 : 0); acc.running += (p.status === "running" ? 1 : 0);
    return acc;
  }, { projects: R.PROJECTS.length, nodes: 0, workflows: 0, active: 0, ghosts: 0, human: 0, running: 0, attention: 0 });

  R.PROJECT_BY_ID = Object.fromEntries(R.PROJECTS.map((p) => [p.id, p]));
  R.deep = (id) => R.PROJECTS.find((p) => p.n === id);

  const ACTORS = ["orchestrator", "reviewer#1", "reviewer#2", "worker", "human"];
  const TYPES = ["run", "approve", "reject", "fuse", "human", "branch"];
  R.EVENTS = Array.from({ length: 960 }, (_, i) => {
    const p = R.PROJECTS[Math.floor(rnd() * R.PROJECTS.length)];
    const type = pick(TYPES);
    const mins = i * 1.5;
    const text = {
      run: `E-${pad(1 + Math.floor(rnd() * 240), 3)} 执行完成，退出码 0，产物已寻址`,
      approve: `reviewer 一致通过 D-${pad(1 + Math.floor(rnd() * 240), 3)} 的原子断言`,
      reject: `D-${pad(1 + Math.floor(rnd() * 240), 3)} 被驳回，进入幽灵车道`,
      fuse: `${p.id} 谱系连续 2 次驳回，auto 熔断并升级人工`,
      human: `人工裁决 ${p.id} 的双审分歧`,
      branch: `从 D-${pad(1 + Math.floor(rnd() * 240), 3)} 派生新方向候选`,
    }[type];
    return { seq: 960 - i, at: mins, project: p.id, actor: pick(ACTORS), type, text };
  });
  R.genMs = Math.round((performance.now() - t0) * 100) / 100;

  // Synthetic graph factory for density / stress demos. Deterministic, same shape every reload.
  R.graph = function (n, width, height) {
    const g = { nodes: [], edges: [] };
    for (let i = 0; i < n; i++) {
      const depth = i === 0 ? 0 : 1 + Math.floor(i / 5);
      const kind = i === 0 ? "question" : depth % 3 === 0 ? "experiment" : "direction";
      const status = rnd() < 0.12 ? "running" : rnd() < 0.2 ? "pending" : "admitted";
      g.nodes.push({
        id: "N" + pad(i, 4), kind, status, depth,
        x: (0.06 + rnd() * 0.88) * width, y: (0.06 + rnd() * 0.88) * height,
        title: i === 0 ? "核心研究问题" : `${kind === "experiment" ? "实验" : "方向"} N${pad(i, 4)}`,
      });
    }
    for (let i = 1; i < n; i++) {
      const parent = Math.max(0, i - 1 - Math.floor(rnd() * 3));
      g.edges.push({ source: g.nodes[parent].id, target: g.nodes[i].id, polarity: rnd() < 0.82 ? "supports" : "refutes" });
    }
    for (let i = 0; i < Math.floor(n / 3); i++) {
      const a = Math.floor(rnd() * n), b = Math.floor(rnd() * n);
      if (a !== b) g.edges.push({ source: g.nodes[a].id, target: g.nodes[b].id, polarity: "evidence" });
    }
    return g;
  };

  R.fmt = (n) => new Intl.NumberFormat("zh-CN").format(n);
  R.minutesAgo = (m) => m < 60 ? `${m} 分钟前` : m < 1440 ? `${Math.round(m / 60)} 小时前` : `${Math.round(m / 1440)} 天前`;
  R.summary = () => ({
    项目: R.TOTAL.projects + " 题", 节点: R.fmt(R.TOTAL.nodes), 工作流: R.fmt(R.TOTAL.workflows),
    运行中: R.TOTAL.active, 幽灵: R.fmt(R.TOTAL.ghosts), 待人工: R.TOTAL.human,
    数据来源: "docs/questions.json 转换 + 确定性伪随机 mock", 生成耗时: R.genMs + " ms", 持久化: "无（内存态）",
  });
})();
