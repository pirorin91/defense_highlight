#!/usr/bin/env python3
import sys
import requests
from bs4 import BeautifulSoup
import json

position_names = (('ピッチャー', 'キャッチャー', 'ファースト', 'セカンド', 'サード', 'ショート', 'レフト', 'センター', 'ライト', 'DH'),
                  ('投', '捕', '一', '二', '三', '遊', '左', '中', '右', '指'))

def get_highlight(url, top_bottom, player_id):
    """
    指定された表/裏、Player IDに基づいて試合経過を取得する。

    Args:
        url (str): 試合経過ページのURL
        top_bottom (str): "表" または "裏"
        player_id (str): 選手のID（例: "1700025"）

    Returns:
        list: 指定された条件に一致するテキストのリスト
    """
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')

    # イニングごとのデータを取得
    inning_sections = soup.find_all('section', class_='bb-liveText')
    if not inning_sections:
        raise ValueError("指定されたHTML構造にイニングデータが見つかりません。URLやHTML構造を確認してください。")

    # 全てのイニングを処理
    position = ''
    for section in inning_sections:
        inning_label = section.find('h1', class_='bb-liveText__inning')
        if inning_label:
            inning_text = inning_label.text.strip()
            if inning_text == "試合前情報":
                # Player IDに基づいてポジションを更新
                player_link = section.find('a', href=lambda href: href and player_id in href)
                if player_link:
                    # "(投)" のような文字列を探す
                    position_text = player_link.find_next_sibling(string=True)
                    if position_text and "(" in position_text and ")" in position_text:
                        position_code = position_text[position_text.find("(") + 1:position_text.find(")")]
                        if position_code in position_names[1]:
                            index = position_names[1].index(position_code)
                            position = position_names[0][index]
                            # 先発ポジションをJSON形式で出力（iningも追加）
                            print(json.dumps({"ining": inning_text, "text": f"{position}で先発", "is_highlight": False}, ensure_ascii=False))
                else:
                    # ベンチスタートの場合もJSON形式で出力（iningも追加）
                    print(json.dumps({"ining": inning_text, "text": "ベンチスタート", "is_highlight": False}, ensure_ascii=False))
            elif top_bottom in inning_text:
                # 指定された表/裏に一致するセクションを処理
                summaries = section.find_all('p', class_='bb-liveText__summary')
                for summary in summaries:
                    # "bb-liveText__summary--change" クラスがセットされている場合の処理
                    if "bb-liveText__summary--change" in summary.get("class", []):
                        # Player IDに基づいてポジションを更新
                        player_link = summary.find('a', href=lambda href: href and player_id in href)
                        if player_link:
                            # "→ファースト" のような文字列を探す
                            position_text = player_link.find_next_sibling(string=True)
                            if position_text and "→" in position_text:
                                position_text_strip = position_text.split("→")[1].strip()
                                for pos in position_names[0]:
                                    if position_text_strip.startswith(pos):
                                        position = pos
                                        break
                                # 守備変更をJSON形式で出力（iningも追加、textからinning_textを除外）
                                print(json.dumps({"ining": inning_text, "text": f"守備変更 {position}", "is_highlight": False}, ensure_ascii=False))
                                break

                            # "守備交代:サード " のような文字列を探す
                            position_text = player_link.find_previous_sibling(string=True)
                            if position_text and "守備交代:" in position_text:
                                position_text_strip = position_text.split("守備交代:")[1].strip()
                                if position_text_strip in position_names[0]:
                                    position = position_text_strip
                                    # 守備交代をJSON形式で出力（iningも追加、textからinning_textを除外）
                                    print(json.dumps({"ining": inning_text, "text": f"守備交代 {position}", "is_highlight": False}, ensure_ascii=False))
                                    break
                    else:
                        # 通常の処理
                        if position and position in summary.text:
                            batter_number = summary.find_previous('p', class_='bb-liveText__number')
                            batter_name = summary.find_previous('a', class_='bb-liveText__player')
                            if batter_number and batter_name:
                                # 打席情報をJSON形式で出力（iningも追加、textからinning_textを除外）
                                print(json.dumps({"ining": inning_text, "text": f"{batter_number.text.strip('：')}人目の打者 {batter_name.text.strip()} {summary.text.strip()}", "is_highlight": True}, ensure_ascii=False))

if __name__ == "__main__":
    # サンプルURL
    # url = "https://baseball.yahoo.co.jp/npb/game/2021029156/text"
    # top_bottom = "表"  # 例: "裏"
    # player_id = "1700025"  # 例: 1700025 (清宮)
    # player_id = "1300109"  # 例: 1300109 (若月)
    # player_id = "1400119"  # 例: 1400119 (淺間)
    # player_id = "2107900"  # 例: 2107900 (吉田)

    url = sys.argv[1]
    top_bottom = sys.argv[2]
    player_id = sys.argv[3]
    get_highlight(url, top_bottom, player_id)