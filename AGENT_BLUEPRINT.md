# 実装プロンプト：中国人向け AI 日本語会話アプリ（Hanashi / 日语会话）

以下を **唯一の仕様書** として読め。質問で止めず、この文書の決定事項に従って **動作するモバイルWebアプリを最初から実装** せよ。曖昧な点は本文の「デフォルト決定」を採用する。

---

## 0. ミッション

中国語を母語とする学習者が、スマートフォンのブラウザだけで日本語を練習できるアプリを作る。

必須機能は次の4つだけ：

1. **日常会話** … 音声の送受信（話す → AIが日本語で返す → 音声で聞く）
2. **単語検索** … わからない語を調べる（読み・中国語訳・例文）
3. **シャドーイング** … お手本音声を聞いて直後に真似して録音・比較
4. **ディクテーション** … 音声を聞いて書き取る

言語スタックは **Python バックエンド必須**。スマホで開くこと。App Store / Google Play のネイティブアプリは作らない。

---

## 1. プロダクト決定（変更禁止）

| 項目 | 決定 |
|---|---|
| アプリ名（表示） | 日语会话 Hanashi |
| UI言語 | 簡体字中国語 |
| 学習対象言語 | 日本語 |
| 形態 | モバイルファースト PWA（ホーム画面追加可） |
| 対象画面幅 | 390px を基準。デスクトップは中央カラム（最大 480px） |
| 認証 | v1 はログインなし。`localStorage` の `device_id` で進捗を紐付け |
| レベル | 初級〜中級（N5〜N3 想定）。会話は優しく、短文 |
| 課金・SNS・多言語切替 | 作らない |
| 管理画面 | 作らない |

### 学習者向けトーン

- AI会話相手は「優しい日本人の友人」。丁寧語（です・ます）を基本にする。
- 学習者の発話が崩れても否定せず、自然な日本語に直してから会話を続ける。
- 画面上では **日本語本文 + ふりがな + 簡体字訳** をセットで出す。
- 中国人学習者がつまずきやすい助詞（は/が、に/で、を）やテ形は、必要なら一言だけ中国語で補足する。くどく説明しない。

---

## 2. 技術スタック（変更禁止）

```
バックエンド     FastAPI + Uvicorn + Pydantic v2
テンプレート     Jinja2
フロント         バニラ HTML / CSS / JS（フレームワーク禁止）
永続化           SQLite + SQLAlchemy 2.x
音声認識 (STT)   OpenAI Audio Transcriptions（whisper-1）
音声合成 (TTS)   OpenAI Audio Speech（tts-1 / voice=nova）
会話・解説 LLM   OpenAI Chat Completions（gpt-4o-mini）
設定             pydantic-settings + .env
パッケージ管理   requirements.txt
Python           3.11+
```

禁止：

- Streamlit / Gradio / Django / React / Vue / Next.js / React Native / Flutter / Kivy
- ユーザー登録、OAuth、メール
- Docker 以外の複雑なインフラ。まずはローカル起動で完結
- 外部辞書APIへの依存（オフライン辞書ファイルも必須にしない）。単語検索は LLM + アプリ内シード語彙

必須環境変数（`.env.example` を置く）：

```
OPENAI_API_KEY=
OPENAI_CHAT_MODEL=gpt-4o-mini
OPENAI_STT_MODEL=whisper-1
OPENAI_TTS_MODEL=tts-1
OPENAI_TTS_VOICE=nova
APP_SECRET=dev-secret-change-me
DATABASE_URL=sqlite:///./data/hanashi.db
```

APIキーが無い場合でも **UIとモック音声（静的サンプルwav）で画面遷移できる** こと。キーがあるときだけ実音声・実LLMを使う。`OPENAI_API_KEY` 未設定なら各サービスは明確なフォールバックを返す。

---

## 3. ディレクトリ構成（この通りに作る）

```
chinese-learn-japanese/
├── AGENT_BLUEPRINT.md          # 本ファイル（消さない）
├── README.md                   # 起動方法・スマホからの開き方
├── requirements.txt
├── .env.example
├── .gitignore
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI, 静的ファイル, ルート
│   ├── config.py
│   ├── db.py
│   ├── models.py
│   ├── schemas.py
│   ├── routers/
│   │   ├── pages.py            # HTML ページ
│   │   ├── conversation.py
│   │   ├── dictionary.py
│   │   ├── shadowing.py
│   │   └── dictation.py
│   ├── services/
│   │   ├── openai_client.py
│   │   ├── stt.py
│   │   ├── tts.py
│   │   ├── llm.py
│   │   ├── dictionary.py
│   │   └── scoring.py
│   ├── data/
│   │   ├── seed_words.json     # 300語程度の初級語彙
│   │   ├── shadowing_lessons.json
│   │   └── dictation_lessons.json
│   ├── templates/
│   │   ├── base.html
│   │   ├── home.html
│   │   ├── conversation.html
│   │   ├── dictionary.html
│   │   ├── shadowing.html
│   │   ├── shadowing_play.html
│   │   ├── dictation.html
│   │   └── dictation_play.html
│   └── static/
│       ├── manifest.json
│       ├── sw.js
│       ├── css/app.css
│       ├── js/app.js           # 共通（録音、再生、トースト、device_id）
│       ├── js/conversation.js
│       ├── js/dictionary.js
│       ├── js/shadowing.js
│       ├── js/dictation.js
│       ├── icons/icon-192.png
│       ├── icons/icon-512.png
│       └── audio/placeholder.wav
├── data/                       # SQLite と生成音声の保存先（git無視）
└── scripts/
    └── seed.py                 # 任意。起動時にJSONを読めば十分
```

