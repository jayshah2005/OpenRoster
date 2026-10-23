#!/usr/bin/env bash
# Rebuild data/geo/cities.tsv from GeoNames cities5000 (CC BY 4.0). Canada + US only.
set -euo pipefail
cd "$(dirname "$0")/.."
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
curl -sSfL -o "$tmp/c.zip" https://download.geonames.org/export/dump/cities5000.zip
unzip -q "$tmp/c.zip" -d "$tmp"
awk -F'\t' 'BEGIN{OFS="\t"; split("01:AB 02:BC 03:MB 04:NB 05:NL 07:NS 08:ON 09:PE 10:QC 11:SK 12:YT 13:NT 14:NU",a," ");
  for(i in a){split(a[i],kv,":"); ca[kv[1]]=kv[2]}; print "name","region","country","lat","lon","pop"}
  ($9=="CA" && ($11 in ca)) || $9=="US" { reg = ($9=="CA") ? "CA-" ca[$11] : "US-" $11; print $2,reg,$9,$5,$6,$15 }' \
  "$tmp/cities5000.txt" > data/geo/cities.tsv
wc -l data/geo/cities.tsv
