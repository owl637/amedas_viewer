import re
import csv
import requests
from bs4 import BeautifulSoup

output_file = "stations.csv"
base_url = "https://www.data.jma.go.jp/stats/etrn/select/prefecture.php?prec_no={}&block_no=&year=&month=&day=&view="

# 重複排除のための辞書
all_points = {}

for prec_no in range(1, 101):
    url = base_url.format(prec_no)
    print(f"Fetching: {url}")
    try:
        response = requests.get(url, timeout=10)
        response.encoding = response.apparent_encoding
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        continue

    soup = BeautifulSoup(response.text, "lxml")
    map_tag = soup.find("map", {"name": "point"})
    if not map_tag:
        print(f"No <map> tag found for prec_no={prec_no}")
        continue

    for area in map_tag.find_all("area"):
        if not area.has_attr("onmouseover"):
            continue
        alt = area.get("alt")
        href = area.get("href")
        if not alt or not href or "index.php" not in href:
            continue

        match = re.search(r"prec_no=(\d+)&block_no=(\d+)", href)
        if match:
            p_no, block_no = match.groups()
            key = (alt, p_no, block_no)
            all_points[key] = {"name": alt, "prec_no": p_no, "block_no": block_no}

# CSVに出力
with open(output_file, "w", newline='', encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["name", "prec_no", "block_no"])
    for point in all_points.values():
        writer.writerow([point["name"], point["prec_no"], point["block_no"]])

print(f"{len(all_points)} 件の観測点を {output_file} に保存しました。")
