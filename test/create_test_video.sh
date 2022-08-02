#!/usr/bin/env bash
#
# Create a test video containing a sequence of black and white periods

cd "$(dirname "$0")" || exit 1

ffmpeg \
  -y \
  -f lavfi -i color=black:d=5 \
  -f lavfi -i color=white:d=5 \
  -f lavfi -i color=black:d=5 \
  -f lavfi -i color=white:d=5 \
  -f lavfi -i color=black:d=5 \
  -f lavfi -i color=white:d=5 \
  -filter_complex "[0:v][1:v][2:v][3:v][4:v][5:v]concat=n=6:v=1:a=0[out]" \
  -map "[out]" \
  -c:v libx264 -pix_fmt yuv420p \
  test.mp4
