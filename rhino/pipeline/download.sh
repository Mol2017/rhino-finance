#!/usr/bin/env bash
# usage: download.sh <ids_file> <media_dir> <yt-dlp path>
# Slow, polite download using Chrome Default profile login (members-only access).
set -u
IDS=$1; OUT=$2; Y=$3
while read -r id rest; do
  [ -z "$id" ] && continue
  d=$OUT/$id; mkdir -p "$d"
  if [ -f "$d/audio.m4a" ] && [ -f "$d/video.mp4" ]; then echo "skip $id"; continue; fi
  "$Y" --no-update --cookies-from-browser 'chrome:Default' -q --no-warnings \
     --write-info-json --no-write-playlist-metafiles \
     -f 'bv*[height<=720][ext=mp4]+ba[ext=m4a]/b[height<=720]' -k \
     -o "$d/full.%(ext)s" "https://www.youtube.com/watch?v=$id" < /dev/null \
     && ffmpeg -nostdin -loglevel error -y -i "$d/full.mp4" -vn -c:a copy "$d/audio.m4a" \
     && ffmpeg -nostdin -loglevel error -y -i "$d/full.mp4" -an -c:v copy "$d/video.mp4" \
     && rm -f "$d/full.mp4" "$d"/full.f*.* \
     && echo "ok $id" || echo "FAIL $id"
  sleep $((30 + RANDOM % 31))
done < "$IDS"
echo DONE
