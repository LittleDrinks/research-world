#!/usr/bin/env bash
# 合成演示视频：<repo>/.scratch/demo-video.mp4（1920×1080，30fps，无声，约 6:20）。
# 前置：make_cards.mjs、make_bars.mjs 已产出卡片与字幕条；rec/ 下有 site.webm、product.webm。
# 用法：bash scripts/demo-video/compose.sh
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RW="$(cd "$HERE/../.." && pwd)"
REPO="$(cd "$RW/.." && pwd)"
V="$REPO/.scratch/video"
OUT="$REPO/.scratch/demo-video.mp4"
ENC="-c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -r 30"

mkdir -p "$V/seg"
# 1) 字幕卡 → 定长片段（时长=阅读时间，见 storyboard.md）
card() { ffmpeg -y -v error -loop 1 -framerate 30 -t "$2" -i "$V/cards/$1.png" \
  -vf "scale=1920:1080" $ENC "$V/seg/$1.mp4"; }
card 01-title 12;      card 02-oneliner 16;  card 03-dashboard 16
card 04-sec-method 6;  card 05-problem 18;   card 06-v1-directions 28
card 07-v1-score 18;   card 08-findings 38;  card 09-revision 22
card 10-peters 24;     card 11-rubric 22;    card 12-cost 30
card 13-deepcases 20;  card 14-sec-site 6;   card 17-compose 14
card 21-end 16

# 2) 站点录屏：0.62× 放慢 + 底部字幕条
ffmpeg -y -v error -i "$V/rec/site.webm" -i "$V/bars/bar-site.png" \
  -filter_complex "[0:v]fps=30,setpts=PTS/0.62[v];[v][1:v]overlay=0:920,format=yuv420p" \
  $ENC "$V/seg/15-site.mp4"

# 3) 产品录屏切三段：发问流式 / 刷新恢复 / 图谱，尾部冻结补阅读时间
prodcut() { ffmpeg -y -v error -ss "$2" -t "$3" -i "$V/rec/product.webm" -i "$V/bars/$5.png" \
  -filter_complex "[0:v]fps=30[v];[v][1:v]overlay=0:920,tpad=stop_mode=clone:stop_duration=$4,format=yuv420p" \
  $ENC "$V/seg/$1.mp4"; }
prodcut 18-prodA 0    23   2 bar-prodA
prodcut 19-prodB 23   8.5  2 bar-prodB
prodcut 20-prodC 31.5 8.2  3 bar-prodC

# 4) 顺序拼接（分镜顺序，见 storyboard.md）重编码统一参数
: > "$V/concat.txt"
for s in 01-title 02-oneliner 03-dashboard 04-sec-method 05-problem 06-v1-directions \
         07-v1-score 08-findings 09-revision 10-peters 11-rubric 12-cost 13-deepcases \
         14-sec-site 15-site 16-sec-product 17-compose 18-prodA 19-prodB 20-prodC 21-end; do
  # 16-sec-product 是产品章节卡（6s），与卡片同参数生成
  [ -f "$V/seg/$s.mp4" ] || ffmpeg -y -v error -loop 1 -framerate 30 -t 6 \
    -i "$V/cards/16-sec-product.png" -vf "scale=1920:1080" $ENC "$V/seg/16-sec-product.mp4"
  echo "file '$V/seg/$s.mp4'" >> "$V/concat.txt"
done
ffmpeg -y -v error -f concat -safe 0 -i "$V/concat.txt" $ENC "$OUT"
ffprobe -v error -show_entries format=duration,size -of default=noprint_wrappers=1 "$OUT"
echo "OUT: $OUT"
