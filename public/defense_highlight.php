<?php
setlocale(LC_CTYPE, 'ja_JP.UTF-8');

// Pythonスクリプトを呼び出してget_game_result_urlを実行
function get_game_result_url($date, $team) {
    $cmd = escapeshellcmd("python3 ../python/get_game_result_url.py " . escapeshellarg($date) . " " . escapeshellarg($team));
    $output = shell_exec($cmd);
    // Python側でJSON文字列を返すようにしておく
    $result = json_decode($output, true);
    return $result;
}

// Pythonスクリプトを呼び出してget_highlightを実行
function get_highlight($url, $is_home, $player_id) {
    $cmd = escapeshellcmd("python3 ../python/get_highlight.py " . escapeshellarg($url) . " " . escapeshellarg($is_home) . " " . escapeshellarg($player_id));
    $output = shell_exec($cmd);
    return $output;
}

// 指定した日付・チームに該当する動画URLとサムネイル画像URLをCSVから取得
function get_game_video_info($date, $team) {
    // '2025-04-20' → '2025/4/20' へ変換
    $date_obj = DateTime::createFromFormat('Y-m-d', $date);
    if ($date_obj) {
        $date = $date_obj->format('Y/n/j');
    }
    $csv_path = __DIR__ . '/../data/game_video_info.csv';
    if (!file_exists($csv_path)) return ['url' => '', 'image' => ''];
    $fp = fopen($csv_path, 'r');
    if (!$fp) return ['url' => '', 'image' => ''];
    $header = fgetcsv($fp);
    while ($row = fgetcsv($fp)) {
        $row_assoc = array_combine($header, $row);
        // 日付とチーム名が一致する行のurlとimageを返す
        if ($row_assoc['date'] === $date && ($row_assoc['home'] === $team || $row_assoc['away'] === $team)) {
            fclose($fp);
            return ['url' => $row_assoc['url'], 'image' => $row_assoc['image']];
        }
    }
    fclose($fp);
    return ['url' => '', 'image' => ''];
}

// players_info.csvを読み込んで選手名→Player ID, Teamの連想配列を作成
function load_players_info() {
    $csv_path = __DIR__ . '/../data/players_info.csv';
    if (!file_exists($csv_path)) return [];
    $fp = fopen($csv_path, 'r');
    if (!$fp) return [];
    $header = fgetcsv($fp);
    $players = [];
    while ($row = fgetcsv($fp)) {
        $row_assoc = array_combine($header, $row);
        $players[$row_assoc['Name']] = [
            'Player ID' => $row_assoc['Player ID'],
            'Team' => $row_assoc['Team']
        ];
    }
    fclose($fp);
    return $players;
}

// 選手情報を読み込み、選手名リストを作成
$players_info = load_players_info();
$player_names = array_keys($players_info);

// フォームからの入力取得
$date = $_POST['date'] ?? '';
$player_name = $_POST['player_name'] ?? '';
$result_lines = [];

// フォーム送信時の処理
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($players_info[$player_name])) {
    $player_id = $players_info[$player_name]['Player ID'];
    $team = $players_info[$player_name]['Team'];
    $game_info = get_game_result_url($date, $team);
    // 守備なのでホームなら表、アウェイなら裏
    $is_home_str = $game_info['is_home'] ? '表' : '裏';
    $highlight_output = get_highlight($game_info['url'], $is_home_str, $player_id);
    $video_info = get_game_video_info($date, $team); // urlとimageを取得

    // get_highlight.pyの出力各行(JSON)をパースし、iningとtextを表示
    foreach (explode("\n", $highlight_output) as $line) {
        $line = trim($line);
        if ($line === '') continue;
        $json = json_decode($line, true);
        if (!$json || !isset($json['ining']) || !isset($json['text'])) continue;
            $text = htmlspecialchars($json['ining'] . ' ' . $json['text']);
        $is_highlight = isset($json['is_highlight']) && $json['is_highlight'];
        $li_class = $is_highlight ? 'highlight-true' : 'highlight-false';
        if ($is_highlight && $video_info['url'] && $video_info['image']) {
                $text .= ' <a href="' . htmlspecialchars($video_info['url']) . '" target="_blank">'
                    . '<img src="' . htmlspecialchars($video_info['image']) . '" alt="動画リンク" style="height:40px;vertical-align:middle;">'
                    . '</a>';
            }
        $result_lines[] = ['text' => $text, 'class' => $li_class];
    }
}
?>

