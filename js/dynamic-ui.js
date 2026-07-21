(() => {
  "use strict";

  const enteringFromHome = sessionStorage.getItem("albumDynamicEntering") === "1";
  if (enteringFromHome) {
    sessionStorage.removeItem("albumDynamicEntering");
    document.body.classList.add("album-arriving");
    const curtain = document.createElement("div");
    curtain.className = "album-arrival-curtain";
    curtain.innerHTML = "<i></i><span>ÁLBUM DA COPA 2026</span>";
    document.body.appendChild(curtain);
    setTimeout(() => {
      curtain.remove();
      document.body.classList.remove("album-arriving");
    }, 1050);
  }

  const reduceMotion = matchMedia("(prefers-reduced-motion: reduce)").matches;
  let previousPercent = Number.parseInt(document.getElementById("sPct")?.textContent, 10) || 0;
  let toastTimer;

  function animateStickers(root = document) {
    if (reduceMotion) return;
    root.querySelectorAll(".grid .sticker:not([data-motion-ready])").forEach((sticker, index) => {
      sticker.dataset.motionReady = "1";
      sticker.style.setProperty("--stagger", `${Math.min(index, 24) * 32}ms`);
      sticker.classList.add("sticker-enter");
    });
  }

  function popCounters() {
    document.querySelectorAll(".sum b,.stats-card b").forEach(counter => {
      counter.classList.remove("count-pop");
      void counter.offsetWidth;
      counter.classList.add("count-pop");
    });
  }

  function burstAt(x, y) {
    if (reduceMotion) return;
    const burst = document.createElement("i");
    burst.className = "sticker-burst";
    burst.style.left = `${x}px`;
    burst.style.top = `${y}px`;
    document.body.appendChild(burst);
    setTimeout(() => burst.remove(), 750);
  }

  function celebrate() {
    if (reduceMotion || document.querySelector(".celebration")) return;
    const layer = document.createElement("div");
    layer.className = "celebration";
    const colors = ["#ffd32a", "#16a34a", "#075bd8", "#df2336", "#ffffff"];
    for (let i = 0; i < 64; i += 1) {
      const piece = document.createElement("i");
      piece.className = "confetti";
      piece.style.setProperty("--left", `${Math.random() * 100}%`);
      piece.style.setProperty("--delay", `${Math.random() * 0.65}s`);
      piece.style.setProperty("--duration", `${1.8 + Math.random() * 1.5}s`);
      piece.style.setProperty("--drift", `${-90 + Math.random() * 180}px`);
      piece.style.setProperty("--confetti", colors[i % colors.length]);
      layer.appendChild(piece);
    }
    const banner = document.createElement("div");
    banner.className = "completion-banner";
    banner.textContent = "🏆 País completo!";
    document.body.append(layer, banner);
    setTimeout(() => {
      layer.remove();
      banner.remove();
    }, 3600);
  }

  function showAnimatedToast(message) {
    const node = document.getElementById("toast");
    if (!node) return;
    clearTimeout(toastTimer);
    node.textContent = message;
    node.style.display = "block";
    requestAnimationFrame(() => node.classList.add("toast-visible"));
    toastTimer = setTimeout(() => {
      node.classList.remove("toast-visible");
      setTimeout(() => {
        node.style.display = "none";
      }, 260);
    }, 2200);
  }

  if (typeof window.toast !== "function") window.toast = showAnimatedToast;

  const grid = document.getElementById("grid");
  if (grid) new MutationObserver(() => animateStickers(grid)).observe(grid, {childList: true});
  animateStickers();

  document.addEventListener("click", event => {
    const sticker = event.target.closest(".sticker");
    if (!sticker) return;
    const wasMissing = sticker.classList.contains("missing");
    const rect = sticker.getBoundingClientRect();
    setTimeout(() => {
      popCounters();
      const currentPercent = Number.parseInt(document.getElementById("sPct")?.textContent, 10) || 0;
      if (wasMissing) burstAt(rect.left + rect.width / 2, rect.top + rect.height / 2);
      if (previousPercent < 100 && currentPercent === 100) celebrate();
      previousPercent = currentPercent;
    }, 40);
  }, true);

  document.addEventListener("visibilitychange", () => {
    document.body.classList.toggle("page-paused", document.hidden);
  });
})();
