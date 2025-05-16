import pandas as pd
import datetime
import requests
from bs4 import BeautifulSoup
import os

# 辞書をグローバルに定義
DIRECTION_TO_DEGREES = {
    "北": 0, "北北東": 22.5, "北東": 45, "東北東": 67.5,
    "東": 90, "東南東": 112.5, "南東": 135, "南南東": 157.5,
    "南": 180, "南南西": 202.5, "南西": 225, "西南西": 247.5,
    "西": 270, "西北西": 292.5, "北西": 315, "北北西": 337.5
}

def try_fetch_valid_kind(base_url_template, prec_no, block_no, year, month, day):
    """
    kind='10min_s1' → '10min_a1' の順で試行。
    データが存在するkindとsoupを返す。
    """
    for kind in ['10min_s1', '10min_a1']:
        url = base_url_template.format(
            kind=kind,
            prec_no=prec_no,
            block_no=block_no,
            year=year,
            month=month,
            day=day
        )
        print(f"Fetching URL: {url}")  # デバッグ用
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            data_rows = soup.find_all('tr', class_='mtx')
            if data_rows:  # データが存在する
                return kind, soup
        except Exception:
            continue
    raise ValueError("10分毎データが station/airplane どちらでも見つかりませんでした。")


def scrape_weather_data(start_time: str, end_time: str, output_csv: str,
                        prec_no: int = 91, block_no: str = "47945"):
    start_dt = datetime.datetime.fromisoformat(start_time)
    end_dt = datetime.datetime.fromisoformat(end_time)

    base_url = "https://www.data.jma.go.jp/stats/etrn/view/{kind}.php?prec_no={prec_no}&block_no={block_no}&year={year}&month={month}&day={day}&view="
    all_data = []

    for single_date in pd.date_range(start=start_dt.date(), end=end_dt.date()):
        year, month, day = single_date.year, single_date.month, single_date.day

        try:
            kind, soup = try_fetch_valid_kind(base_url, prec_no, block_no, year, month, day)
        except Exception as e:
            print(f"[{year}-{month}-{day}] 取得失敗: {e}")
            continue

    rows = soup.find_all("tr", class_="mtx")

    # 共通のカラム名
    keys = [
        "現地気圧", "海面気圧", "降水量", "気温", "相対湿度",
        "平均風速", "風向", "最大風速", "最大風向", "日照時間"
    ]

    if kind == "10min_a1":
        keys = [
            "降水量", "気温", "相対湿度",
            "平均風速", "風向", "最大風速", "最大風向", "日照時間"
        ]

    all_data = []

    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 2:
            continue

        # 時刻の処理（24:00 → 翌日 00:00）
        time_text = cols[0].text.strip()
        try:
            hour, minute = map(int, time_text.split(":"))
            time_obj = datetime.datetime(year, month, day) + datetime.timedelta(hours=hour % 24, minutes=minute)
            if hour == 24:
                time_obj += datetime.timedelta(days=1)
        except Exception:
            continue

        record = {"時": time_obj}
        for i, key in enumerate(keys, start=1):
            try:
                val = cols[i].text.strip()
                # ✅ 欠損判定を正確にする（- や "" を None に）
                if val in ["", "-", "--", "×", "///"]:
                    record[key] = None
                else:
                    record[key] = val
            except IndexError:
                record[key] = None

        all_data.append(record)

    # ステップ 1: スクレイピング直後の raw データ件数を確認
    print("[DEBUG 1] all_data 行数:", len(all_data))

    df = pd.DataFrame(all_data)
    print("[DEBUG 2] DataFrame 作成後 行数:", len(df), "列:", df.columns.tolist())

    # ステップ 2: dropna (列除去) 前の DataFrame のサンプル表示
    print("[DEBUG 3] 最初の2行:\n", df.head(2))

    # ステップ 3: カラム dropna 実行
    df.dropna(axis=1, how="all", inplace=True)
    df.drop(columns=[col for col in df.columns if df[col].eq("").all()], inplace=True)
    print("[DEBUG 4] dropna (列) 後の列:", df.columns.tolist())

    # ステップ 4: 行 dropna 実行
    df.dropna(axis=0, how="all", inplace=True)
    print("[DEBUG 5] dropna (行) 後の行数:", len(df))

    # ステップ 5: 時刻での絞り込み前の最大・最小確認
    if not df.empty:
        print("[DEBUG 6] 時刻の最小:", df['時'].min(), "最大:", df['時'].max())
    else:
        print("[DEBUG 6] 時刻カラムが存在しないか、全データが dropされた")

    # 出力
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    df.to_csv(output_csv, index=False, encoding="utf-8-sig")
