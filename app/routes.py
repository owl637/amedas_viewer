from flask import Blueprint, render_template, request, send_file, flash
import os
from .scraper import scrape_weather_data

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def index():
    return render_template("index.html")


@main_bp.route("/get_data", methods=["POST"])
def get_data():
    start_time = request.form.get("start_time")
    end_time = request.form.get("end_time")

    if not start_time or not end_time:
        flash("開始日時と終了日時を指定してください。")
        return render_template("index.html")

    # CSVファイル名の作成（例：data/20240513_1200_1300.csv）
    csv_filename = f"data/{start_time.replace(':', '').replace('-', '')}_{end_time.replace(':', '').replace('-', '')}.csv"
    os.makedirs("data", exist_ok=True)

    # スクレイピングしてCSV保存
    try:
        scrape_weather_data(start_time, end_time, csv_filename)
    except Exception as e:
        flash(f"データ取得に失敗しました: {str(e)}")
        return render_template("index.html")

    # CSVを返す（今はダウンロードするだけの構成）
    return send_file(csv_filename, as_attachment=True)
