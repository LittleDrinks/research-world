// THROWAWAY PROTOTYPE: V04 活手稿 — 研究即一部仍在撰述中的手稿。
import { useState } from "react";
import { BookOpen, ChevronLeft, ChevronRight, Feather, FlaskConical, PenLine, ScrollText, Send, Stamp, X } from "lucide-react";
import { kimiTasks, kimiProjects, kimiActivity, kimiChat, kimiMetrics } from "../seed";
import "./style.css";

const CHN = ["一", "二", "三", "四"];
const question = kimiTasks.find((t) => t.type === "question");
const directions = kimiTasks.filter((t) => t.type === "direction");
const groups = [...new Set(directions.map((t) => t.group))];

function ink(t) {
  if (t.scienceState === "待审查") return "#b3342a";
  if (t.scienceState === "待验证") return "#9a6b1f";
  if (t.scienceState === "已支持" || t.scienceState === "已采纳") return "#2f6b3a";
  return "#2b2620";
}

export default function LivingManuscript() {
  const [page, setPage] = useState("cover");
  const [chapter, setChapter] = useState(0);
  const [project, setProject] = useState(kimiProjects[0].id);
  const [sel, setSel] = useState(null);
  const [sheet, setSheet] = useState(false);
  const [marks, setMarks] = useState({});
  const [notes, setNotes] = useState({});
  const [extra, setExtra] = useState([]);
  const [draft, setDraft] = useState("");

  const effTasks = kimiTasks.map((t) => (marks[t.id] ? { ...t, scienceState: marks[t.id] } : t));
  const byId = (id) => effTasks.find((t) => t.id === id);
  const kids = (id) => effTasks.filter((t) => t.parent === id);
  const count = (fn) => effTasks.filter(fn).length;
  const nWait = count((t) => t.scienceState === "待审查");
  const nRun = count((t) => t.executionState === "运行");
  const nSup = count((t) => t.scienceState === "已支持");
  const nLock = count((t) => t.authoringState === "已锁定");
  const selTask = sel ? byId(sel) : null;

  const peek = (id) => { setSel(id); setSheet(true); };
  const judge = (id, state, note) => {
    setMarks({ ...marks, [id]: state });
    setNotes({ ...notes, [id]: note });
  };
  const send = () => {
    if (!draft.trim()) return;
    setExtra([...extra, { role: "user", text: draft.trim() }]);
    setDraft("");
  };

  const statusEm = (t) => <em className={"v04-st" + (t.scienceState === "待审查" ? " red" : "")}>{t.scienceState}</em>;

  const marginOf = (t) => (
    <aside className="v04-margin">
      {t.scienceState === "待审查"
        ? <span className="v04-redpen">✎ 待审查，亟须朱批</span>
        : <span className="v04-mnote dark">{t.scienceState}</span>}
      {notes[t.id] && <span className="v04-redpen">✎ 朱批：{notes[t.id]}</span>}
      <span className="v04-mnote">{t.agent} 执笔</span>
      <span className="v04-mnote">{t.model} · {t.channel}</span>
      <span className="v04-mnote">执行{t.executionState} · 撰述{t.authoringState}</span>
      {kids(t.id).filter((k) => k.type === "review").map((r) => (
        <span key={r.id} className={"v04-mnote" + (r.scienceState === "待审查" ? " red" : "")}>审查 {r.id}：{r.scienceState}</span>
      ))}
    </aside>
  );

  const cardOf = (k) => (
    <div key={k.id} className={"v04-card" + (k.type === "review" ? " rev" : "") + (k.scienceState === "待审查" ? " pending" : "")} onClick={() => peek(k.id)}>
      <div className="v04-card-h">
        {k.type === "review" ? <Stamp size={12} /> : <FlaskConical size={12} />}
        <b>{k.id}　{k.title}</b>
        <em>{k.kind} · {k.scienceState} · {k.executionState}</em>
      </div>
      <p>{k.prompt}</p>
      <div className="v04-card-m">{k.agent} · {k.model} · {k.channel} · {k.authoringState}</div>
    </div>
  );

  const fnOf = (t) => (
    <ol className="v04-fnotes">
      {t.acceptance.map((a, i) => <li key={i}>[{i + 1}] {a}</li>)}
    </ol>
  );

  const refSup = (t) => t.acceptance.map((_, i) => <sup key={i} className="v04-fnref">[{i + 1}]</sup>);

  const ROW = 34, TOP = 46;
  const dY = (i) => TOP + i * ROW;
  const qY = TOP + ((directions.length - 1) * ROW) / 2;

  const plateDot = (t, x, y, r) => (
    <>
      <circle cx={x} cy={y} r={r} fill={ink(t)} stroke={ink(t)} strokeWidth="1"
        strokeDasharray={t.executionState === "排队" ? "3 2" : undefined} />
      {t.authoringState === "已锁定" && <circle cx={x} cy={y} r={r + 3} fill="none" stroke={ink(t)} strokeWidth="0.8" />}
      {t.executionState === "失败" && <text x={x - r - 7} y={y - 5} className="v04-fail">×</text>}
    </>
  );

  return (
    <section className="v04-root">
      {page !== "cover" && (
        <header className="v04-head">
          <span className="v04-head-l"><Feather size={12} /> 活手稿 · 卷一　—　{kimiProjects.find((p) => p.id === project).name}</span>
          <span className="v04-head-r">{selTask ? <>批阅中：<b>{selTask.id} {selTask.title}</b> · {selTask.scienceState}</> : "尚未点节批阅"}</span>
        </header>
      )}

      {page === "cover" ? (
        <div className="v04-cover">
          <p className="v04-kicker">RESEARCH WORLD 手稿丛刊 · 第肆号</p>
          <h1 className="v04-cover-title">活　手　稿</h1>
          <p className="v04-cover-sub">研究即撰述：章以类聚，节以方向，实验为卡，朱批在侧，修订有录。择一稿本，展卷入读。</p>
          <div className="v04-shelf">
            {kimiProjects.map((p) => (
              <button key={p.id} className={"v04-book" + (p.lead ? " lead" : "")} onClick={() => { setProject(p.id); setPage("read"); }}>
                <span className="v04-book-tag">{p.lead ? "当前稿本" : "别　册"}</span>
                <b>{p.name}</b>
                <i>{p.question}</i>
                <span className="v04-book-meta">{p.nodes} 节 · 运行 {p.running} · 待审 {p.pending} · 更于{p.updated}</span>
                <span className="v04-book-cta">展卷 ⟶</span>
              </button>
            ))}
          </div>
          <p className="v04-cover-foot">凡 {kimiMetrics.total} 节 · 运行者 {nRun} · 待朱批 {nWait} · 已支持 {nSup} · 已锁定 {nLock}</p>
        </div>
      ) : (
        <div className="v04-body">
          <aside className="v04-toc">
            <button className="v04-toc-book" onClick={() => setPage("cover")}><BookOpen size={13} /> 活手稿 · 封皮</button>
            <nav className="v04-toc-nav">
              <button className={"v04-toc-ch" + (page === "read" && chapter === 0 ? " on" : "")} onClick={() => { setPage("read"); setChapter(0); }}>绪　论 · 研究问题</button>
              {groups.map((g, gi) => (
                <div key={g} className="v04-toc-grp">
                  <button className={"v04-toc-ch" + (page === "read" && chapter === gi + 1 ? " on" : "")} onClick={() => { setPage("read"); setChapter(gi + 1); }}>第{CHN[gi]}章　{g}</button>
                  {directions.filter((d) => d.group === g).map((d) => (
                    <button key={d.id} className={"v04-toc-sec" + (sel === d.id ? " on" : "")}
                      onClick={() => { setPage("read"); setChapter(gi + 1); setSel(d.id); }}>
                      <i style={{ background: ink(byId(d.id)) }} />{d.id}　{d.title}
                    </button>
                  ))}
                </div>
              ))}
              <button className={"v04-toc-ch" + (page === "plate" ? " on" : "")} onClick={() => setPage("plate")}><ScrollText size={12} /> 图版 Ⅰ · 图谱摹本</button>
              <button className={"v04-toc-ch" + (page === "revs" ? " on" : "")} onClick={() => setPage("revs")}><PenLine size={12} /> 附录 A · 修订记录</button>
            </nav>
            <div className="v04-toc-stats">
              <b>全稿统计</b>
              <span>凡 {effTasks.length} 节</span>
              <span className="red">待审查 {nWait}</span>
              <span>运行 {nRun} · 已支持 {nSup}</span>
              <span>已锁定 {nLock}</span>
            </div>
          </aside>

          <main className="v04-main">
            {page === "read" && chapter === 0 && (
              <article className="v04-article">
                <p className="v04-eyebrow">绪　论</p>
                <h2 className="v04-ch-title" onClick={() => peek(question.id)}>{question.id}　{question.title}</h2>
                <div className="v04-sec">
                  <div className="v04-sec-main">
                    <p className="v04-prose v04-cols">
                      本稿所问：{question.prompt}凡二十节方向，分隶四章——{groups.join("、")}；实验五则、审查四则，各附于所属方向之侧。旨归：{question.goal}
                      撰述之法：每节先叙其旨，次列实验与审查之卡，执笔、模型、通道署于页边；其待审查者以朱笔识之，俟批而后定。今通稿凡 {effTasks.length} 节，运行者 {nRun}，待朱批者 {nWait}，已支持者 {nSup}。
                    </p>
                    <div className="v04-fanli">
                      <b>凡　例</b>
                      <span><i className="v04-dot" style={{ background: "#b3342a" }} /> 朱＝待审查（{nWait}）</span>
                      <span><i className="v04-dot" style={{ background: "#9a6b1f" }} /> 赭＝待验证</span>
                      <span><i className="v04-dot" style={{ background: "#2f6b3a" }} /> 绿＝已支持（{nSup}）</span>
                      <span><i className="v04-dot" style={{ background: "#2b2620" }} /> 墨＝其余</span>
                    </div>
                    {fnOf(question)}
                  </div>
                  {marginOf(question)}
                </div>
                <div className="v04-turn">
                  <span />
                  <span>绪论 · 毕</span>
                  <button onClick={() => setChapter(1)}>第一章 <ChevronRight size={13} /></button>
                </div>
              </article>
            )}

            {page === "read" && chapter > 0 && (
              <article className="v04-article">
                <p className="v04-eyebrow">第{CHN[chapter - 1]}章</p>
                <h2 className="v04-ch-title">{groups[chapter - 1]}　<span className="v04-ch-sub">凡 {directions.filter((d) => d.group === groups[chapter - 1]).length} 节</span></h2>
                {directions.filter((d) => d.group === groups[chapter - 1]).map((d, di) => (
                  <section key={d.id} className="v04-sec">
                    <div className="v04-sec-main">
                      <h3 className={"v04-sec-title" + (sel === d.id ? " on" : "")} onClick={() => peek(d.id)}>
                        <span className="v04-sec-no">§ {chapter}.{di + 1}</span>　{d.id}　{d.title}　{statusEm(d)}
                      </h3>
                      <p className="v04-prose">
                        本节所究：{d.prompt}是节由 {d.agent} 执笔，假 {d.channel} 通道而行，执行{d.executionState}，撰述{d.authoringState}；旨归{d.goal}{refSup(d)}
                      </p>
                      {kids(d.id).map(cardOf)}
                      {fnOf(d)}
                    </div>
                    {marginOf(d)}
                  </section>
                ))}
                <div className="v04-turn">
                  <button disabled={chapter <= 1} onClick={() => setChapter(chapter - 1)}><ChevronLeft size={13} /> 上一章</button>
                  <span>第{CHN[chapter - 1]}章 · 毕</span>
                  <button disabled={chapter >= groups.length} onClick={() => setChapter(chapter + 1)}>下一章 <ChevronRight size={13} /></button>
                </div>
              </article>
            )}

            {page === "plate" && (
              <article className="v04-article wide">
                <p className="v04-eyebrow">图版 Ⅰ</p>
                <h2 className="v04-ch-title">研究图谱摹本　<span className="v04-ch-sub">问题居左，方向中列，实验与审查附于所属之右</span></h2>
                <svg viewBox="0 0 980 740" className="v04-plate">
                  {directions.map((d, i) => (
                    <path key={"q" + d.id} className="v04-link" d={`M 100 ${qY} C 190 ${qY}, 210 ${dY(i)}, 293 ${dY(i)}`} />
                  ))}
                  {directions.map((d, i) => kids(d.id).map((k) => {
                    const sibs = kids(d.id).length;
                    const kx = k.type === "experiment" ? 600 : 750;
                    const ky = dY(i) + (sibs > 1 ? (k.type === "experiment" ? -8 : 8) : 0);
                    return <path key={k.id} className="v04-link thin" d={`M 307 ${dY(i)} C 420 ${dY(i)}, ${kx - 80} ${ky}, ${kx - 7} ${ky}`} />;
                  }))}
                  <g className="v04-pnode" onClick={() => peek(question.id)}>
                    {plateDot(byId(question.id), 90, qY, 7)}
                    <text x="90" y={qY - 16} textAnchor="middle" className="v04-pid">{question.id}</text>
                    <text x="90" y={qY + 24} textAnchor="middle" className="v04-pt">{question.title}</text>
                  </g>
                  {directions.map((d, i) => (
                    <g key={d.id} className={"v04-pnode" + (sel === d.id ? " on" : "")} onClick={() => peek(d.id)}>
                      {plateDot(byId(d.id), 300, dY(i), 4.5)}
                      <text x="314" y={dY(i) + 3.5} className="v04-pl">{d.id}　{d.title}</text>
                    </g>
                  ))}
                  {directions.map((d, i) => kids(d.id).map((k) => {
                    const sibs = kids(d.id).length;
                    const kx = k.type === "experiment" ? 600 : 750;
                    const ky = dY(i) + (sibs > 1 ? (k.type === "experiment" ? -8 : 8) : 0);
                    return (
                      <g key={"n" + k.id} className={"v04-pnode" + (sel === k.id ? " on" : "")} onClick={() => peek(k.id)}>
                        {plateDot(k, kx, ky, 4)}
                        <text x={kx + 12} y={ky + 3.5} className="v04-pl">{k.id}　{k.title}</text>
                      </g>
                    );
                  }))}
                </svg>
                <p className="v04-legend">朱●待审查　赭●待验证　绿●已支持　墨●其余　｜　虚圈＝排队　×＝失败　双圈＝已锁定　｜　点击节点以披览插页</p>
              </article>
            )}

            {page === "revs" && (
              <article className="v04-article">
                <p className="v04-eyebrow">附录 A</p>
                <h2 className="v04-ch-title">修订记录　<span className="v04-ch-sub">凡 {kimiActivity.length} 则，以时为序</span></h2>
                <div className="v04-revs">
                  {kimiActivity.map((a) => (
                    <div key={a.id} className="v04-rev">
                      <span className="v04-rev-t">{a.time}</span>
                      <span className="v04-rev-body">
                        <b>{a.actor}</b>　{a.action}　
                        <button className="v04-ref" onClick={() => peek(a.target.split(" ")[0])}>{a.target}</button>
                        　—— {a.detail}
                      </span>
                      <em className={"v04-rev-s" + (a.state === "失败" ? " red" : "")}>{a.state}</em>
                    </div>
                  ))}
                </div>
              </article>
            )}
          </main>
        </div>
      )}

      {sheet && selTask && (
        <div className="v04-overlay" onClick={() => setSheet(false)}>
          <div className="v04-sheet" onClick={(e) => e.stopPropagation()}>
            <button className="v04-x" onClick={() => setSheet(false)}><X size={14} /></button>
            <p className="v04-eyebrow">插　页 · {selTask.kind}</p>
            <h3 className="v04-sheet-title">{selTask.id}　{selTask.title}</h3>
            <div className="v04-chips">
              <span className={selTask.scienceState === "待审查" ? "red" : ""}>{selTask.scienceState}</span>
              <span>{selTask.authoringState}</span>
              <span>{selTask.executionState}</span>
            </div>
            <p className="v04-prose">{selTask.prompt}　旨归：{selTask.goal}</p>
            <dl className="v04-fields">
              <div><dt>执笔</dt><dd>{selTask.agent}</dd></div>
              <div><dt>模型</dt><dd>{selTask.model}</dd></div>
              <div><dt>提供方</dt><dd>{selTask.provider}</dd></div>
              <div><dt>通道</dt><dd>{selTask.channel}</dd></div>
              <div><dt>工作区</dt><dd>{selTask.workspace}</dd></div>
              <div><dt>权限</dt><dd>{selTask.permission}</dd></div>
              <div><dt>器用</dt><dd>{selTask.tools.join("、")}</dd></div>
            </dl>
            {fnOf(selTask)}
            {selTask.scienceState === "待审查" && (
              <div className="v04-judge">
                <button onClick={() => judge(selTask.id, "待验证", "准所请，入图待验。")}>准 · 入图待验</button>
                <button className="no" onClick={() => judge(selTask.id, "待审查", "驳回，退回重修。")}>驳 · 退回重修</button>
              </div>
            )}
            {notes[selTask.id] && <p className="v04-redpen v04-jnote">✎ 朱批：{notes[selTask.id]}</p>}
            <h4 className="v04-corr-title"><PenLine size={12} /> 往来批注</h4>
            <div className="v04-corr">
              {[...kimiChat, ...extra].map((m, i) => (
                <div key={i} className={"v04-msg " + m.role}>
                  <b>{m.role === "user" ? "研究者" : "Orchestrator"}</b>
                  <p>{m.text}</p>
                  {m.nodes && (
                    <div className="v04-refs">
                      {m.nodes.map((n) => <button key={n} className="v04-ref" onClick={() => peek(n)}>{n}</button>)}
                    </div>
                  )}
                </div>
              ))}
            </div>
            <div className="v04-compose">
              <input value={draft} onChange={(e) => setDraft(e.target.value)} onKeyDown={(e) => e.key === "Enter" && send()} placeholder="批注此节……" />
              <button onClick={send} aria-label="送出批注"><Send size={13} /></button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
