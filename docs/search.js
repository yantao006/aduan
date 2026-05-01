(function () {
  let index = null;
  const input = document.getElementById("global-search");
  const results = document.getElementById("search-results");
  if (!input || !results) return;

  function esc(value) {
    return String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  function loadIndex() {
    if (index) return Promise.resolve(index);
    var BASE = document.querySelector('script[src$="search.js"]').src.replace(/search\.js$/, '');
    return fetch(BASE + "search-index.json")
      .then((response) => response.json())
      .then((data) => {
        index = data;
        return index;
      });
  }

  function close() {
    results.classList.remove("open");
    results.innerHTML = "";
  }

  function scoreItem(item, terms, rawQuery) {
    const title = String(item.t || "").toLowerCase();
    const body = String(item.b || "").toLowerCase();
    let score = 0;
    for (const term of terms) {
      if (!term) continue;
      if (title === rawQuery) score += 30;
      if (title.includes(term)) score += 12;
      if (body.includes(term)) score += 2;
    }
    return score;
  }

  function render(query) {
    const rawQuery = query.trim().toLowerCase();
    if (rawQuery.length < 1) {
      close();
      return;
    }
    const terms = rawQuery.split(/\s+/);
    loadIndex().then((data) => {
      const matches = data
        .map((item) => ({ item, score: scoreItem(item, terms, rawQuery) }))
        .filter((row) => row.score > 0)
        .sort((a, b) => b.score - a.score)
        .slice(0, 12);
      if (!matches.length) {
        results.innerHTML = '<div class="search-result"><span>没有匹配结果</span></div>';
        results.classList.add("open");
        return;
      }
      results.innerHTML = matches
        .map(({ item }) => {
          const body = String(item.b || "").replace(/\s+/g, " ").slice(0, 92);
          return `<a class="search-result" href="${esc(item.p)}"><strong>${esc(item.t)}</strong><span>${esc(item.y)} · ${esc(body)}</span></a>`;
        })
        .join("");
      results.classList.add("open");
    });
  }

  input.addEventListener("input", () => render(input.value));
  input.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      input.value = "";
      close();
    }
  });
  document.addEventListener("keydown", (event) => {
    if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
      event.preventDefault();
      input.focus();
    }
  });
  document.addEventListener("click", (event) => {
    if (!event.target.closest(".search-shell")) close();
  });
})();
