(function () {
  if (!window || !document) return;

  // check for touch/coarse pointer
  const isTouch =
    "ontouchstart" in window ||
    (navigator.maxTouchPoints && navigator.maxTouchPoints > 0);
  if (window.matchMedia("(pointer: coarse)").matches || isTouch) return;

  // create cursor
  let cursor = document.createElement("div");
  cursor.className = "custom-cursor";
  document.body.appendChild(cursor);

  // pointer position
  document.addEventListener("pointermove", (e) => {
    cursor.style.left = e.clientX + "px";
    cursor.style.top = e.clientY + "px";
  });

  // hover effect on interactive elements
  const hoverSelector =
    "a, button, .btn, input, textarea, select, [role=button], .gallery-card, .nav-link, .thumb";
  function bindHover() {
    document.querySelectorAll(hoverSelector).forEach((el) => {
      if (el.__cursorBound) return;
      el.addEventListener("pointerenter", () =>
        cursor.classList.add("cursor--hover")
      );
      el.addEventListener("pointerleave", () =>
        cursor.classList.remove("cursor--hover")
      );
      el.__cursorBound = true;
    });
  }
  bindHover();
  new MutationObserver(bindHover).observe(document.body, {
    childList: true,
    subtree: true,
  });

  // mouse down/up
  document.addEventListener("pointerdown", (e) => {
    if (e.button !== 0) return;
    cursor.classList.add("cursor--down");
    createRipple(e.clientX, e.clientY);
  });
  document.addEventListener("pointerup", (e) => {
    if (e.button !== 0) return;
    cursor.classList.remove("cursor--down");
  });

  // ripple creation
  function createRipple(x, y) {
    const r = document.createElement("div");
    r.className = "cursor-ripple";
    r.style.left = x + "px";
    r.style.top = y + "px";
    document.body.appendChild(r);
    r.addEventListener("animationend", () => r.remove(), { once: true });
    setTimeout(() => {
      if (r.parentNode) r.parentNode.removeChild(r);
    }, 500);
  }
})();
