def scrape_weather_data(start_time: str, end_time: str, output_csv: str):
    # ここにスクレイピング処理を書く予定（仮のダミーデータを出力）
    import pandas as pd
    import datetime

    timestamps = pd.date_range(start=start_time, end=end_time, freq="H")
    dummy_data = {
        "時刻": timestamps,
        "気温": [20 + i % 5 for i in range(len(timestamps))],
        "湿度": [60 + i % 10 for i in range(len(timestamps))],
        "風速": [5 + i % 3 for i in range(len(timestamps))]
    }
    df = pd.DataFrame(dummy_data)
    df.to_csv(output_csv, index=False)
