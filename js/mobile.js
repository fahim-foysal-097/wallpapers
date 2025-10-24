// js/mobile.js
(() => {
  const JSON_PATH = "json/wallpapers-mobile.json";
  const galleryEl = document.getElementById("gallery");
  const summaryEl = document.getElementById("summary");
  const emptyStateEl = document.getElementById("emptyState");
  const searchInput = document.getElementById("searchInput");
  const aspectSelect = document.getElementById("aspectSelect");
  const downloadAllBtn = document.getElementById("downloadAllBtn");

  // modal elements
  const previewModalEl = document.getElementById("previewModal");
  const bsModal = new bootstrap.Modal(previewModalEl, {});
  const modalImage = document.getElementById("modalImage");
  const modalFilename = document.getElementById("modalFilename");
  const modalMeta = document.getElementById("modalMeta");
  const modalDownload = document.getElementById("modalDownload");
  const modalPrevBtn = document.getElementById("modalPrevBtn");
  const modalNextBtn = document.getElementById("modalNextBtn");

  let wallpapers = [];
  let filtered = [];
  let currentIndex = 0;

  const ASPECT_KEY = "mobileAspectRatio";
  const DEFAULT_ASPECT = "9/16";

  function setAspectOnThumbs(aspect) {
    // apply inline style to each .thumb-wrap so CSS aspect-ratio is updated
    document.querySelectorAll(".thumb-wrap").forEach((el) => {
      el.style.aspectRatio = aspect;
    });
  }

  function buildTile(entry, idx, aspect) {
    const col = document.createElement("div");
    col.className = "col-6 col-sm-4 col-md-3"; // fine for mobile gallery layout

    const tile = document.createElement("div");
    tile.className = "tile";

    const thumbWrap = document.createElement("a");
    thumbWrap.href = "#";
    thumbWrap.className = "thumb-wrap";
    thumbWrap.style.aspectRatio = aspect;
    thumbWrap.dataset.index = idx;

    const img = document.createElement("img");
    img.className = "thumb";
    img.src = entry.url;
    img.alt = entry.filename;
    img.loading = "lazy";

    thumbWrap.appendChild(img);

    const footer = document.createElement("div");
    footer.className = "tile-footer";

    const meta = document.createElement("div");
    meta.className = "meta";
    meta.textContent = `${entry.filename}`;

    const actions = document.createElement("div");
    actions.className = "d-flex gap-2 align-items-center";

    const dl = document.createElement("a");
    dl.href = entry.url;
    dl.className = "btn btn-tiny btn-outline-light";
    dl.setAttribute("download", entry.filename);
    dl.innerHTML = `<i class="bi bi-download"></i>`;

    actions.appendChild(dl);

    footer.appendChild(meta);
    footer.appendChild(actions);

    tile.appendChild(thumbWrap);
    tile.appendChild(footer);
    col.appendChild(tile);

    // click -> preview
    thumbWrap.addEventListener("click", (ev) => {
      ev.preventDefault();
      openModalAtIndex(parseInt(thumbWrap.dataset.index, 10));
    });

    return col;
  }

  function renderList(list) {
    galleryEl.innerHTML = "";
    if (!list || list.length === 0) {
      emptyStateEl.style.display = "block";
      summaryEl.textContent = "0 wallpapers";
      return;
    } else {
      emptyStateEl.style.display = "none";
    }

    const aspect = aspectSelect.value || DEFAULT_ASPECT;

    list.forEach((entry, i) => {
      const tile = buildTile(entry, i, aspect);
      galleryEl.appendChild(tile);
    });

    setAspectOnThumbs(aspect);

    summaryEl.textContent = `${list.length} mobile wallpaper${
      list.length === 1 ? "" : "s"
    }`;
  }

  function openModalAtIndex(i) {
    currentIndex = i;
    const entry = filtered[i];
    if (!entry) return;
    modalImage.src = entry.url;
    modalFilename.textContent = entry.filename;
    modalMeta.textContent = `${Math.round(entry.size / 1024)} KB • ${new Date(
      entry.modified
    ).toLocaleString()}`;
    modalDownload.href = entry.url;
    modalDownload.setAttribute("download", entry.filename);
    bsModal.show();
  }

  function prev() {
    if (filtered.length === 0) return;
    currentIndex = (currentIndex - 1 + filtered.length) % filtered.length;
    openModalAtIndex(currentIndex);
  }
  function next() {
    if (filtered.length === 0) return;
    currentIndex = (currentIndex + 1) % filtered.length;
    openModalAtIndex(currentIndex);
  }

  // simple client-side search by filename
  function applySearch(text) {
    const q = text.trim().toLowerCase();
    if (!q) {
      filtered = [...wallpapers];
    } else {
      filtered = wallpapers.filter((w) => w.filename.toLowerCase().includes(q));
    }
    renderList(filtered);
  }

  // Optional sort: name/time/size
  function applySort(mode) {
    const arr = [...filtered];
    switch (mode) {
      case "name-asc":
        arr.sort((a, b) => a.filename.localeCompare(b.filename));
        break;
      case "name-desc":
        arr.sort((a, b) => b.filename.localeCompare(a.filename));
        break;
      case "time-desc":
        arr.sort((a, b) => new Date(b.modified) - new Date(a.modified));
        break;
      case "time-asc":
        arr.sort((a, b) => new Date(a.modified) - new Date(b.modified));
        break;
      case "size-desc":
        arr.sort((a, b) => b.size - a.size);
        break;
      case "size-asc":
        arr.sort((a, b) => a.size - b.size);
        break;
      default:
        break;
    }
    filtered = arr;
    renderList(filtered);
  }

  // fetch json and init
  async function init() {
    // restore aspect ratio selection
    const savedAspect = localStorage.getItem(ASPECT_KEY) || DEFAULT_ASPECT;
    if (aspectSelect) {
      aspectSelect.value = savedAspect;
      aspectSelect.addEventListener("change", () => {
        localStorage.setItem(ASPECT_KEY, aspectSelect.value);
        setAspectOnThumbs(aspectSelect.value);
      });
    }

    // wire modal prev/next
    if (modalPrevBtn) modalPrevBtn.addEventListener("click", prev);
    if (modalNextBtn) modalNextBtn.addEventListener("click", next);

    // search input
    if (searchInput) {
      searchInput.addEventListener("input", (e) => {
        applySearch(e.target.value);
      });
    }

    // wire sort dropdown items (if present)
    document.querySelectorAll(".sort-option").forEach((el) => {
      el.addEventListener("click", (ev) => {
        ev.preventDefault();
        const mode = el.dataset.sort;
        applySort(mode);
      });
    });

    try {
      const resp = await fetch(JSON_PATH, { cache: "no-cache" });
      if (!resp.ok)
        throw new Error(`Failed to fetch ${JSON_PATH}: ${resp.status}`);
      const data = await resp.json();
      wallpapers = data.wallpapers || [];
      filtered = [...wallpapers];

      // set download all link to the expected mobile zip file (user can provide)
      if (downloadAllBtn) {
        // leave it; default href in HTML is wallpaper-mobile-all.zip; optionally adjust if json contains path
      }

      renderList(filtered);
    } catch (err) {
      console.error("Error loading mobile wallpapers:", err);
      summaryEl.textContent = "Error loading mobile wallpapers";
      emptyStateEl.style.display = "block";
    }
  }

  // keyboard navigation for modal
  document.addEventListener("keydown", (ev) => {
    if (!document.body.classList.contains("modal-open")) return;
    if (ev.key === "ArrowLeft") prev();
    if (ev.key === "ArrowRight") next();
  });

  // init on DOM ready
  document.addEventListener("DOMContentLoaded", init);
})();

