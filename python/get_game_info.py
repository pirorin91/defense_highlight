import sys
import requests
from bs4 import BeautifulSoup
import json

def get_game_info(date, team_name):
    # スケジュールページのURLを生成
    url = f"https://baseball.yahoo.co.jp/npb/schedule/?date={date}"
    res = requests.get(url)
    soup = BeautifulSoup(res.content, "html.parser")

    # 各試合リンクを探索
    for a in soup.select("a.bb-score__content"):
        # ホーム・アウェイチーム名の取得
        home_tag = a.select_one("p.bb-score__homeLogo")
        away_tag = a.select_one("p.bb-score__awayLogo")
        home_team = home_tag.text.strip() if home_tag else ""
        away_team = away_tag.text.strip() if away_tag else ""

        # 指定チームがどちらかに含まれているか判定
        if team_name == home_team or team_name == away_team:
            game_url = a.get("href")
            # 絶対URLに変換
            if not game_url.startswith("http"):
                game_url = "https://baseball.yahoo.co.jp" + game_url
            # "index" を "text" に置換
            if game_url.endswith("index"):
                game_url = game_url[:-5] + "text"

            return {
                "game_url": game_url,
                "home_team": home_team,
                "away_team": away_team
            }

    # 見つからなかった場合
    return {
        "error": "指定したチームの試合が見つかりませんでした"
    }

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(json.dumps({"error": "引数にdateとteam_nameが必要です"}, ensure_ascii=False))
        sys.exit(1)
    date = sys.argv[1]  # 例: 2025-04-20
    team_name = sys.argv[2]
    info = get_game_info(date, team_name)
    print(json.dumps(info, ensure_ascii=False))