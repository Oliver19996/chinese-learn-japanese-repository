import os
from datetime import date

import streamlit as st


def load_secrets() -> None:
    try:
        secrets = st.secrets
    except Exception:
        return
    for key in (
        "OPENAI_API_KEY",
        "OPENAI_BASE_URL",
        "OPENAI_CHAT_MODEL",
        "OPENAI_STT_MODEL",
        "OPENAI_TTS_MODEL",
        "OPENAI_TTS_VOICE",
        "DATABASE_URL",
    ):
        if key in secrets and secrets[key]:
            os.environ[key] = str(secrets[key])


load_secrets()

from app.services.dictionary import lookup
from app.services.lessons import dictation_lessons, shadowing_lessons
from app.services.llm import SCENES, opening_for, reply_conversation
from app.services.scoring import best_score

st.set_page_config(page_title="Hanashi", page_icon="🇯🇵", layout="wide")

TODAY_PHRASES = [
    ("今日もがんばりましょう。", "きょうもがんばりましょう。", "今天也加油吧。"),
    ("駅はどこですか。", "えきはどこですか。", "车站在哪里？"),
    ("また会いましょう。", "またあいましょう。", "下次再见。"),
]


def render_home() -> None:
    phrase = TODAY_PHRASES[date.today().toordinal() % len(TODAY_PHRASES)]
    st.title("Hanashi")
    st.caption("中国語母語話者のための日本語練習")
    st.subheader("今日の一言")
    st.markdown(f"## {phrase[0]}")
    st.write(f"{phrase[1]}  ·  {phrase[2]}")
    st.info("左のメニューから会話、辞書、シャドーイング、ディクテーションを選べます。")


def render_dictionary() -> None:
    st.title("辞書")
    query = st.text_input("日本語または中国語を入力", key="dictionary_query")
    if not query:
        return
    results = lookup(query)
    if not results:
        st.warning("見つかりませんでした。")
        return
    for item in results:
        with st.container(border=True):
            st.subheader(item.ja or query)
            st.write(f"{item.reading} · {item.pos} · {item.zh}")
            for example in item.examples:
                st.write(f"{example.ja}（{example.reading}）")
                st.caption(example.zh)


def render_conversation() -> None:
    st.title("会話練習")
    scene = st.selectbox("場面", list(SCENES), format_func=lambda key: SCENES[key])
    if st.button("会話をリセット", type="secondary") or "conversation_scene" not in st.session_state:
        st.session_state.conversation_scene = scene
        st.session_state.conversation_history = []
        opening = opening_for(scene)
        st.session_state.conversation_messages = [("先生", opening.reply_ja, opening.reply_zh)]
    elif st.session_state.conversation_scene != scene:
        st.session_state.conversation_scene = scene
        st.session_state.conversation_history = []
        opening = opening_for(scene)
        st.session_state.conversation_messages = [("先生", opening.reply_ja, opening.reply_zh)]

    for speaker, japanese, chinese in st.session_state.get("conversation_messages", []):
        st.markdown(f"**{speaker}**  {japanese}")
        st.caption(chinese)

    with st.form("conversation_form", clear_on_submit=True):
        text = st.text_input("日本語で返答")
        submitted = st.form_submit_button("送信", type="primary")
    if submitted and text.strip():
        history = st.session_state.conversation_history
        result = reply_conversation(scene, text.strip(), history)
        history.extend([
            {"role": "user", "content": text.strip()},
            {"role": "assistant", "content": result.reply_ja},
        ])
        st.session_state.conversation_messages.extend([
            ("あなた", result.learner_transcript or text.strip(), ""),
            ("先生", result.reply_ja, result.reply_zh),
        ])
        st.rerun()


def render_lessons() -> None:
    st.title("レッスン")
    tab_shadowing, tab_dictation = st.tabs(["シャドーイング", "ディクテーション"])
    with tab_shadowing:
        for lesson in shadowing_lessons():
            with st.expander(f"{lesson['title_zh']} · {lesson.get('title_ja', '')}"):
                for item in lesson.get("items", []):
                    st.write(f"{item['ja']} 　{item.get('reading', '')} 　{item.get('zh', '')}")
    with tab_dictation:
        lessons = dictation_lessons()
        lesson = st.selectbox("教材", lessons, format_func=lambda value: value["title_zh"])
        item = st.selectbox("問題", lesson["items"], format_func=lambda value: value["id"])
        answer = st.text_input("聞こえた日本語")
        if st.button("採点") and answer.strip():
            score = best_score(answer, item["ja"], item.get("reading", ""))
            st.metric("スコア", f"{score}点")
            st.write(f"正解: {item['ja']}（{item.get('reading', '')}）")
            st.caption(item.get("zh", ""))


page = st.sidebar.radio("メニュー", ["ホーム", "会話", "辞書", "レッスン"])
if page == "ホーム":
    render_home()
elif page == "会話":
    render_conversation()
elif page == "辞書":
    render_dictionary()
else:
    render_lessons()