<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>守備ハイライト</title>
    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            background: #f5f7fa;
            color: #222;
        }
        .main-container {
            max-width: 600px;
            margin: 40px auto;
            background: #fff;
            border-radius: 16px;
            box-shadow: 0 4px 24px rgba(0,0,0,0.08);
            padding: 2rem 2.5rem;
        }
        h1 {
            color: #0b4e9b;
            font-weight: 700;
            letter-spacing: 2px;
        }
        .form-label {
            color: #0b4e9b;
            font-weight: 600;
        }
        .btn-primary {
            background: #0b4e9b;
            border: none;
        }
        .btn-primary:hover {
            background: #1e7fc7;
        }
        .highlight-list li {
            margin-bottom: 1.2em;
            font-size: 1.1em;
            background: #eaf3fb;
            border-radius: 8px;
            padding: 0.8em 1em;
            box-shadow: 0 1px 3px rgba(11,78,155,0.05);
            display: flex;
            align-items: center;
        }
        .highlight-list img {
            margin-left: 1em;
            border-radius: 6px;
            border: 1px solid #cce0f7;
            box-shadow: 0 1px 4px rgba(11,78,155,0.08);
            transition: transform 0.2s;
        }
        .highlight-list img:hover {
            transform: scale(1.08);
        }
        .highlight-list .highlight-true {
            background: #b3d1f7; /* 濃いめの青系 */
        }
        .highlight-list .highlight-false {
            background: #eaf3fb; /* 通常の淡い青 */
        }
        @media (max-width: 600px) {
            .main-container { padding: 1rem 0.5rem; }
        }
    </style>
    <script>
    // オートコンプリート用に選手名リストをJSに渡す
    const playerNames = <?= json_encode($player_names, JSON_UNESCAPED_UNICODE) ?>;
    window.addEventListener('DOMContentLoaded', () => {
        const input = document.getElementById('player_name');
        input.addEventListener('input', function() {
            const list = document.getElementById('player_list');
            list.innerHTML = '';
            if (this.value.length === 0) return;
            playerNames.forEach(name => {
                if (name.includes(this.value)) {
                    const option = document.createElement('option');
                    option.value = name;
                    list.appendChild(option);
                }
            });
        });
    });
    </script>
</head>
<body>
    <div class="main-container shadow">
        <h1 class="mb-4 text-center">守備ハイライト</h1>
        <form method="post" class="mb-4">
            <div class="mb-3">
                <label class="form-label" for="date">日付</label>
                <input type="date" class="form-control" name="date" id="date" value="<?= htmlspecialchars($date) ?>">
            </div>
            <div class="mb-3">
                <label class="form-label" for="player_name">選手名</label>
                <input type="text" class="form-control" name="player_name" id="player_name" list="player_list" value="<?= htmlspecialchars($player_name) ?>" autocomplete="off">
                <datalist id="player_list"></datalist>
            </div>
            <button type="submit" class="btn btn-primary w-100">検索</button>
        </form>
        <?php if (!empty($result_lines)): ?>
            <h2 class="mb-3"><?= htmlspecialchars($player_name) ?>の<?= htmlspecialchars($date) ?>の守備</h2>
            <ul class="highlight-list list-unstyled">
                <?php foreach ($result_lines as $line): ?>
                    <li class="<?= $line['class'] ?>"><?= $line['text'] ?></li>
                <?php endforeach; ?>
            </ul>
        <?php endif; ?>
    </div>
    <!-- Bootstrap JS (optional, for some components) -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>