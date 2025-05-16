import csv

def load_prefecture_list(csv_path="prefectures.csv"):
    prefectures = []
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            prefectures.append({
                "prec_no": int(row["prec_no"]),
                "pref_name": row["pref_name"]
            })
    return prefectures

def load_station_list(csv_path="stations.csv"):
    stations = []
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            stations.append({
                "name": row["name"],
                "block_no": row["block_no"],
                "prec_no": int(row["prec_no"])
            })
    return stations