// --- Typing animation for #animatedText for mobile page ---

(function typingAnimation() {
  const el = document.getElementById("animatedText");
  if (!el) return; // nothing to do

  // phrases to cycle through - you can edit these
  const phrases = [
    "Discover Beautiful Wallpapers",
    "Portrait wallpapers for phones",
    "High-resolution phone backgrounds",
  ];

  const TYPING_SPEED = 40; // ms per character
  const ERASING_SPEED = 30; // ms per character when deleting
  const PAUSE_AFTER = 1200; // pause after typing a phrase (ms)
  let phraseIndex = 0;
  let charIndex = 0;
  let isDeleting = false;

  function tick() {
    const current = phrases[phraseIndex];
    if (!isDeleting) {
      // typing
      el.textContent = current.slice(0, charIndex + 1);
      charIndex++;
      if (charIndex === current.length) {
        // finished typing
        isDeleting = true;
        setTimeout(tick, PAUSE_AFTER);
        return;
      }
      setTimeout(tick, TYPING_SPEED);
    } else {
      // deleting
      el.textContent = current.slice(0, charIndex - 1);
      charIndex--;
      if (charIndex === 0) {
        isDeleting = false;
        phraseIndex = (phraseIndex + 1) % phrases.length;
        setTimeout(tick, TYPING_SPEED);
        return;
      }
      setTimeout(tick, ERASING_SPEED);
    }
  }

  // start when DOM ready (if script is appended at end it's usually safe, but be explicit)
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => {
      setTimeout(tick, 300); // small initial delay
    });
  } else {
    setTimeout(tick, 300);
  }
})();