生成した TTS 音声は `data/audio/` に保存し、`/media/audio/{filename}` で配信する。ファイル名は UUID。古いファイル掃除は不要（v1）。

---

## 4. UX / 画面設計

### 共通 UI

- 背景：暖色のオフホワイト `#FFF8F1`
- メイン：朱に近い赤 `#C23A2B`（日本らしいが派手すぎない）
- サブ：深い紺 `#1F2A44`
- 本文：`#2B2B2B`
- フォント：システムフォント。日本語は `Hiragino Sans`, `Noto Sans JP`, `PingFang SC` の順
- 下部固定タブバー（4つ + ホームでも可。実体は4機能 + ホーム）：

```
首页 | 会话 | 查词 | 跟读 | 听写
```

- 各タブにアイコン（インラインSVG）と中国語ラベル
- タッチターゲットは最小 44px
- ふりがなは `<ruby>日本語<rt>にほんご</rt></ruby>`
- 読み込み中はスケルトンではなく、小さな点滅ドット + 「正在思考…」等
- エラーは画面下部トースト。英語の例外メッセージを出さない。中国語で短く

### 4.1 首页 `/`

- アプリ名と一文：「用声音学会日常日语」
- 今日の一言（サーバーが固定シードから日付で選ぶ。API不要でも可）
- 4機能の大きなカード
- 下部に学習メモ：今日の会話ターン数・シャドーイング完了数・ディクテーション正答数（device_id 集計）

### 4.2 会话 `/conversation`

日常会話。音声の受け渡しが主。

レイアウト（上から）：

1. 場面セレクタ（横スクロールチップ）
   - 咖啡店 / 车站 / 便利店 / 餐厅 / 初次见面 / 购物 / 问路 / 自由聊天
2. 会話ログ（自分は右、AIは左）
   - 各バブル：日本語（ふりがな付き） / 简体中文訳 / 再生ボタン
   - 学習者側は「你说的」原文 + 必要なら「更自然的说法」訂正
3. 下部固定操作
   - 大きなマイクボタン（押し話し：押している間録音、離して送信）
   - 補助：キーボード入力（テキストでも同じAPIに送れる）
   - 「新对话」でリセット

会話1ターンのサーバー処理：

```
音声 or テキスト
  → STT（音声なら。言語ヒント ja）
  → LLM
  → TTS（AIの日本語返答のみ）
  → JSON + 音声URL
```

LLM は **必ず JSON** で返す（コードフェンス禁止）：

```json
{
  "learner_transcript": "学習者の発話（整形後の日本語）",
  "correction": null,
  "correction_note_zh": null,
  "reply_ja": "AIの日本語返答。1〜2文。ですます。",
  "reply_ja_ruby": [
    {"s": "今日", "r": "きょう"},
    {"s": "は", "r": ""},
    {"s": "空", "r": "そら"},
    {"s": "が", "r": ""},
    {"s": "きれい", "r": ""},
    {"s": "です", "r": ""},
    {"s": "ね。", "r": ""}
  ],
  "reply_zh": "今天天气真好啊。",
  "new_words": [
    {"ja": "空", "reading": "そら", "zh": "天空"}
  ]
}
```

`correction` は、学習者の日本語が不自然なときだけ正しい文を入れる。問題なければ `null`。

システムプロンプト要点：

- あなたは日本語の会話相手兼コーチ
- 学習者は中国語母語。返答の日本語は短く、N4前後
- 場面設定を守る
- 中国語で会話を続けない。日本語で返し、中国語は訳欄だけ
- JSON以外を出力しない

履歴：直近 12 ターンをサーバーが DB に持ち、LLM に渡す。それ以上は捨ててよい。

マイク：

- `MediaRecorder` + `getUserMedia`
- iOS Safari を最優先で確認すること。`audio/webm` が駄目なら `audio/mp4` または `audio/wav`
- HTTPS または localhost のみマイク可、と README に書く
- 録音中はボタンを赤くパルス。再生中は波形風のCSSアニメで十分（実波形解析は不要）

