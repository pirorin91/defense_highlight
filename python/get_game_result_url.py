#!/usr/bin/env python3
import sys
import requests
from bs4 import BeautifulSoup
import json

def get_game_result_url(team_name, date):
    # 対象のURL（指定された日付を使用）
    url = f"https://baseball.yahoo.co.jp/npb/schedule/?date={date}"

    # HTMLを取得
    response = requests.get(url)
    response.raise_for_status()  # エラーがあれば例外を発生させる
    soup = BeautifulSoup(response.text, 'html.parser')

    # 試合結果リンクを探す
    game_links = soup.find_all('a', href=True)
    for link in game_links:
        href = link['href']
        # 対象リンクが試合結果ページであるか確認
        if "game" in href and (team_name in link.text):
            # チームがホームかどうかを判定
            teams = link.text.split("\n")
            if len(teams) > 6:
                is_home = teams[5] == team_name  # 6番目にチーム名があればホーム
                # "index" を "text" に置換
                href = href.replace("index", "text")
                return href, is_home

    return f"{team_name}の試合結果リンクが見つかりませんでした。", None

if __name__ == "__main__":
    date = sys.argv[1]
    team_name = sys.argv[2]
    result_url, is_home = get_game_result_url(team_name, date)
    output = {"url": result_url}
    if is_home is not None:
        output["is_home"] = is_home
    print(json.dumps(output, ensure_ascii=False))
