"""
将 viz_data.json 和 HK.json (GeoJSON) 都内嵌到 visualization.html 中，
生成一个完全离线可用的独立 HTML 文件。
"""
import json
import os

os.chdir(r'd:\hkust\DV\Group Project\Group Project')

with open('viz_data.json', 'r', encoding='utf-8') as f:
    data_json = f.read()

with open('HK.json', 'r', encoding='utf-8') as f:
    geo_json = f.read()

with open('visualization.html', 'r', encoding='utf-8') as f:
    html = f.read()

old_block = """Promise.all([
  fetch('viz_data.json').then(r => r.json()),
  fetch(HK_GEOJSON_URL).then(r => r.json()),
]).then(([D, geoData]) => {
  echarts.registerMap('HK', geoData);
  renderMap(D.chart_map);
  if (D.t2_synced) renderT2Synced(D.t2_synced);
  if (D.t2_stream) { renderLiquidBalls(D.t2_stream.recovery, D.t2_stream.venues); renderT2Stream(D.t2_stream); }
}).catch(() => {
  fetch('viz_data.json').then(r => r.json()).then(D => {
    renderMapFallback(D.chart_map);
    if (D.t2_synced) renderT2Synced(D.t2_synced);
    if (D.t2_stream) { renderLiquidBalls(D.t2_stream.recovery, D.t2_stream.venues); renderT2Stream(D.t2_stream); }
  });
});"""

new_block = f"""const D = {data_json};
const _geoHK = {geo_json};
echarts.registerMap('HK', _geoHK);
requestAnimationFrame(function() {{
  renderMap(D.chart_map);
  if (D.t2_synced) renderT2Synced(D.t2_synced);
  if (D.t2_stream) {{ renderLiquidBalls(D.t2_stream.recovery, D.t2_stream.venues); renderT2Stream(D.t2_stream); }}
}});"""

if old_block not in html:
    print("ERROR: Could not find the fetch block to replace!")
    exit(1)

html = html.replace(old_block, new_block)

with open('visualization_standalone.html', 'w', encoding='utf-8') as f:
    f.write(html)

size_kb = os.path.getsize('visualization_standalone.html') / 1024
print(f'Done! visualization_standalone.html ({size_kb:.0f} KB)')
