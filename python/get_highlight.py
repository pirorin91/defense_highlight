#!/usr/bin/env python3
import sys
import requests
from bs4 import BeautifulSoup
import json
import re

position_names = (
    ('ピッチャー', 'キャッチャー', 'ファースト', 'セカンド', 'サード', 'ショート', 'レフト', 'センター', 'ライト', 'DH'),
    ('投', '捕', '一', '二', '三', '遊', '左', '中', '右', '指'),
    ('1', '2', '3', '4', '5', '6', '7', '8', '9', 'DH')
)

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

    # 試合終了判定
    all_summaries = soup.find_all('p', class_='bb-liveText__summary')
    is_live = True
    if all_summaries:
        if all_summaries[-1].get_text(strip=True) == "試合終了":
            is_live = False

    # liveの場合はreverseで処理
    inning_iter = reversed(inning_sections) if is_live else inning_sections

    position_index = None
    for section in inning_iter:
        inning_label = section.find('h1', class_='bb-liveText__inning')
        if not inning_label:
            continue
        inning_text = inning_label.text.strip()
        if inning_text == "試合前情報":
            # Player IDに基づいてポジションを更新
            player_link = section.find('a', href=lambda href: href and player_id in href)
            if player_link:
                # player_linkの直後のbb-liveText__stateクラスのspan要素を取得
                next_span = player_link.find_next_sibling('span', class_='bb-liveText__state')
                if next_span:
                    position_text = next_span.get_text().strip()

                    if position_text and "(" in position_text and ")" in position_text:
                        position_code = position_text[position_text.find("(") + 1:position_text.find(")")]

                        if position_code in position_names[1]:
                            index = position_names[1].index(position_code)
                            position_index = index
                            # 先発ポジションをJSON形式で出力
                            print(json.dumps({"ining": inning_text, "text": f"{position_names[0][position_index]}で先発", "is_highlight": False}, ensure_ascii=False))
                        else:
                            print(f"ERROR: position_code '{position_code}' not found in position_names[1]", file=sys.stderr)
                    else:
                        print(f"ERROR: position_text format invalid: '{position_text}'", file=sys.stderr)
                else:
                    print(f"ERROR: next span not found for player {player_id}", file=sys.stderr)
            else:
                # ベンチスタートの場合
                print(json.dumps({"ining": inning_text, "text": "ベンチスタート", "is_highlight": False}, ensure_ascii=False))
        elif top_bottom in inning_text:
            # olタグ内のli（打席ごと）をループ
            ol = section.find('ol', class_='bb-liveText__orderedList')
            if ol:
                items = ol.find_all('li', class_='bb-liveText__item')
                # 打席（li）自体を逆順にする
                item_iter = reversed(items) if is_live else items
                for item in item_iter:
                    batter_info = item.find('p', class_='bb-liveText__batter')
                    if not batter_info:
                        continue
                    batter_number = item.find('p', class_='bb-liveText__number')
                    batter_name_tag = batter_info.find('a', class_='bb-liveText__player')
                    if not (batter_number and batter_name_tag):
                        continue
                    batter_name = batter_name_tag.text.strip()
                    summaries = item.find_all('p', class_='bb-liveText__summary')
                    for summary in summaries:
                        if "bb-liveText__summary--change" in summary.get("class", []):
                            # Player IDに基づいてポジションを更新
                            player_link = summary.find('a', href=lambda href: href and player_id in href)
                            if player_link:
                                # "→ファースト" のような文字列を探す
                                position_text = player_link.find_next_sibling(string=True)
                                if position_text and "→" in position_text:
                                    position_text_strip = position_text.split("→")[1].strip()
                                    for idx, pos in enumerate(position_names[0]):
                                        if position_text_strip.startswith(pos):
                                            position_index = idx
                                            break
                                    # 守備変更をJSON形式で出力（iningも追加、textからinning_textを除外）
                                    print(json.dumps({"ining": inning_text, "text": f"守備変更 {position_names[0][position_index]}", "is_highlight": False}, ensure_ascii=False))
                                    break
                                # "守備交代:サード " のような文字列を探す
                                position_text = player_link.find_previous_sibling(string=True)
                                if position_text and "守備交代:" in position_text:
                                    position_text_strip = position_text.split("守備交代:")[1].strip()
                                    if position_text_strip in position_names[0]:
                                        position_index = position_names[0].index(position_text_strip)
                                        # 守備交代をJSON形式で出力（iningも追加、textからinning_textを除外）
                                        print(json.dumps({"ining": inning_text, "text": f"守備交代 {position_names[0][position_index]}", "is_highlight": False}, ensure_ascii=False))
                                        break
                        else:
                            # 通常の処理
                            double_play_match = re.findall(r'(\d-\d-\d)', summary.text)
                            double_play_positions = []
                            if double_play_match:
                                # 例: "5-4-3" → ['5', '4', '3']
                                double_play_positions = double_play_match[0].split('-')
                            if position_index is not None and (
                                position_names[0][position_index] in summary.text or
                                f"({position_names[1][position_index]})" in summary.text or
                                (double_play_positions and position_names[2][position_index] in double_play_positions)
                            ):
                                cleaned_summary = re.sub(r'\s+', ' ', summary.text).strip()
                                print(json.dumps({
                                    "ining": inning_text,
                                    "text": f"{batter_number.text.strip('：')}人目の打者 {batter_name} {cleaned_summary}",
                                    "is_highlight": True
                                }, ensure_ascii=False))

if __name__ == "__main__":
    # サンプルURL
    # url = "https://baseball.yahoo.co.jp/npb/game/2021029150/text"
    # url = "https://baseball.yahoo.co.jp/npb/game/2021029156/text"
    # top_bottom = "表"  # 例: "裏"
    # top_bottom = "裏"  # 例: "裏"
    # player_id = "1700025"  # 例: 1700025 (清宮)
    # player_id = "1300109"  # 例: 1300109 (若月)
    # player_id = "1400119"  # 例: 1400119 (淺間)
    # player_id = "2107900"  # 例: 2107900 (吉田)

    url = sys.argv[1]
    top_bottom = sys.argv[2]
    player_id = sys.argv[3]
    get_highlight(url, top_bottom, player_id)