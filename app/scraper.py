import pandas as pd
import datetime
import requests
from bs4 import BeautifulSoup
import os
import numpy as np

# 辞書をグローバルに定義
DIRECTION_TO_DEGREES = {
    "北": 0, "北北東": 22.5, "北東": 45, "東北東": 67.5,
    "東": 90, "東南東": 112.5, "南東": 135, "南南東": 157.5,
    "南": 180, "南南西": 202.5, "南西": 225, "西南西": 247.5,
    "西": 270, "西北西": 292.5, "北西": 315, "北北西": 337.5
}

# 露点温度を計算する関数
null_values = {"", "-", "--", "×", "///"}

def to_none(cell):
    return None if cell in null_values else cell
def is_empty_cell(cell):
    return pd.isna(cell) or cell in ["", "-", "--", "×", "///", None]

def calculate_dew_point_row(row):
    T = row.get("気温")
    RH = row.get("相対湿度")
    # print(f"Calculating dew point for T={T}, RH={RH}")

    try:
        if is_empty_cell(T) or is_empty_cell(RH):
            print("Empty cell detected, returning NaN")
            return None
        T = float(T)
        RH = float(RH)

        if RH <= 0 or RH > 100:
            print("Invalid input, returning NaN")
            return np.nan

        a = 17.62
        b = 243.12
        gamma = (a * T) / (b + T) + np.log(RH / 100)
        dew_point = (b * gamma) / (a - gamma)

        if not np.isfinite(dew_point):
            print("Computed dew point is not finite, returning NaN")
            return np.nan

        # print(f"Dew point calculated: {dew_point}")
        return dew_point

    except Exception as e:
        print(f"Error calculating dew point: {e}")
        return np.nan


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

        if kind == "10min_a1":
            keys = ["降水量", "気温", "相対湿度", "平均風速", "風向", "最大風速", "最大風向", "日照時間"]
        else:
            keys = ["現地気圧", "海面気圧", "降水量", "気温", "相対湿度", "平均風速", "風向", "最大風速", "最大風向", "日照時間"]

        table = soup.find("table", id="tablefix1")
        if not table:
            print(f"[{year}-{month}-{day}] tablefix1 が見つかりませんでした")
            continue

        rows = table.find_all("tr")

        for row in rows:
            cols = row.find_all(["td", "th"])
            if len(cols) < 2:
                continue

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
                    record[key] = val
                except IndexError:
                    record[key] = None

            all_data.append(record)

    df = pd.DataFrame(all_data)

    # 全ての値が NaN または "" の列を削除
    # df = df.loc[:, ~df.apply(lambda col: all(cell in [None, ""] or pd.isna(cell) for cell in col), axis=0)]

    # 全ての値が NaN または "" の行を削除
    # df = df.loc[~df.apply(lambda row: all(cell in [None, ""] or pd.isna(cell) for cell in row), axis=1)]

    df = df[(df["時"] >= start_dt) & (df["時"] <= end_dt)]
    
    # 気温と相対湿度があれば、露点温度を計算
    if {"気温", "相対湿度"}.issubset(df.columns):
        print("露点温度を計算中...")
        df["露点温度"] = df.apply(calculate_dew_point_row, axis=1)
    # print(df.columns)
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    df.to_csv(output_csv, index=False, encoding="utf-8-sig")