### 4.3 查词 `/dictionary`

- 検索欄プレースホルダ：「输入日语或中文，如 食べる / 吃饭」
- 入力確定または虫眼鏡で検索
- 結果カード：
  - 見出し語 + ふりがな
  - 品词（中国語：动词 / 名词…）
  - 中文意思
  - 例文 1〜2（日本語ふりがな + 中文）
  - 「加入会话」は作らない。代わりに「朗读」ボタン（TTS）
- まず `seed_words.json` を部分一致検索
- ヒットが弱い、またはユーザー入力がシード外なら LLM で1語解説（同じJSONスキーマ）
- 最近検索（最大 20、device_id、DB）

シード語彙は N5〜N4 中心に約 300 語。動詞は辞書形。各エントリ：

```json
{
  "ja": "食べる",
  "reading": "たべる",
  "pos": "动词",
  "zh": "吃",
  "examples": [
    {"ja": "パンを食べます。", "reading": "パンをたべます。", "zh": "我吃面包。"}
  ]
}
```

### 4.4 跟读（シャドーイング） `/shadowing`

レッスン一覧 → 再生画面。

レッスンは JSON で 8 本。各 6〜10 文。場面は会話機能と揃える。例：

- 咖啡店点单
- 车站买票
- 便利店结账
- 餐厅点菜
- 初次见面
- 购物试穿
- 问路
- 预约医院

各文：

```json
{
  "id": "cafe-03",
  "ja": "ホットコーヒーを一つお願いします。",
  "ruby": "... または reading 文字列",
  "zh": "请给我一杯热咖啡。",
  "reading": "ホットコーヒーをひとつおねがいします。"
}
```

再生画面：

1. お手本を再生（初回アクセス時に TTS 生成してキャッシュ）
2. 速度：0.7 / 1.0 / 1.2
3. 「跟读」＝押している間録音
4. 「你的声音」再生
5. 「对照」：お手本と自分の録音を連続再生
6. 簡易スコア：自分の録音を STT し、お手本の `ja` または `reading` と recitation 類似度（下記）
7. 文の前後ナビ、進捗「3/8」
8. 全部終わったら「完成」と中国語の短い励まし

スコアは厳密な発音評価器を自作しない。`scoring.py` で：

- ひらがな化（簡易：reading フィールドを使う）
- 空白・句読点除去
- 文字単位の類似度（SequenceMatcher）
- 0〜100 点と「很好 / 再试一次 / 注意助词」程度の中国語コメント

### 4.5 听写（ディクテーション） `/dictation`

レッスン一覧 → プレイ画面。シャドーイングと別JSON。文は少し短め。6本 × 各8問。

プレイ：

1. 再生ボタン（デフォルトは2回まで。3回目からボタンは出すが「再听」と表示）
2. 入力欄：日本語（IME想定）。プレースホルダ「写下你听到的日语」
3. 「提交」
4. 結果：
   - 正解文（ふりがな + 中文）
   - 学習者入力との差分（正しい文字は緑、誤りは赤、抜けは下線）
   - 点数
5. 次の問題へ

採点：`scoring.py` の同じ正規化 + 文字一致率。漢字/かなの表記ゆれは、可能なら reading 同士でも比較し、高い方を採用。

---

## 5. API 仕様

HTMLページは `routers/pages.py`。API は `/api/...`。すべて JSON。エラーは：

```json
{"error": "麦克风音频无法识别，请再试一次。"}
```

### ページ

- `GET /` 首页
- `GET /conversation`
- `GET /dictionary`
- `GET /shadowing`
- `GET /shadowing/{lesson_id}`
- `GET /dictation`
- `GET /dictation/{lesson_id}`
- `GET /manifest.json`, `GET /sw.js`
- `GET /media/audio/{filename}`

### API

`X-Device-Id` ヘッダ必須（フロントが生成して付ける）。

```
POST /api/conversation/start
  body: { "scene": "cafe" }
  → { "session_id": "...", "opening_ja": "...", "opening_ruby": [...], "opening_zh": "...", "audio_url": "..." }

POST /api/conversation/turn
  multipart: session_id, audio? , text?
  → 上記 LLM JSON + audio_url + session_id

POST /api/conversation/reset
  body: { "session_id": "..." }

GET  /api/dictionary?q=
  → { "items": [ ... ] }

POST /api/dictionary/speak
  body: { "text": "食べる" }
  → { "audio_url": "..." }

GET  /api/shadowing/lessons
GET  /api/shadowing/lessons/{id}
POST /api/shadowing/tts          body: { "lesson_id", "item_id" } → { audio_url }
POST /api/shadowing/score        multipart: lesson_id, item_id, audio
  → { "score": 86, "heard": "...", "comment_zh": "..." }

GET  /api/dictation/lessons
GET  /api/dictation/lessons/{id}
POST /api/dictation/tts
POST /api/dictation/grade        body: { lesson_id, item_id, answer }
  → { "score": 70, "correct_ja": "...", "diff": [...], "correct_zh": "..." }

GET  /api/stats
  → { "conversation_turns": 0, "shadowing_done": 0, "dictation_correct": 0 }
```

