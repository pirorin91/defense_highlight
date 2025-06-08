import requests
from bs4 import BeautifulSoup
import re
import os
import csv

TEAM_MAP = {
    "埼玉西武ライオンズ": "西武",
    "北海道日本ハムファイターズ": "日本ハム",
    "千葉ロッテマリーンズ": "ロッテ",
    "オリックス・バファローズ": "オリックス",
    "福岡ソフトバンクホークス": "ソフトバンク",
    "東北楽天ゴールデンイーグルス": "楽天",
}

def create_player_db():
    URLS = [
        "https://baseball.yahoo.co.jp/npb/teams/7/memberlist?kind=b",
        "https://baseball.yahoo.co.jp/npb/teams/8/memberlist?kind=b",
        "https://baseball.yahoo.co.jp/npb/teams/9/memberlist?kind=b",
        "https://baseball.yahoo.co.jp/npb/teams/11/memberlist?kind=b",
        "https://baseball.yahoo.co.jp/npb/teams/12/memberlist?kind=b",
        "https://baseball.yahoo.co.jp/npb/teams/376/memberlist?kind=b",
    ]

    out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data"))
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "players_info.csv")

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Player ID", "Name", "Team"])
        writer.writeheader()

        for URL in URLS:
            response = requests.get(URL)
            soup = BeautifulSoup(response.content, "html.parser")

            # チーム名取得
            team_elem = soup.find(class_="bb-title02__title")
            team_raw = team_elem.text.strip() if team_elem else "Unknown"
            team = TEAM_MAP.get(team_raw, team_raw)

            table = soup.find("table")
            if table:
                for row in table.find_all("tr")[1:]:  # ヘッダー除外
                    name_td = row.find("td", class_="bb-playerTable__data bb-playerTable__data--player")
                    if not name_td:
                        continue
                    name_link = name_td.find("a")
                    if name_link and "href" in name_link.attrs:
                        name = name_link.text.strip()
                        href = name_link["href"]
                        m = re.search(r"/player/(\d+)/", href)
                        player_id = m.group(1) if m else ""
                        writer.writerow({
                            "Player ID": player_id,
                            "Name": name,
                            "Team": team
                        })
    print("players_info.csv を出力しました。")

if __name__ == "__main__":
    try:
        create_player_db()
    except Exception as e:
        print(f"エラー: {e}")
