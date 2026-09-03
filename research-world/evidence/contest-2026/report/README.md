---
artifact: contest-submission-report
issue: "https://github.com/LittleDrinks/research-world/issues/295"
template_sha256: 430ef9a8ec504a3b693e00653a8c3b55a34e00c888ebd616cc06cea7f75c2884
docx_sha256: 9bec99a23f38e2441bf77275fb3424e1163d57fd54b27aad2fe6ebf6742f1991
pdf_sha256: acee2cb9d3067b1eaab8b099bda6fbb7888fb5355265b029583021fff7836e17
pages: 20
figures: 5
---
# 技术方案报告（P1–P20 填充）
按官方模板填充的提交版报告。P13–P19 数字与 `../submission-evidence.md` 完全一致；团队信息、报名表截图、部署 URL、演示视频与百炼凭证截图为【待用户补充】占位，不编造。
## 产物
- `技术方案报告-ResearchWorld-filled.docx`：填充后报告（正文 20 页，含 5 图 26 表）。
- `技术方案报告-ResearchWorld-filled.pdf`：由 docx 经 LibreOffice headless 导出（`lscr.io/linuxserver/libreoffice` 容器，LibreOffice 25.8）。
- `figures/`：图1–图5 源 PNG 与渲染脚本 `render_figures.py`。
## 复现
```bash
# 1. 渲染插图（需 matplotlib + Noto Sans CJK SC）
python figures/render_figures.py
# 2. 填充模板（需 python-docx，仓库根 research-world/ 的上一级含 docs/ 模板）
python fill_report.py
# 3. docx → PDF
docker run --rm -v "$PWD:/work" -v /tmp/lo-out:/out lscr.io/linuxserver/libreoffice:latest \
  bash -c "s6-setuidgid abc libreoffice --headless -env:UserInstallation=file:///tmp/lo \
  --convert-to pdf --outdir /out '/work/技术方案报告-ResearchWorld-filled.docx'"
```
## 图清单
| 图 | 槽位 | 内容 |
|---|---|---|
| 图1 | P2 总体思路 | 科学问题→缺口→证据→三方向→评审→修订→研究计划闭环 |
| 图2 | P6 系统架构 | 已实现（web/control/worker/runtime/runner-controller）＋规划中（ADR-0037 Research Graph/动态 Workflow/Graph CLI/报告发布） |
| 图3 | P7 上下文结构 | 作者 Session 分层拼接上下文＋评审 Session 隔离上下文，findings 回流 |
| 图4 | P12 运行流程 | q049 实链 v1→review→v2→review→v3→对照→回执→review-v8 |
| 图5 | P19 结果可视化 | (a) 125 终态分布；(b) 深度案例 V1→final rubric；(c) 全量成本（对数轴） |
## 提交前待用户补充
1. 报名表第一、二页盖章版截图贴入 P1 占位框（含个人信息，不入 git）。
2. 挑战杯系统报名名称回填 P1 表首行。
3. 阿里云百炼调用凭证截图（不泄露密钥）回填 P20。
4. 公网可交互部署地址回填 P20 `[DEPLOY-URL]`。
5. ≤10 分钟演示视频上传夸克网盘，链接回填 P1/P20。
