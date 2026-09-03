"""渲染技术方案报告全部插图（图1-图5）。输出 PNG，供 fill_report.py 嵌入 docx。

用法: python render_figures.py
依赖: matplotlib（Noto Sans CJK SC 字体）
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

matplotlib.rcParams["font.family"] = ["Noto Sans CJK SC"]
matplotlib.rcParams["axes.unicode_minus"] = False

BLUE = "#2f5b94"      # 已实现/主流程
LBLUE = "#dce7f5"     # 主流程底色
GRAY = "#6b7280"
LGRAY = "#f0f1f3"
GREEN = "#3a7d44"
LGREEN = "#e2f0e5"
RED = "#c0392b"
ORANGE = "#d9822b"
LORANGE = "#fbeedd"

OUT = Path(__file__).parent


def box(ax, x, y, w, h, text, fc=LBLUE, ec=BLUE, ls="-", fs=10.5, tc="#1a1a1a", lw=1.4, bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.6",
                                fc=fc, ec=ec, ls=ls, lw=lw))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
            color=tc, fontweight="bold" if bold else "normal", linespacing=1.45)


def arrow(ax, x1, y1, x2, y2, text="", color=BLUE, ls="-", fs=9, rad=0.0, toff=(0, 1.8), lw=1.6):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=16,
                                 color=color, ls=ls, lw=lw,
                                 connectionstyle=f"arc3,rad={rad}"))
    if text:
        ax.text((x1 + x2) / 2 + toff[0], (y1 + y2) / 2 + toff[1], text, ha="center",
                va="center", fontsize=fs, color=color)


def canvas(w=12.5, h=6.2):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    return fig, ax


def save(fig, name):
    fig.savefig(OUT / name, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"saved {name}")


# ---------------------------------------------------------------- 图1 总体思路
def fig1():
    fig, ax = canvas(12.5, 6.0)
    bw, bh, y1, y2 = 21.0, 17, 66, 22
    xs = [2.5, 27.2, 51.9, 76.6]
    row1 = ["官方 125 道科学问题\n（canonical 原题）",
            "问题理解与题干\n前提校正",
            "知识缺口识别\n（已有认识 / 争议 / 未知）",
            "证据获取与核验\n（DOI/arXiv 可回读）"]
    # 第二行自右向左流动
    row2 = ["研究计划与限定计算\n（planned / executed 分离）",
            "修订与筛选\n（findings 逐条回流）",
            "独立评审\n六维 rubric + 来源门",
            "候选假设生成\n三个可区分方向 D1–D3"]
    for x, t in zip(xs, row1):
        box(ax, x, y1, bw, bh, t, fs=10.5)
    for x, t in zip(xs, row2):
        box(ax, x, y2, bw, bh, t, fs=10.5, fc=LORANGE, ec=ORANGE)
    for i in range(3):
        arrow(ax, xs[i] + bw, y1 + bh / 2, xs[i + 1], y1 + bh / 2)
        arrow(ax, xs[i + 1], y2 + bh / 2, xs[i], y2 + bh / 2)
    # row1 末 -> row2 末（右缘转折下行）
    arrow(ax, xs[3] + bw / 2, y1, xs[3] + bw / 2, y2 + bh)
    # 反馈：独立评审 -> 候选假设（第二行相邻，弧线在下方）
    ax.add_patch(FancyArrowPatch((xs[2] + bw / 2, y2), (xs[3] + bw / 2, y2),
                                 arrowstyle="-|>", mutation_scale=16, color=RED, lw=1.8,
                                 connectionstyle="arc3,rad=-0.45"))
    ax.text((xs[2] + xs[3]) / 2 + bw / 2, y2 - 9.5, "verdict = revise\nfindings 触发修订",
            ha="center", fontsize=9, color=RED)
    # 输出（左下，箭头来自第二行最左框）
    box(ax, 2.5, 2, 60, 11,
        "输出：候选结论 + 研究计划 + 来源记录 + 运行账本（Session / 调用 / token / SHA-256）",
        fc=LGREEN, ec=GREEN, fs=10.5, bold=True)
    arrow(ax, xs[0] + bw / 2, y2, xs[0] + bw / 2, 13)
    fig.savefig(OUT / "fig1-overview.png", dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("saved fig1-overview.png")


# ---------------------------------------------------------------- 图2 系统架构
def fig2():
    fig, ax = canvas(12.5, 6.6)
    # 已实现外框
    ax.add_patch(FancyBboxPatch((1, 24), 63, 74, boxstyle="round,pad=0.6,rounding_size=2",
                                fc="none", ec=BLUE, lw=1.8))
    ax.text(3.5, 94, "已实现（本作品提交时点）", fontsize=11, color=BLUE, fontweight="bold")
    # 规划外框
    ax.add_patch(FancyBboxPatch((67, 24), 32, 74, boxstyle="round,pad=0.6,rounding_size=2",
                                fc="none", ec=GRAY, lw=1.8, ls=(0, (6, 4))))
    ax.text(69.5, 94, "规划中（ADR-0037 目标架构）", fontsize=11, color=GRAY, fontweight="bold")

    box(ax, 6, 78, 24, 11, "研究者 / 评审\n人工 Gate · waiting_human", fc=LGRAY, ec=GRAY, fs=10)
    box(ax, 36, 78, 24, 11, "Web 前端\nChat · 图谱 · Trace 视图", fs=10)
    box(ax, 6, 60, 24, 12, "control 控制面 :8095\nSQLite 图谱唯一真源\nPipeline · 双审准入", fs=9.5)
    box(ax, 36, 60, 24, 12, "worker\n后台任务 · 审计留痕", fc=LGRAY, ec=GRAY, fs=10)
    box(ax, 6, 42, 24, 12, "Agent Runtime :8098\nACP · Session / Trace\n凭证隔离（.env 不入库）", fs=9.5)
    box(ax, 36, 42, 24, 12, "Qwen 系列\n阿里云百炼 OpenAI 兼容端点\nqwen3-max 等", fc=LGREEN, ec=GREEN, fs=9.5)
    box(ax, 21, 27, 24, 10, "runner-controller :8096\n工具沙箱 · Lean 验证镜像", fs=9.5)
    ax.text(32.5, 21.5, "docker compose 编排（control / worker / runtime / runner-controller）",
            ha="center", fontsize=9, color=GRAY)

    # 人 <-> Web
    ax.add_patch(FancyArrowPatch((30, 83.5), (36, 83.5), arrowstyle="<|-|>",
                                 mutation_scale=14, color=BLUE, lw=1.6))
    ax.text(33, 86.2, "Gate", ha="center", fontsize=8.5, color=BLUE)
    # Web -> control
    arrow(ax, 44, 78, 24, 72, rad=0.12, text="请求 / 决策", fs=8.5, toff=(9, 2.5))
    # control -> worker
    arrow(ax, 30, 66, 36, 66, text="派发", fs=8.5, toff=(0, 2.2))
    # control -> runtime
    arrow(ax, 18, 60, 18, 54, text="launch / prompt", fs=8.5, toff=(-9, 0))
    # runtime -> Qwen
    arrow(ax, 30, 48, 36, 48, text="OpenAI 兼容调用", fs=8.5, toff=(0, 2.4))
    # control -> runner
    arrow(ax, 26, 60, 31, 37, rad=0.1, text="工具调用", fs=8.5, toff=(7.5, -3))

    # 规划层
    box(ax, 70, 78, 26, 11, "Research Graph\nDirection / Experiment / Claim\n仅采纳有证据闭包的 Claim",
        fc="white", ec=GRAY, ls=(0, (6, 4)), fs=9.5)
    box(ax, 70, 60, 26, 12, "主 Agent 动态 Workflow\nChild Agent 继续 / 复审 / 并行 / 转向",
        fc="white", ec=GRAY, ls=(0, (6, 4)), fs=9.5)
    box(ax, 70, 42, 26, 12, "Graph CLI\n主 Agent 与人可写图\nChild Agent 只读",
        fc="white", ec=GRAY, ls=(0, (6, 4)), fs=9.5)
    box(ax, 70, 27, 26, 10, "报告发布\n报告投影 · BibTeX · 交付校验",
        fc="white", ec=GRAY, ls=(0, (6, 4)), fs=9.5)
    # 演进箭头（已实现框 -> 规划框）
    ax.add_patch(FancyArrowPatch((64.5, 52), (66.4, 52), arrowstyle="-|>",
                                 mutation_scale=15, color=GRAY, ls=(0, (5, 3)), lw=1.8))
    ax.text(65.5, 55.5, "演进", fontsize=9, color=GRAY, ha="center")
    fig.savefig(OUT / "fig2-architecture.png", dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("saved fig2-architecture.png")


# ---------------------------------------------------------------- 图3 Qwen 上下文结构
def fig3():
    fig, ax = canvas(12.5, 6.4)
    # 作者上下文堆栈
    blocks = [
        ("系统协议（每轮固定）\n角色约束 · 输出契约（固定章节）\n证据门槛 · 文件边界 · 检索预算", BLUE, LBLUE),
        ("任务输入\ncanonical 科学问题原文 + 题干语境", BLUE, LBLUE),
        ("证据上下文\n检索结果 · 来源记录（作者/年份/标题/DOI）\n支持证据与反对证据", ORANGE, LORANGE),
        ("历史与反馈上下文\n历史版本 · 评审 findings · 被拒原因", ORANGE, LORANGE),
        ("边界约束\nplanned / executed 分离 · 停止与回退条件", GRAY, LGRAY),
    ]
    y = 88
    hs = [17, 11, 17, 13, 11]
    for (t, ec, fc), h in zip(blocks, hs):
        y -= h + 3
        box(ax, 3, y, 44, h, t, ec=ec, fc=fc, fs=9.5)
    ax.text(25, 93, "作者 Session 上下文（逐层拼接）", fontsize=11, fontweight="bold", color="#1a1a1a")
    box(ax, 55, 42, 20, 22, "Qwen\n作者 Session\nqwen3-max\n（独立运行）", fc=LGREEN, ec=GREEN, fs=10.5, bold=True)
    # 输出
    box(ax, 80, 40, 18, 26, "输出\nMarkdown 报告\n固定章节 +\nD1–D3 + 来源 +\nplanned 标注\n↓\nrun.md 账本\nSession/token/哈希",
        fc="white", ec=GREEN, fs=8.5)
    arrow(ax, 47, 53, 55, 53, text="", fs=9)
    arrow(ax, 75, 53, 80, 53)
    # 评审上下文
    box(ax, 55, 8, 43, 24,
        "独立评审 Session 上下文（隔离）\n固定六维 rubric（各 0–2，满分 12）+ 来源门\n被审版本与被审来源清单\n不含作者 Trajectory；引用由评审独立检索核验",
        fc="white", ec=BLUE, fs=9.5)
    arrow(ax, 90, 40, 78, 32, text="送审", fs=9, toff=(6, 0))
    arrow(ax, 60, 32, 30, 44, text="verdict + findings 回流", color=RED, fs=9, toff=(-16, -1), rad=0.15)
    fig.savefig(OUT / "fig3-context.png", dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("saved fig3-context.png")


# ---------------------------------------------------------------- 图4 完整运行流程（q049）
def fig4():
    fig, ax = canvas(13.0, 6.6)
    y_main = 62
    bh = 16
    box(ax, 1.5, y_main, 15.5, bh, "作者 Session\nv1\n9/12 · 来源 2/5", fs=9.5)
    box(ax, 21.5, y_main, 17.5, bh, "独立评审 review-v1\nrevise · 5 findings\n错配 DOI / 错 arXiv 号\n反向转述 / 数量级错\n无效判据", fs=8.5, fc=LORANGE, ec=ORANGE)
    box(ax, 43.5, y_main, 14.5, bh, "作者 v2\n8/12 · 来源 5/5", fs=9.5)
    box(ax, 62.5, y_main, 17.5, bh, "独立评审 review-v2\nrevise · 机制捆绑\n时间尺度 / 判据错误", fs=8.5, fc=LORANGE, ec=ORANGE)
    box(ax, 84.5, y_main, 14, bh, "作者 v3\n12/12 · 来源 5/5\n执行 Peters 计算", fs=9)
    arrow(ax, 17, y_main + bh / 2, 21.5, y_main + bh / 2)
    arrow(ax, 39, y_main + bh / 2, 43.5, y_main + bh / 2, color=RED)
    ax.text(41.2, y_main + bh / 2 + 8.2, "修订", ha="center", fontsize=9, color=RED)
    arrow(ax, 58, y_main + bh / 2, 62.5, y_main + bh / 2)
    arrow(ax, 80, y_main + bh / 2, 84.5, y_main + bh / 2, color=RED)
    ax.text(82.2, y_main + bh / 2 + 8.2, "修订", ha="center", fontsize=9, color=RED)

    # 下排：对照与收束
    y2 = 20
    box(ax, 6, y2, 19, 14, "直接回答对照\nattempt 1–7（同题同模型\n同检索权限）\n4/12 · 6/12 · 0 来源", fs=8.5, fc=LGRAY, ec=GRAY)
    box(ax, 29, y2, 15.5, 14, "benchmark 评审\nattempt 2/6 vs V1\nvs baseline", fs=8.5, fc=LGRAY, ec=GRAY)
    box(ax, 48.5, y2, 14.5, 14, "显示投影\nbaseline-matched-v9", fs=8.5, fc=LGRAY, ec=GRAY)
    box(ax, 67, y2, 13.5, 14, "独立回执\nreceipt 复算\nSession/token/哈希", fs=8.5, fc=LGRAY, ec=GRAY)
    box(ax, 84.5, y2, 14, 14, "最终评审 review-v8\ndeliverable\n12/12 · 来源 6/6", fs=8.5, fc=LGREEN, ec=GREEN, bold=True)
    arrow(ax, 25, y2 + 7, 29, y2 + 7)
    arrow(ax, 44.5, y2 + 7, 48.5, y2 + 7)
    arrow(ax, 63, y2 + 7, 67, y2 + 7)
    arrow(ax, 80.5, y2 + 7, 84.5, y2 + 7)
    arrow(ax, 91.5, y_main, 91.5, y2 + 14, text="版本链延续 v4–v8", fs=8.5, toff=(0, 4))
    # planned 标注
    ax.text(50, 6, "反馈机制：每轮 review 的 findings 逐条进入下一轮作者上下文；失败 / 暂停 Session 以 failed / stopped 留痕，重试用全新 Session",
            ha="center", fontsize=9.5, color=GRAY,
            bbox=dict(boxstyle="round,pad=0.45", fc="#faf5ec", ec=ORANGE, lw=1.0))
    fig.savefig(OUT / "fig4-workflow.png", dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("saved fig4-workflow.png")


# ---------------------------------------------------------------- 图5 125 题结果可视化
def fig5():
    fig, axes = plt.subplots(1, 3, figsize=(13.0, 3.9))
    # (a) 终态分布
    ax = axes[0]
    cats = ["completed", "partial", "waiting_human", "failed"]
    vals = [8, 117, 0, 0]
    colors = [GREEN, ORANGE, GRAY, RED]
    bars = ax.bar(cats, vals, color=colors, width=0.62)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 2.5, str(v), ha="center", fontsize=11, fontweight="bold")
    ax.set_ylim(0, 132)
    ax.set_ylabel("题目数", fontsize=10)
    ax.set_title("(a) 125 题轻量运行终态分布\n（候选结论 125/125）", fontsize=10.5)
    ax.tick_params(axis="x", labelsize=9, rotation=12)
    ax.spines[["top", "right"]].set_visible(False)
    # (b) 深度案例 V1 vs final
    ax = axes[1]
    cases = ["q049", "q089", "q021", "q112", "q098"]
    v1 = [9, 10, 10, 7, 7]
    final = [12] * 5
    x = range(5)
    ax.bar([i - 0.19 for i in x], v1, width=0.36, color=ORANGE, label="V1（首轮）")
    ax.bar([i + 0.19 for i in x], final, width=0.36, color=GREEN, label="最终版")
    for i, v in zip(x, v1):
        ax.text(i - 0.19, v + 0.25, str(v), ha="center", fontsize=9)
    for i in x:
        ax.text(i + 0.19, 12.25, "12", ha="center", fontsize=9, fontweight="bold")
    ax.axhline(12, color=GRAY, lw=0.8, ls="--")
    ax.set_ylim(0, 14.6)
    ax.set_xticks(list(x), cases, fontsize=10)
    ax.set_ylabel("六维 rubric 得分（满分 12）", fontsize=10)
    ax.set_title("(b) 五个深度案例：独立评审 rubric\n（最终来源门 6/6·9/9·8/8·9/9·8/8 全过）", fontsize=10.5)
    ax.legend(fontsize=9, loc="lower right")
    ax.spines[["top", "right"]].set_visible(False)
    # (c) 全量成本（对数横轴；各行单位不同，以标注为准）
    ax = axes[2]
    items = ["模型调用\n（次）", "非缓存输入\n（百万 token）", "缓存读取\n（百万 token）", "输出\n（万 token）"]
    vals = [2592, 27.87, 99.87, 58.13]
    bars = ax.barh(items[::-1], vals[::-1], color=BLUE, height=0.55)
    for b, v in zip(bars, vals[::-1]):
        ax.text(b.get_width() * 1.25, b.get_y() + b.get_height() / 2, f"{v:g}",
                va="center", fontsize=9.5)
    ax.set_xscale("log")
    ax.set_xlim(8, 12000)
    ax.set_title("(c) 125 题全量运行成本\n（135 Session · 2592 次调用；对数轴）", fontsize=10.5)
    ax.tick_params(axis="y", labelsize=9)
    ax.tick_params(axis="x", labelsize=8)
    ax.spines[["top", "right"]].set_visible(False)
    fig.subplots_adjust(left=0.07, right=0.98, bottom=0.14, top=0.82, wspace=0.42)
    fig.savefig(OUT / "fig5-results.png", dpi=200, facecolor="white")
    plt.close(fig)
    print("saved fig5-results.png")


if __name__ == "__main__":
    fig1()
    fig2()
    fig3()
    fig4()
    fig5()
