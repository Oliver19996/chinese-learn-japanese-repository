(() => {
  const form = document.getElementById("search-form");
  const input = document.getElementById("q");
  const results = document.getElementById("results");
  const status = document.getElementById("status");

  function card(item) {
    const examples = (item.examples || [])
      .map(
        (ex) => `<div class="ex"><p class="ja">${Hanashi.escapeHtml(ex.ja)}</p>
        <p class="reading">${Hanashi.escapeHtml(ex.reading || "")}</p>
        <p class="zh">${Hanashi.escapeHtml(ex.zh || "")}</p></div>`
      )
      .join("");
    return `<article class="card word-card">
      <h2><ruby>${Hanashi.escapeHtml(item.ja)}<rt>${Hanashi.escapeHtml(item.reading || "")}</rt></ruby></h2>
      <span class="pos">${Hanashi.escapeHtml(item.pos || "")}</span>
      <p class="zh">${Hanashi.escapeHtml(item.zh || "")}</p>
      ${examples}
      <button class="btn ghost" type="button" data-speak="${Hanashi.escapeHtml(item.ja)}">朗读</button>
    </article>`;
  }

  async function search(q) {
    status.innerHTML = `<span class="dots"><i></i><i></i><i></i></span> 正在查找…`;
    results.innerHTML = "";
    try {
      const data = await Hanashi.api("/api/dictionary?q=" + encodeURIComponent(q));
      if (!data.items.length) {
        status.textContent = "暂无该词，请换个说法试试。";
        return;
      }
      status.textContent = `找到 ${data.items.length} 条`;
      results.innerHTML = data.items.map(card).join("");
    } catch (err) {
      status.textContent = "";
      Hanashi.toast(err.message);
    }
  }

  form.addEventListener("submit", (ev) => {
    ev.preventDefault();
    const q = input.value.trim();
    if (!q) return;
    search(q);
  });

  results.addEventListener("click", async (ev) => {
    const btn = ev.target.closest("[data-speak]");
    if (!btn) return;
    try {
      const data = await Hanashi.api("/api/dictionary/speak", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: btn.dataset.speak }),
      });
      Hanashi.play(data.audio_url);
    } catch (err) {
      Hanashi.toast(err.message);
    }
  });
})();
