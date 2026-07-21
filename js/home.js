(() => {
  "use strict";

  const notice = document.getElementById("homeNotice");
  const albumLink = document.querySelector(".album-card");
  let timer;
  let opening = false;

  function show(message) {
    if (!notice) return;
    clearTimeout(timer);
    notice.textContent = message;
    notice.classList.add("show");
    timer = setTimeout(() => notice.classList.remove("show"), 2200);
  }

  function openAlbum(event) {
    if (!albumLink || opening) return;
    event.preventDefault();
    opening = true;

    const book = albumLink.querySelector(".album-book");
    const cover = book?.querySelector("img");
    const rect = (book || albumLink).getBoundingClientRect();
    const openWidth = Math.min(innerWidth * 0.92, innerHeight * 0.82 * 1.5);
    const openHeight = openWidth / 1.5;
    const openPageWidth = openWidth / 2;
    const openLeft = innerWidth / 2;
    const openTop = (innerHeight - openHeight) / 2;
    const scene = document.createElement("div");
    scene.className = "album-transition";
    scene.style.cssText = `left:${rect.left}px;top:${rect.top}px;width:${rect.width}px;height:${rect.height}px;--open-left:${openLeft}px;--open-top:${openTop}px;--open-width:${openPageWidth}px;--open-height:${openHeight}px`;
    scene.innerHTML = `<div class="transition-pages"><i></i><i></i><i></i><span>ÁLBUM DA COPA 2026</span></div><div class="transition-cover"><img src="${cover?.src || "assets/hub/album_copa_capa.png"}" alt=""></div>`;

    const veil = document.createElement("div");
    veil.className = "album-transition-veil";
    document.body.append(veil, scene);
    document.body.classList.add("opening-album");
    requestAnimationFrame(() => requestAnimationFrame(() => scene.classList.add("open")));
    sessionStorage.setItem("albumDynamicEntering", "1");
    setTimeout(() => { location.href = albumLink.href; }, 1180);
  }

  albumLink?.addEventListener("click", openAlbum);
  document.querySelectorAll(".side-card").forEach(card => {
    card.addEventListener("click", () => show(`${card.getAttribute("aria-label")} está disponível dentro do álbum.`));
  });

  const video = document.querySelector(".home-video");
  document.addEventListener("visibilitychange", () => {
    if (!video) return;
    if (document.hidden) video.pause();
    else video.play().catch(() => {});
  });

  if ("serviceWorker" in navigator && location.protocol !== "file:") {
    addEventListener("load", () => navigator.serviceWorker.register("./sw.js").catch(() => {}));
  }
})();
