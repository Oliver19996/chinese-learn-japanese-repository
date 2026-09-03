const Hanashi = (() => {
  const KEY = "hanashi_device_id";

  function uuid() {
    if (crypto.randomUUID) return crypto.randomUUID();
    return "xxxxxxxxyxxx".replace(/[xy]/g, (c) => {
      const r = (Math.random() * 16) | 0;
      return (c === "x" ? r : (r & 0x3) | 0x8).toString(16);
    });
  }

  function deviceId() {
    let id = localStorage.getItem(KEY);
    if (!id) {
      id = uuid();
      localStorage.setItem(KEY, id);
    }
    return id;
  }

  function toast(message) {
    const el = document.getElementById("toast");
    if (!el) return;
    el.hidden = false;
    el.textContent = message;
    clearTimeout(toast._t);
    toast._t = setTimeout(() => {
      el.hidden = true;
    }, 2600);
  }

  async function api(url, options = {}) {
    const headers = Object.assign({ "X-Device-Id": deviceId() }, options.headers || {});
    const res = await fetch(url, Object.assign({}, options, { headers }));
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || "出了点问题，请稍后再试。");
    return data;
  }

  function rubyHtml(tokens, fallback) {
    if (!tokens || !tokens.length) return escapeHtml(fallback || "");
    return tokens
      .map((t) => {
        const s = escapeHtml(t.s || "");
        const r = escapeHtml(t.r || "");
        return r ? `<ruby>${s}<rt>${r}</rt></ruby>` : s;
      })
      .join("");
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function pickMime() {
    const types = ["audio/mp4", "audio/webm;codecs=opus", "audio/webm", "audio/wav"];
    if (!window.MediaRecorder) return "";
    for (const t of types) {
      if (MediaRecorder.isTypeSupported(t)) return t;
    }
    return "";
  }

  function holdRecord(button, { onStart, onStop }) {
    let recorder = null;
    let chunks = [];
    let stream = null;
    let recording = false;

    async function start(ev) {
      ev.preventDefault();
      if (recording) return;
      try {
        button.setPointerCapture(ev.pointerId);
      } catch {}
      try {
        stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      } catch {
        toast("无法使用麦克风。请允许权限，或改用键盘输入。");
        return;
      }
      const mime = pickMime();
      chunks = [];
      recorder = mime ? new MediaRecorder(stream, { mimeType: mime }) : new MediaRecorder(stream);
      recorder.ondataavailable = (e) => {
        if (e.data && e.data.size) chunks.push(e.data);
      };
      recorder.start();
      recording = true;
      button.classList.add("is-rec");
      if (onStart) onStart();
    }

    async function stop(ev) {
      if (ev) ev.preventDefault();
      if (!recording || !recorder) return;
      recording = false;
      button.classList.remove("is-rec");
      await new Promise((resolve) => {
        recorder.onstop = resolve;
        try {
          recorder.stop();
        } catch {
          resolve();
        }
      });
      (stream.getTracks() || []).forEach((t) => t.stop());
      const type = recorder.mimeType || "audio/webm";
      const blob = new Blob(chunks, { type });
      recorder = null;
      stream = null;
      if (onStop) onStop(blob);
    }

    button.addEventListener("pointerdown", start);
    button.addEventListener("pointerup", stop);
    button.addEventListener("pointercancel", stop);
    button.addEventListener("lostpointercapture", stop);
  }

  function play(url, rate = 1) {
    const audio = new Audio(url);
    audio.playbackRate = rate;
    return audio.play().then(() => audio).catch(() => {
      toast("无法播放音频。");
      return audio;
    });
  }

  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("/sw.js").catch(() => {});
  }

  return { deviceId, toast, api, rubyHtml, escapeHtml, holdRecord, play };
})();
