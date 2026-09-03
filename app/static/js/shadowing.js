(() => {
  const root = document.getElementById("play");
  if (!root) return;
  const lessonId = root.dataset.lesson;
  const items = JSON.parse(root.dataset.items);
  let index = 0;
  let rate = 1;
  let modelUrl = "";
  let myBlobUrl = "";
  let myBlob = null;

  const ja = document.getElementById("ja");
  const reading = document.getElementById("reading");
  const zh = document.getElementById("zh");
  const progress = document.getElementById("progress");
  const scoreEl = document.getElementById("score");

  function show() {
    const item = items[index];
    ja.textContent = item.ja;
    reading.textContent = item.reading || "";
    zh.textContent = item.zh || "";
    progress.textContent = `${index + 1} / ${items.length}`;
    scoreEl.hidden = true;
    myBlob = null;
    if (myBlobUrl) URL.revokeObjectURL(myBlobUrl);
    myBlobUrl = "";
    modelUrl = "";
  }

  async function ensureModel() {
    const item = items[index];
    const data = await Hanashi.api("/api/shadowing/tts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ lesson_id: lessonId, item_id: item.id }),
    });
    modelUrl = data.audio_url;
    return modelUrl;
  }

  document.getElementById("play-model").onclick = async () => {
    try {
      const url = await ensureModel();
      const audio = new Audio(url);
      audio.playbackRate = rate;
      audio.play();
    } catch (err) {
      Hanashi.toast(err.message);
    }
  };

  document.getElementById("speeds").addEventListener("click", (ev) => {
    const btn = ev.target.closest("[data-rate]");
    if (!btn) return;
    document.querySelectorAll("#speeds button").forEach((b) => b.classList.remove("is-on"));
    btn.classList.add("is-on");
    rate = Number(btn.dataset.rate);
  });

  Hanashi.holdRecord(document.getElementById("record"), {
    onStop(blob) {
      if (!blob || blob.size < 200) {
        Hanashi.toast("录音太短，请再试一次。");
        return;
      }
      myBlob = blob;
      if (myBlobUrl) URL.revokeObjectURL(myBlobUrl);
      myBlobUrl = URL.createObjectURL(blob);
      grade(blob);
    },
  });

  document.getElementById("play-me").onclick = () => {
    if (!myBlobUrl) {
      Hanashi.toast("请先按住跟读。");
      return;
    }
    new Audio(myBlobUrl).play();
  };

  document.getElementById("compare").onclick = async () => {
    try {
      const url = await ensureModel();
      const a = new Audio(url);
      a.playbackRate = rate;
      a.onended = () => {
        if (myBlobUrl) new Audio(myBlobUrl).play();
      };
      a.play();
    } catch (err) {
      Hanashi.toast(err.message);
    }
  };

  async function grade(blob) {
    const item = items[index];
    const body = new FormData();
    body.append("lesson_id", lessonId);
    body.append("item_id", item.id);
    body.append("audio", blob, "speech.webm");
    try {
      const data = await Hanashi.api("/api/shadowing/score", { method: "POST", body });
      scoreEl.hidden = false;
      scoreEl.textContent = `${data.score} 分 · ${data.comment_zh}`;
    } catch (err) {
      Hanashi.toast(err.message);
    }
  }

  document.getElementById("prev").onclick = () => {
    index = Math.max(0, index - 1);
    show();
  };
  document.getElementById("next").onclick = () => {
    if (index >= items.length - 1) {
      scoreEl.hidden = false;
      scoreEl.textContent = "完成！说得很认真，继续保持。";
      return;
    }
    index += 1;
    show();
  };

  show();
})();