DB モデル（最低限）：

- `Device` (id, created_at)
- `ConversationSession` (id, device_id, scene, created_at)
- `ConversationTurn` (id, session_id, role, text_ja, text_zh, correction, audio_path, created_at)
- `SearchHistory` (id, device_id, query, created_at)
- `ActivityEvent` (id, device_id, kind, payload_json, created_at)

---

## 6. 実装手順（この順でコミット可能な単位で進める）

実装は次の順。途中で別機能に脱線しない。

1. プロジェクト骨格：FastAPI、静的配信、baseレイアウト、タブバー、PWA manifest、空ページ
2. `seed_*.json` と CSS（モバイルUIを先に美しくする）
3. 查词（シード検索 → LLMフォールバック → TTS）
4. 会话（テキスト入力だけで LLM+TTS を通す）
5. 会话の録音送信（STT）。iOS/Android を意識した MIME 処理
6. 跟读（レッスン、TTSキャッシュ、録音、スコア）
7. 听写（再生回数制限、差分表示、採点）
8. 首页統計、README、`.env.example`、起動確認

各ステップが終わったら、その機能がスマホ幅で使える状態にする。APIだけ作って画面がない状態で次に進まない。

---

## 7. 見た目の品質基準

これは学習アプリであり、管理画面やダッシュボードではない。

- 余白を十分に。カードは丸角 16px、薄い影
- 会話バブルはチャットアプリのように見える
- マイクボタンは画面中央下に大きく、片手で押せる
- 装飾のためのイラスト生成や巨大ヒーロー画像は不要。シンプルな和風モチーフ（小さな丸、細い線）で十分
- ダークモードは作らない
- アニメは CSS のみ。ライブラリ追加禁止（ソート・日付・UUID も標準ライブラリ）

フロントの依存は **ゼロ**。CDN で Vue/React/jQuery を引かない。

バックエンド追加してよいライブラリ：

```
fastapi
uvicorn[standard]
jinja2
python-multipart
sqlalchemy
pydantic
pydantic-settings
httpx
python-dotenv
aiofiles
```

これ以外は必要性が明確なときだけ。音声変換にどうしても必要なら `pydub` は可。ただし ffmpeg 必須になるので、まずはそのまま OpenAI に webm/mp4 を送る。

---

## 8. README に必ず書くこと

簡体字中国語 + 日本語の両方で短く：

- 何のアプリか
- `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
- `.env` の作り方
- `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
- 同じWi-Fiのスマホから `http://<PCのLAN IP>:8000` で開く方法
- マイクは localhost か HTTPS が必要なこと（iOS は HTTP の LAN IP でマイクが失敗しうる。その場合はテキスト入力で会話できること、ngrok / Cloudflare Tunnel の一言）
- OpenAI キーなしでも UI 確認できること

---

## 9. 受け入れ条件（すべて満たせ）

- 390x844 相当の幅で、横スクロールが本文に出ない（チップ列だけ例外）
- タブ4機能 + 首页が実在し、相互に遷移できる
- 会話：テキスト入力で AI 返答（日本語・中文・ふりがな・音声）が返る
- 会話：録音ボタンで音声送信できる（対応ブラウザ）
- 查词：シード語（食べる、電車 など）が即ヒット。未知語は LLM または丁寧な「暂无」
- 跟读：お手本再生、録音、自分の声の再生、点数表示
- 听写：音声再生、入力、差分と点数
- APIキー欠如時に 500 のスタックトレースHTMLを出さない
- `README.md` だけで第三者が起動できる

---

## 10. 明示的にやらないこと

- ユーザーアカウント、ランキング、連続学習日の通知
- 漢字書き問題、文法ドリル、SRS（Anki的な復習間隔）
- 教師用ダッシュボード
- リアルタイム割り込み音声（全二重）。ターン制でよい
- 方言、関西弁モード
- テストコードは必須ではない。作るなら `tests/test_scoring.py` だけ

---

## 11. 実装者への最後の指示

今すぐコードを書き始めよ。設計の再提案や別スタックの議論は不要。

最初の成果物は、タブが動くモバイルUIと空の4画面である。そこから機能を埋める。

コミットメッセージは日本語で、なぜかを1文で書く。ユーザーがコミットを依頼するまで、git commit はしなくてよい（ローカル実装のみ）。

作業完了時は、起動コマンドと、各機能の使い方を簡体字中国語で短く報告する。
