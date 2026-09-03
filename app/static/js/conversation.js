(() => {
  const log = document.getElementById("log");
  const mic = document.getElementById("mic");
  const form = document.getElementById("text-form");
  const input = document.getElementById("text-input");
  let sessionId = "";
  let scene = "cafe";
  let busy = false;

  function thinking() {
    const el = document.createElement("div");
    el.className = "bubble ai";
    el.innerHTML = `<span class="dots"><i></i><i></i><i></i></span> 正在思考…`;
    log.appendChild(el);
    log.scrollTop = log.scrollHeight;
    return el;
  }

  function addAi(text, ruby, zh, audioUrl) {
    const el = document.createElement("article");
    el.className = "bubble ai";
    el.innerHTML = `
      <p class="ja">${Hanashi.rubyHtml(ruby, text)}</p>
      ${zh ? `<p class="zh">${Hanashi.escapeHtml(zh)}</p>` : ""}
      ${audioUrl ? `<button class="play-mini" type="button">播放</button>` : ""}
    `;
    const btn = el.querySelector(".play-mini");
    if (btn) btn.onclick = () => Hanashi.play(audioUrl);
    log.appendChild(el);
    log.scrollTop = log.scrollHeight;
  }

  function addMe(transcript, correction, note) {
    const el = document.createElement("article");
    el.className = "bubble me";
    el.innerHTML = `
      <p class="meta">你说的</p>
      <p class="ja">${Hanashi.escapeHtml(transcript)}</p>
      ${
        correction
          ? `<div class="fix"><p class="meta">更自然的说法</p><p class="ja">${Hanashi.escapeHtml(correction)}</p>
             ${note ? `<p class="zh">${Hanashi.escapeHtml(note)}</p>` : ""}</div>`
          : ""
      }
    `;
    log.appendChild(el);
    log.scrollTop = log.scrollHeight;
  }

  async function start() {
    log.innerHTML = "";
    const wait = thinking();
    try {
      const data = await Hanashi.api("/api/conversation/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ scene }),
      });
      sessionId = data.session_id;
      wait.remove();
      addAi(data.opening_ja, data.opening_ruby, data.opening_zh, data.audio_url);
      if (data.audio_url) Hanashi.play(data.audio_url);
    } catch (err) {
      wait.remove();
      Hanashi.toast(err.message);
    }
  }

  async function send({ text, blob }) {
    if (busy) return;
    if (!sessionId) await start();
    busy = true;
    const wait = thinking();
    const body = new FormData();
    body.append("session_id", sessionId);
    if (text) body.append("text", text);
    if (blob) body.append("audio", blob, blob.type.includes("mp4") ? "speech.mp4" : "speech.webm");
    try {
      const data = await Hanashi.api("/api/conversation/turn", { method: "POST", body });
      wait.remove();
      addMe(data.learner_transcript, data.correction, data.correction_note_zh);
      addAi(data.reply_ja, data.reply_ja_ruby, data.reply_zh, data.audio_url);
      if (data.audio_url) Hanashi.play(data.audio_url);
    } catch (err) {
      wait.remove();
      Hanashi.toast(err.message);
    } finally {
      busy = false;
    }
  }

  document.getElementById("scenes").addEventListener("click", (ev) => {
    const btn = ev.target.closest("[data-scene]");
    if (!btn) return;
    document.querySelectorAll(".chip").forEach((c) => c.classList.remove("is-on"));
    btn.classList.add("is-on");
    scene = btn.dataset.scene;
    start();
  });

  document.getElementById("new-chat").onclick = () => {
    if (sessionId) {
      Hanashi.api("/api/conversation/reset", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId }),
      }).catch(() => {});
    }
    start();
  };

  form.addEventListener("submit", (ev) => {
    ev.preventDefault();
    const text = input.value.trim();
    if (!text) return;
    input.value = "";
    send({ text });
  });

  Hanashi.holdRecord(mic, {
    onStop(blob) {
      if (!blob || blob.size < 200) {
        Hanashi.toast("录音太短，请再试一次。");
        return;
      }
      send({ blob });
    },
  });

  start();
})();
