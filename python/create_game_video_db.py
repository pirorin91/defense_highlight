# 必要なライブラリをインストールしてください:
# pip install requests beautifulsoup4

import requests
from bs4 import BeautifulSoup
import re
import csv
import os

def get_start_id():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    data_dir = os.path.join(base_dir, "data")
    csv_path = os.path.join(data_dir, "game_video_info.csv")
    if not os.path.exists(csv_path):
        return 501995
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            rows = list(csv.reader(f))
            if len(rows) <= 1:
                return 501995
            last_row = rows[-1]
            return int(last_row[0]) + 1
    except Exception:
        return 501995

def create_game_video_db():
    current_id = get_start_id()
    not_found_count = 0  # 連続で該当フォーマットが見つからなかった回数
    while True:
        content_id = str(current_id)
        url = f"https://sports.tv.rakuten.co.jp/pacificleague/content/{content_id}/"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")

        # <title>要素のテキストを取得
        title_text = soup.title.get_text(strip=True)
        match = re.search(r"(\d{4}/\d{1,2}/\d{1,2}) (\d{1,2}:\d{2}) (.+) VS (.+)", title_text)
        if match:
            date, time, home, away = match.groups()
            away = away.split()[0] if " " in away else away

            tail4 = content_id[-4:].zfill(4)
            dir1 = tail4[0:2][::-1]  # 前半2文字を逆順に
            dir2 = tail4[2:4][::-1]  # 後半2文字を逆順に
            image_url = f"https://im.akimg.tv.rakuten.co.jp/content/{dir1}/{dir2}/{content_id}/main.jpg"

            # CSVファイルを一つ上のディレクトリの"data"フォルダに出力
            base_dir = os.path.dirname(os.path.dirname(__file__))
            data_dir = os.path.join(base_dir, "data")
            os.makedirs(data_dir, exist_ok=True)
            csv_path = os.path.join(data_dir, "game_video_info.csv")
            write_header = not os.path.exists(csv_path)
            with open(csv_path, "a", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                if write_header:
                    writer.writerow(["id", "date", "time", "home", "away", "url", "image"])
                writer.writerow([content_id, date, time, home, away, url, image_url])
            print(f"{csv_path} に追記しました")
            print(f"{content_id} {date} {time} {home} VS {away}")
            current_id += 1
            not_found_count = 0  # 成功したらリセット
        else:
            print(f"{content_id}: 該当フォーマットが見つかりませんでした。")
            not_found_count += 1
            current_id += 1
            if not_found_count >= 10:
                print("10回連続で該当フォーマットが見つかりませんでした。処理を終了します。")
                break

# 使用例
if __name__ == "__main__":
    try:
        create_game_video_db()
    except Exception as e:
        print(f"エラー: {e}")
