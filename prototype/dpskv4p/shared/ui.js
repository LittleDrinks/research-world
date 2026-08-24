// THROWAWAY PROTOTYPE shared frame: bottom-centre variant switcher + collapsible state surface.
// Per .agents/skills/prototype/UI.md: arrows cycle variants, URL-less because each variant is a standalone file,
// keyboard arrows work everywhere except inside inputs, the bar is visually foreign to the page.
(function () {
  window.RWUI = window.RWUI || null;
  window.$ = window.$ || ((id) => document.getElementById(id));
  const R = (window.RW = window.RW || {});
  const MANIFEST = [
    ["v01", "fleet", "研究舰队总览", "完整系统", "125 题一个屏：健康度矩阵与人工分诊"],
    ["v02", "cartography", "证据制图台", "完整系统", "图谱即地图册：图例、缩略图与分层目录"],
    ["v03", "ledger", "审计台账", "完整系统", "append-only 事件账本：本周期五问"],
    ["v04", "docket", "双审庭审台", "完整系统", "双审分歧、抗辩与人工裁决队列"],
    ["v05", "lineage-rail", "谱系铁路", "完整系统", "谱系即线路：连续驳回熔断信号"],
    ["v06", "assembly", "能力装配甲板", "完整系统", "能力包插槽、装配凭据与渐进披露"],
    ["v07", "wet-lab", "湿实验操作台", "125 命题", "Q112 环保塑料：人工登记与证据上传"],
    ["v08", "orbit", "行星轨道星历桌", "125 命题", "Q49 轨道稳定性：JPL 星历人工返回"],
    ["v09", "matrix", "证据矩阵", "完整系统", "claim × source 交叉核对，诚信至上"],
    ["v10", "budget", "预算闸门", "完整系统", "125 题批量跑批的预算与熔断"],
    ["v11", "inbox", "人工裁决收件箱", "完整系统", "等待人类的事项，按风险与时限排队"],
    ["v12", "dissector", "节点解剖台", "局部组件", "节点 inspector：五层展开与依赖切片"],
    ["v13", "ghost-archive", "幽灵档案室", "局部组件", "驳回轨迹、相似性匹配与复用阻断"],
    ["v14", "impact", "影响半径计算器", "局部组件", "上游失效时下游污染的确定性定位"],
    ["v15", "time-window", "时间窗", "局部组件", "本周期新增/失败/待办/影响的单屏回答"],
    ["v16", "palette", "命令面板", "局部组件", "渐进披露：按语义展开能力与图谱内容"],
    ["v17", "repro-card", "复现凭据卡", "局部组件", "image/command/seed/limits/exit code/hash 一张卡"],
    ["v18", "density", "密度压力表", "局部组件", "5000 节点真实 DOM 渲染的性能证据"],
    ["v19", "alarm", "高光报错台", "局部组件", "失败升级为信号，不埋进日志"],
    ["v20", "citation", "引用检查清样", "局部组件", "引用存在性、最终发表版与 .bib 导出"],
    ["v21", "scifact", "SciFact 抗生素链", "125 命题", "Q21 耐药性：证据句绑定到原子主张"],
    ["v22", "matbench", "Matbench 能量链", "125 命题", "Q89 转换效率：材料-性能证据链"],
    ["v23", "sleep", "睡眠证据台", "125 命题", "Q98 睡眠：Sleep-EDF + 手表数据返回"],
    ["v24", "selection", "设计选型矩阵", "完整系统", "24 套方案按场景打分的决策工具"],
  ];
  R.MANIFEST = MANIFEST.map(([n, slug, title, kind, brief]) => ({ n, slug, title, kind, brief, href: `${n}-${slug}/index.html` }));
  R.index = () => ({ n: "index", slug: "index", title: "总览", kind: "索引", brief: "", href: "index.html" });

  function currentIndex() {
    const seg = location.pathname.split("/");
    const dir = seg[seg.length - 2] || "index";
    if (dir === "index") return -1;
    const found = MANIFEST.findIndex((m) => m[0] === dir.slice(0, 3));
    return found >= 0 ? found : -1;
  }

  function buildBar() {
    const idx = currentIndex();
    const cur = idx >= 0 ? R.MANIFEST[idx] : R.index();
    const prev = idx > 0 ? R.MANIFEST[idx - 1] : R.index();
    const next = idx >= 0 && idx < R.MANIFEST.length - 1 ? R.MANIFEST[idx + 1] : (idx === -1 ? R.MANIFEST[0] : null);
    const to = (item) => (location.pathname.endsWith("index.html") ? item.href : "../" + item.href);
    const nav = document.createElement("nav");
    nav.className = "dpsk-bar";
    nav.innerHTML = `
      <a class="dpsk-home" href="${to(R.index())}" title="回到 dpskv4p 总览">dpskv4p</a>
      ${prev ? `<a href="${to(prev)}" title="上一套：${prev.title}">←</a>` : `<span class="dpsk-off">←</span>`}
      <b>${cur.n} · ${cur.title}</b><small>${cur.kind}</small>
      ${next ? `<a href="${to(next)}" title="下一套：${next.title}">→</a>` : `<span class="dpsk-off">→</span>`}
      <details class="dpsk-state"><summary>Prototype state</summary><pre id="dpsk-state">${escapeHtml(JSON.stringify(R.summary ? R.summary() : {}, null, 2))}</pre></details>`;
    document.body.appendChild(nav);
    const state = nav.querySelector("#dpsk-state");
    window.RWUI = {
      nav,
      setState(extra) {
        const s = Object.assign({ variant: cur.n, title: cur.title, kind: cur.kind }, R.summary(), extra || {});
        state.textContent = JSON.stringify(s, null, 2);
      },
    };
  }

  function escapeHtml(s) { return String(s).replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c])); }

  document.addEventListener("DOMContentLoaded", buildBar);
  document.addEventListener("keydown", (e) => {
    const el = document.activeElement;
    if (el && (el.tagName === "INPUT" || el.tagName === "TEXTAREA" || el.isContentEditable)) return;
    if (e.key !== "ArrowLeft" && e.key !== "ArrowRight") return;
    const idx = currentIndex();
    if (idx < 0) return;
    const target = e.key === "ArrowLeft" ? R.MANIFEST[idx - 1] : R.MANIFEST[idx + 1];
    if (target) location.href = "../" + target.href;
  });
})();
