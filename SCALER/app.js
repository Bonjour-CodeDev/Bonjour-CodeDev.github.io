(() => {
  "use strict";
  const viewer = document.getElementById("figure-viewer");
  const stage = document.getElementById("viewer-stage");
  const image = document.getElementById("viewer-image");
  const level = document.getElementById("zoom-level");
  let scale = 1;
  let fitted = true;
  let toastTimer;

  function notify(message) {
    const toast = document.getElementById("toast");
    clearTimeout(toastTimer);
    toast.textContent = message;
    toast.classList.add("visible");
    toastTimer = setTimeout(() => toast.classList.remove("visible"), 2600);
  }

  function setScale(next, fit = false) {
    if (!image.naturalWidth) return;
    const centerX = (stage.scrollLeft + stage.clientWidth / 2) / Math.max(1, stage.scrollWidth);
    const centerY = (stage.scrollTop + stage.clientHeight / 2) / Math.max(1, stage.scrollHeight);
    scale = Math.min(2, Math.max(0.02, next));
    fitted = fit;
    image.style.width = Math.round(image.naturalWidth * scale) + "px";
    level.textContent = Math.round(scale * 100) + "%";
    if (fit) {
      stage.scrollTo(0, 0);
    } else {
      stage.scrollLeft = centerX * stage.scrollWidth - stage.clientWidth / 2;
      stage.scrollTop = centerY * stage.scrollHeight - stage.clientHeight / 2;
    }
  }

  function fitImage() {
    if (!image.naturalWidth) return;
    const css = getComputedStyle(stage);
    const paddingX = parseFloat(css.paddingLeft) + parseFloat(css.paddingRight);
    const paddingY = parseFloat(css.paddingTop) + parseFloat(css.paddingBottom);
    setScale(Math.min(1, (stage.clientWidth - paddingX) / image.naturalWidth,
      (stage.clientHeight - paddingY) / image.naturalHeight), true);
  }

  if (viewer && typeof viewer.showModal === "function") {
    document.querySelectorAll("[data-zoom]").forEach(link => {
      link.addEventListener("click", event => {
        if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
        event.preventDefault();
        document.getElementById("viewer-title").textContent = link.dataset.title;
        image.alt = link.querySelector("img").alt;
        image.style.visibility = "hidden";
        image.onload = () => {
          fitImage();
          image.style.visibility = "visible";
        };
        image.onerror = () => {
          viewer.close();
          notify("The full-size figure could not load. Please try again.");
        };
        document.body.classList.add("viewer-open");
        viewer.showModal();
        image.src = link.href;
        if (image.complete && image.naturalWidth) {
          fitImage();
          image.style.visibility = "visible";
        }
      });
    });
    document.getElementById("zoom-in").addEventListener("click", () => setScale(scale * 1.4));
    document.getElementById("zoom-out").addEventListener("click", () => setScale(scale / 1.4));
    document.getElementById("zoom-fit").addEventListener("click", fitImage);
    document.getElementById("zoom-actual").addEventListener("click", () => setScale(1));
    document.getElementById("viewer-close").addEventListener("click", () => viewer.close());
    viewer.addEventListener("close", () => document.body.classList.remove("viewer-open"));
    viewer.addEventListener("click", event => {
      if (event.target !== viewer) return;
      const bounds = viewer.getBoundingClientRect();
      if (event.clientX < bounds.left || event.clientX > bounds.right ||
          event.clientY < bounds.top || event.clientY > bounds.bottom) viewer.close();
    });
    window.addEventListener("resize", () => {
      if (viewer.open && fitted) fitImage();
    });
  }

  document.querySelectorAll("[data-copy]").forEach(button => {
    button.addEventListener("click", async () => {
      const text = document.getElementById(button.dataset.copy).textContent;
      try {
        await navigator.clipboard.writeText(text);
        notify("Copied to clipboard");
      } catch {
        const target = document.getElementById(button.dataset.copy);
        const selection = window.getSelection();
        const range = document.createRange();
        range.selectNodeContents(target);
        selection.removeAllRanges();
        selection.addRange(range);
        notify("Text selected. Use your browser’s copy command.");
      }
    });
  });

  const navLinks = [...document.querySelectorAll(".nav-links a")];
  let navFrame;
  function updateNavigation() {
    const offset = document.querySelector(".site-header").getBoundingClientRect().height + 25;
    navLinks.forEach(link => {
      const bounds = document.querySelector(link.hash).getBoundingClientRect();
      const active = bounds.top <= offset && bounds.bottom > offset;
      link.classList.toggle("active", active);
      if (active) link.setAttribute("aria-current", "location");
      else link.removeAttribute("aria-current");
    });
    navFrame = null;
  }
  function scheduleNavigation() {
    if (!navFrame) navFrame = requestAnimationFrame(updateNavigation);
  }
  window.addEventListener("scroll", scheduleNavigation, {passive: true});
  window.addEventListener("resize", scheduleNavigation);
  updateNavigation();
})();
