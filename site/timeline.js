(function () {
  const dots = Array.from(document.querySelectorAll(".timeline-dot"));
  const cards = Array.from(document.querySelectorAll(".event-card"));
  if (!dots.length || !cards.length) return;

  function activate(year) {
    cards.forEach((card) => {
      card.classList.toggle("active", card.dataset.year === String(year));
      if (card.dataset.year === String(year)) {
        card.scrollIntoView({ behavior: "smooth", inline: "center", block: "nearest" });
      }
    });
  }

  dots.forEach((dot) => {
    dot.addEventListener("click", () => activate(dot.dataset.year));
  });
})();
