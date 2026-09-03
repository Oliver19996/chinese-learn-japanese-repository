# 日语会话 Hanashi

给中文母语者用的日语口语练习应用：会话、查词、跟读、听写。手机浏览器打开即可。

中国人向けの日本語会話アプリです。日常会話・単語検索・シャドーイング・ディクテーションを、スマホのブラウザで使えます。

## 启动 / 起動

在项目文件夹 `chinese-learn-japanese` 下执行（VS Code 的终端也一样）：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python scripts/seed.py
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python scripts\seed.py
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

浏览器打开 [http://127.0.0.1:8000](http://127.0.0.1:8000)。

VS Code：选择解释器 `.venv/bin/python`，然后用「运行和调试」里的 **Hanashi**。

## API 密钥（稍后填写）

没有 ChatGPT / OpenAI 密钥也能打开全部画面。真实语音识别、对话、朗读需要密钥。

编辑 `.env`：

```
OPENAI_API_KEY=sk-你的密钥
OPENAI_BASE_URL=https://api.openai.com/v1
```

如果使用代理或 Azure 兼容地址，只改 `OPENAI_BASE_URL`。不要把 `.env` 提交到 GitHub。

## 用手机打开

电脑和手机连同一个 Wi-Fi。电脑终端执行 `ifconfig`（macOS）或 `ipconfig`（Windows）查看局域网 IP，例如 `192.168.1.12`。

手机浏览器打开：`http://192.168.1.12:8000`

- 麦克风需要 **localhost 或 HTTPS**。iPhone 用 HTTP 局域网地址时，录音可能失败。这时请用键盘输入练习会话。
- 需要麦克风时，可用 [ngrok](https://ngrok.com/) 或 Cloudflare Tunnel 把本地服务暴露为 HTTPS。

## 功能

- **会话**：按住说话，或输入日语。AI 用短句日语回答，并给出中文和假名。
- **查词**：输入日语或中文。先查内置约 300 词，没有再问 AI。
- **跟读**：听示范 → 按住模仿 → 听自己的声音 → 对照打分。
- **听写**：最多听两次后写下日语，看对错和分数。

## GitHub 与部署

```bash
git init
git add .
git commit -m "日语会话应用的初始版本"
git remote add origin https://github.com/你的用户名/chinese-learn-japanese.git
git push -u origin main
```

部署到 Render / Railway / Fly.io 时：

- 启动命令：`uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- 环境变量设置 `OPENAI_API_KEY` 和可选的 `OPENAI_BASE_URL`
- 也可用仓库里的 `Dockerfile`

不要部署 `.venv` 和 `.env`。
