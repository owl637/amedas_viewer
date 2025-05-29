from flask import Blueprint, render_template, request, send_file, flash, redirect, url_for
import os
import pandas as pd
import numpy as np
from .scraper import scrape_weather_data
from flask import jsonify
from .utils import load_station_list, load_prefecture_list
from .config import CSV_CACHE_PATH

main_bp = Blueprint("main", __name__)
null_values = {"", "-", "--", "×", "///"}

def to_none(cell):
    return None if cell in null_values else cell
def is_empty_cell(cell):
    return pd.isna(cell) or cell in ["", "-", "--", "×", "///", None]
# routes.py 修正（/get_dataの代わりに/indexをPOSTでも扱う）

@main_bp.route("/", methods=["GET", "POST"])
def index():
    stations = load_station_list()
    prefectures = load_prefecture_list()

    if request.method == "POST":
        action = request.form.get("action")
        start_time = request.form.get("start_time")
        end_time = request.form.get("end_time")
        block_no = request.form.get("block_no")
        prec_no = request.form.get("prec_no")

        if action == "fetch":
            try:
                print(f"action: {action}, start_time: {start_time}, end_time: {end_time}, block_no: {block_no}, prec_no: {prec_no}")
                scrape_weather_data(start_time, end_time, output_csv=CSV_CACHE_PATH,
                                    prec_no=int(prec_no), block_no=block_no)
                df = pd.read_csv(CSV_CACHE_PATH)
                
                # 1. 一括で None に変換
                null_values = {"", "-", "--", "×", "///"}
                df["日照時間"] = df["日照時間"].apply(lambda x: "" if pd.isna(x) else x)
                df["日照時間"] = df["日照時間"].apply(lambda x: "" if x in null_values else x)
                df["露点温度"] = df["露点温度"].apply(lambda x: "" if pd.isna(x) else x)
                df["露点温度"] = df["露点温度"].apply(lambda x: "" if x in null_values else x)

                for col in df.columns:
                    if col == "日照時間" or col == "露点温度":
                        # 日照時間と露点温度は特別扱い
                        continue
                    df[col] = df[col].astype("object")  # まずobject型にしてから
                    df[col] = df[col].apply(
                        lambda x: None if pd.isna(x) or x in null_values else x
                    )
                    # print(df[col].isna().sum(), df[col].dtype)

            
                # 2. 不要な列を削除（全部 None の列）
                df = df.loc[:, ~df.apply(lambda col: all(cell is None for cell in col), axis=0)]

                # 空の列を削除
                df = df.loc[:, ~df.apply(lambda col: all(is_empty_cell(cell) for cell in col), axis=0)]

                # 3. 念のため NaN を None に再変換（プロットのため）
                df = df.where(df.notna(), None)

                columns = list(df.columns)
                columns.remove("時")

                return render_template("index.html",
                    stations=stations,
                    prefectures=prefectures,
                    columns=columns,
                    block_no=block_no,
                    prec_no=prec_no,
                    start_time=start_time,
                    end_time=end_time
                )

            except Exception as e:
                flash(f"取得失敗: {e}")
                return render_template("index.html",
                    stations=stations,
                    prefectures=prefectures,
                    block_no=block_no,
                    prec_no=prec_no,
                    start_time=start_time,
                    end_time=end_time
                )

        elif action == "plot":
            print(f"action: {action}, start_time: {start_time}, end_time: {end_time}, block_no: {block_no}, prec_no: {prec_no}")
            df = pd.read_csv(CSV_CACHE_PATH)

            # 1. 一括で None に変換
            null_values = {"", "-", "--", "×", "///"}
            df["日照時間"] = df["日照時間"].apply(lambda x: "" if pd.isna(x) else x)
            df["日照時間"] = df["日照時間"].apply(lambda x: "" if x in null_values else x)
            df["露点温度"] = df["露点温度"].apply(lambda x: "" if pd.isna(x) else x)
            df["露点温度"] = df["露点温度"].apply(lambda x: "" if x in null_values else x)
            # 日照時間と露点温度は特別扱い

            for col in df.columns:
                if col == "日照時間" or col == "露点温度":
                    # 日照時間と露点温度は特別扱い
                    continue
                df[col] = df[col].astype("object")  # まずobject型にしてから
                df[col] = df[col].apply(
                    lambda x: None if pd.isna(x) or x in null_values else x
                )
                # print(df[col].isna().sum(), df[col].dtype)

            

            # 2. 不要な列を削除（全部 None の列）
            df = df.loc[:, ~df.apply(lambda col: all(cell is None for cell in col), axis=0)]

            # 空の列を削除
            df = df.loc[:, ~df.apply(lambda col: all(is_empty_cell(cell) for cell in col), axis=0)]

            # 3. 念のため NaN を None に再変換（プロットのため）
            df = df.where(df.notna(), None)

            columns = list(df.columns)

            columns.remove("時")
            selected = request.form.getlist("elements")
            plot_data = []

            for col in selected[:3]:
                if col in df.columns:
                    plot_data.append({
                        "x": df["時"].astype(str).tolist(),
                        "y": df[col].tolist(),
                        "name": col
                    })

            return render_template("index.html",
                stations=stations,
                prefectures=prefectures,
                columns=columns,
                selected=selected,
                plot_data=plot_data,
                block_no=block_no,
                prec_no=prec_no,
                start_time=start_time,
                end_time=end_time
            )

    # 🔵 GETの場合の初期描画
    return render_template("index.html",
        stations=stations,
        prefectures=prefectures,
        prec_no=91,
        block_no=47945,
        start_time="2025-05-01T00:00",
        end_time="2025-05-02T00:00"
    )

from io import BytesIO

@main_bp.route("/download")
def download():
    with open(CSV_CACHE_PATH, "rb") as f:
        csv_bytes = BytesIO(f.read())

    csv_bytes.seek(0)
    return send_file(
        csv_bytes,
        as_attachment=True,
        download_name="latest.csv",
        mimetype="text/csv"
    )