(() => {
  const root = document.getElementById("play");
  if (!root) return;
  const lessonId = root.dataset.lesson;
  const items = JSON.parse(root.dataset.items);
  let index = 0;
  let plays = 0;

  const progress = document.getElementById("progress");
  const listen = document.getElementById("listen");
  const form = document.getElementById("form");
  const answer = document.getElementById("answer");
  const result = document.getElementById("result");
  const next = document.getElementById("next");

  function resetItem() {
    const item = items[index];
    progress.textContent = `${index + 1} / ${items.length}`;
    plays = 0;
    listen.textContent = "播放";
    answer.value = "";
    result.hidden = true;
    next.hidden = true;
    form.hidden = false;
    listen.dataset.item = item.id;
  }

  listen.onclick = async () => {
    const item = items[index];
    plays += 1;
    listen.textContent = plays >= 2 ? "再听" : "播放";
    try {
      const data = await Hanashi.api("/api/dictation/tts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ lesson_id: lessonId, item_id: item.id }),
      });
      Hanashi.play(data.audio_url);
    } catch (err) {
      Hanashi.toast(err.message);
    }
  };

  form.addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const item = items[index];
    try {
      const data = await Hanashi.api("/api/dictation/grade", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ lesson_id: lessonId, item_id: item.id, answer: answer.value }),
      });
      const diff = (data.diff || [])
        .map((t) => `<span class="${t.kind}">${Hanashi.escapeHtml(t.t)}</span>`)
        .join("");
      result.hidden = false;
      result.innerHTML = `
        <p class="card-kicker">${data.score} 分</p>
        <p class="diff">${diff}</p>
        <p class="ja">${Hanashi.escapeHtml(data.correct_ja)}</p>
        <p class="reading">${Hanashi.escapeHtml(data.correct_reading || "")}</p>
        <p class="zh">${Hanashi.escapeHtml(data.correct_zh || "")}</p>
      `;
      next.hidden = false;
      next.textContent = index >= items.length - 1 ? "完成" : "下一题";
    } catch (err) {
      Hanashi.toast(err.message);
    }
  });

  next.onclick = () => {
    if (index >= items.length - 1) {
      result.hidden = false;
      result.innerHTML = `<p class="ja">完成！</p><p class="zh">听写结束，回课程列表再练一组吧。</p>`;
      next.hidden = true;
      form.hidden = true;
      return;
    }
    index += 1;
    resetItem();
  };

  resetItem();
})();
