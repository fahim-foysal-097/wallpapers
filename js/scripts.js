(() => {
  const JSON_PATH = "json/wallpapers.json";
  const CATEGORIES_PATH = "json/categories.json";
  const FAVORITES_JSON = "json/favorites.json";
  const galleryEl = document.getElementById("gallery");
  const summaryEl = document.getElementById("summary");
  const emptyState = document.getElementById("emptyState");
  const searchInput = document.getElementById("searchInput");
  const sortOptions = document.querySelectorAll(".sort-option");
  const downloadAllBtn = document.getElementById("downloadAllBtn");
  const animatedEl = document.getElementById("animatedText");
  const chipsContainer = document.getElementById("categoryChips");
  const chipsPrevBtn = document.getElementById("chipsPrev");
  const chipsNextBtn = document.getElementById("chipsNext");

  // GITHUB RELEASES CONFIG
  const GITHUB_OWNER = "fahim-foysal-097";
  const GITHUB_REPO = "wallpapers";
  const TAG_PREFIX = "wallpaper-archive-";
  const CACHE_TTL_MS = 10 * 60 * 1000; // 10 minutes cache

  // set downloadAll link if present (will be replaced after checking releases)
  if (downloadAllBtn) {
    const originalHref = downloadAllBtn.href || "wallpaper-all.zip";
    downloadAllBtn.dataset.fallback = originalHref;
    downloadAllBtn.classList.add("disabled");
    downloadAllBtn.setAttribute("aria-disabled", "true");
    downloadAllBtn.innerHTML = `<i class="bi bi-hourglass-split"></i>&nbsp;Checking latest...`;
    fetchReleaseAssetAndSetButton("wallpaper-all.zip", downloadAllBtn);
  }

  async function getLatestReleaseAsset(assetName) {
    try {
      const cacheKey = `gh_asset_cache_${GITHUB_OWNER}_${GITHUB_REPO}_${assetName}`;
      const cached = localStorage.getItem(cacheKey);
      if (cached) {
        const parsed = JSON.parse(cached);
        if (Date.now() - parsed.ts < CACHE_TTL_MS) {
          return parsed.url;
        }
      }

      const api = `https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/releases?per_page=50`;
      const resp = await fetch(api, {
        headers: { Accept: "application/vnd.github.v3+json" },
      });
      if (!resp.ok) {
        console.warn("GitHub API fetch failed", resp.status);
        return null;
      }
      const releases = await resp.json();

      // filter by our tag prefix then sort newest first
      const matchingReleases = releases
        .filter((r) => r.tag_name && r.tag_name.startsWith(TAG_PREFIX))
        .sort((a, b) => new Date(b.created_at) - new Date(a.created_at));

      for (const rel of matchingReleases) {
        if (!rel.assets || !rel.assets.length) continue;
        const asset = rel.assets.find((a) => a.name === assetName);
        if (asset && asset.browser_download_url) {
          localStorage.setItem(
            cacheKey,
            JSON.stringify({ url: asset.browser_download_url, ts: Date.now() })
          );
          return asset.browser_download_url;
        }
      }
      return null;
    } catch (err) {
      console.error("Failed to get release asset", err);
      return null;
    }
  }

  async function fetchReleaseAssetAndSetButton(assetName, btnEl) {
    try {
      const url = await getLatestReleaseAsset(assetName);
      if (url) {
        btnEl.href = url;
        btnEl.setAttribute("download", assetName);
        btnEl.classList.remove("disabled");
        btnEl.removeAttribute("aria-disabled");
        btnEl.innerHTML = `<i class="bi bi-file-earmark-zip-fill"></i>&nbsp;Download All Desktop`;
        btnEl.title = `Download all desktop wallpapers`;
        return;
      }
    } catch (e) {
      console.warn("Error while resolving release asset:", e);
    }
    // fallback
    const fallback = btnEl.dataset.fallback || `/${assetName}`;
    btnEl.href = fallback;
    btnEl.setAttribute("download", assetName);
    btnEl.classList.remove("disabled");
    btnEl.removeAttribute("aria-disabled");
    btnEl.innerHTML = `<i class="bi bi-file-earmark-zip-fill"></i>&nbsp;Download All`;
    btnEl.title = "Download all desktop wallpapers";
  }

  const MODE = window.GALLERY_MODE === "favorites" ? "favorites" : "all";
  const INLINE_FAVORITES = Array.isArray(window.FAVORITES)
    ? window.FAVORITES
    : [];

  let data = [];
  let filtered = [];

  // modal elements and navigation
  const previewModalEl = document.getElementById("previewModal");
  const modal = previewModalEl ? new bootstrap.Modal(previewModalEl) : null;
  let modalImage = document.getElementById("modalImage"); // changed to let
  const modalFilename = document.getElementById("modalFilename");
  const modalMeta = document.getElementById("modalMeta");
  const modalDownload = document.getElementById("modalDownload");
  const modalPrevBtn = document.getElementById("modalPrevBtn");
  const modalNextBtn = document.getElementById("modalNextBtn");

  let currentIndex = -1; // index into filtered[]
  let modalVisible = false;

  function humanSize(n) {
    if (n < 1024) return n + " B";
    if (n < 1024 * 1024) return (n / 1024).toFixed(1) + " KB";
    if (n < 1024 * 1024 * 1024) return (n / 1024 / 1024).toFixed(1) + " MB";
    return (n / 1024 / 1024 / 1024).toFixed(2) + " GB";
  }

  /* typing animation */
  (function initTyping() {
    if (!animatedEl) return;
    const original =
      animatedEl.textContent.trim() || "Discover Beautiful Wallpapers";
    const alt = "Download Wallpapers";
    const alt2 = "High Quality Wallpapers";
    const phrases = [original, alt, alt2];

    // If mobile (<= 480px) just show the first phrase as static text
    const isMobile = window.matchMedia("(max-width: 480px)").matches;
    if (isMobile) {
      animatedEl.textContent = phrases[0];
      return;
    }

    const typingSpeed = 60;
    const deletingSpeed = 40;
    const pauseAfterTyping = 1200;
    const pauseAfterDeleting = 350;

    let phraseIndex = 0;
    let charIndex = 0;
    let mode = "typing";
    let timeoutId = null;

    function step() {
      const text = phrases[phraseIndex];
      if (mode === "typing") {
        charIndex++;
        animatedEl.textContent = text.slice(0, charIndex);
        if (charIndex >= text.length) {
          mode = "pauseAfterTyping";
          timeoutId = setTimeout(() => {
            mode = "deleting";
            timeoutId = setTimeout(step, deletingSpeed);
          }, pauseAfterTyping);
          return;
        }
        timeoutId = setTimeout(step, typingSpeed);
      } else if (mode === "deleting") {
        charIndex--;
        animatedEl.textContent = text.slice(0, charIndex);
        if (charIndex <= 0) {
          phraseIndex = (phraseIndex + 1) % phrases.length;
          mode = "pauseAfterDeleting";
          timeoutId = setTimeout(() => {
            mode = "typing";
            charIndex = 0;
            timeoutId = setTimeout(step, typingSpeed);
          }, pauseAfterDeleting);
          return;
        }
        timeoutId = setTimeout(step, deletingSpeed);
      } else {
        mode = "typing";
        charIndex = 0;
        timeoutId = setTimeout(step, typingSpeed);
      }
    }

    timeoutId = setTimeout(step, 700);
  })();

  /* ---------- CHIPS: build + scroll behavior ---------- */

  function buildChip(name, label, count, isActive) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "chip btn";
    if (isActive) btn.classList.add("active");
    btn.dataset.category = name;
    btn.setAttribute("role", "option");
    btn.setAttribute("aria-selected", isActive ? "true" : "false");
    btn.title = `${label} (${count})`;
    // DO NOT truncate names — user requested full names and keep scrollbar
    btn.innerHTML = `${label} <span class="count ms-2">${count}</span>`;
    btn.addEventListener("click", () => {
      document.querySelectorAll("#categoryChips .chip").forEach((c) => {
        c.classList.remove("active");
        c.setAttribute("aria-selected", "false");
      });
      btn.classList.add("active");
      btn.setAttribute("aria-selected", "true");
      selectedCategory = name;
      applySearchSort();
    });
    return btn;
  }

  function showHideChipNav() {
    // Show/hide nav buttons depending on scroll position and overflow
    if (!chipsContainer || !chipsPrevBtn || !chipsNextBtn) return;
    const el = chipsContainer;
    // if no overflow -> hide both
    if (el.scrollWidth <= el.clientWidth + 2) {
      chipsPrevBtn.style.display = "none";
      chipsNextBtn.style.display = "none";
      return;
    }
    chipsPrevBtn.style.display = "";
    chipsNextBtn.style.display = "";
    // disable left if at leftmost
    chipsPrevBtn.disabled = el.scrollLeft <= 2;
    // disable right if at rightmost (allow small epsilon)
    chipsNextBtn.disabled =
      el.scrollLeft + el.clientWidth >= el.scrollWidth - 2;
  }

  // scroll by a fraction of the visible width
  function scrollChips(direction = "right") {
    if (!chipsContainer) return;
    const el = chipsContainer;
    const amount = Math.round(el.clientWidth * 0.66);
    const target =
      direction === "right" ? el.scrollLeft + amount : el.scrollLeft - amount;
    el.scrollTo({ left: target, behavior: "smooth" });
  }

  // wire buttons
  if (chipsPrevBtn)
    chipsPrevBtn.addEventListener("click", (e) => {
      e.preventDefault();
      scrollChips("left");
    });
  if (chipsNextBtn)
    chipsNextBtn.addEventListener("click", (e) => {
      e.preventDefault();
      scrollChips("right");
    });

  // show/hide on resize/scroll
  if (chipsContainer) {
    chipsContainer.addEventListener("scroll", () => {
      requestAnimationFrame(showHideChipNav);
    });
    window.addEventListener("resize", () => {
      requestAnimationFrame(showHideChipNav);
    });
    // keyboard: left/right/home/end to navigate the scroll area
    chipsContainer.addEventListener("keydown", (ev) => {
      if (ev.key === "ArrowRight") {
        ev.preventDefault();
        scrollChips("right");
      } else if (ev.key === "ArrowLeft") {
        ev.preventDefault();
        scrollChips("left");
      } else if (ev.key === "Home") {
        ev.preventDefault();
        chipsContainer.scrollTo({ left: 0, behavior: "smooth" });
      } else if (ev.key === "End") {
        ev.preventDefault();
        chipsContainer.scrollTo({
          left: chipsContainer.scrollWidth,
          behavior: "smooth",
        });
      }
    });
  }

  /* -------------------- Gallery rendering -------------------- */

  function renderSummary() {
    if (!summaryEl) return;
    summaryEl.textContent = `${filtered.length} wallpaper${
      filtered.length !== 1 ? "s" : ""
    }`;
  }

  function clearGallery() {
    if (!galleryEl) return;
    galleryEl.innerHTML = "";
  }

  function makeTile(item, idx) {
    const col = document.createElement("div");
    col.className = "col-6 col-sm-4 col-md-3 col-xl-3";

    const tile = document.createElement("div");
    tile.className = "tile";

    // wrapper to enforce 16:9
    const wrap = document.createElement("div");
    wrap.className = "thumb-wrap";

    const img = document.createElement("img");
    img.className = "thumb";
    img.loading = "lazy";
    img.decoding = "async";
    img.alt = item.filename;

    // show thumbnail if present for faster load, otherwise full url
    img.src = item.thumb_url ? item.thumb_url : item.url;

    // store full-res in data attribute so modal uses full image
    img.dataset.fullUrl = item.url;
    img.dataset.index = String(idx);
    img.dataset.filename = item.filename;

    img.onerror = () => {
      img.src =
        "data:image/svg+xml;charset=UTF-8," +
        encodeURIComponent(
          `<svg xmlns='http://www.w3.org/2000/svg' width='1200' height='675'><rect fill='#0b1220' width='100%' height='100%'/><text x='50%' y='50%' fill='#666' dominant-baseline='middle' text-anchor='middle' font-size='24'>Image not available</text></svg>`
        );
    };

    img.addEventListener("click", () => openPreviewAtIndex(idx));
    wrap.appendChild(img);

    const footer = document.createElement("div");
    footer.className = "tile-footer";

    const meta = document.createElement("div");
    meta.className = "meta";
    meta.title = item.filename;
    meta.textContent = item.filename;

    const actions = document.createElement("div");
    actions.className = "d-flex gap-2 align-items-center";

    const sizeBadge = document.createElement("span");
    sizeBadge.className = "text-muted small";
    sizeBadge.textContent = humanSize(item.size);

    const dlBtn = document.createElement("a");
    dlBtn.className = "btn btn-sm btn-outline-light btn-tiny";
    dlBtn.href = item.url;
    dlBtn.setAttribute("download", item.filename);
    dlBtn.innerHTML = `<i class="bi bi-download"></i>`;

    actions.appendChild(sizeBadge);
    actions.appendChild(dlBtn);

    footer.appendChild(meta);
    footer.appendChild(actions);

    tile.appendChild(wrap);
    tile.appendChild(footer);
    col.appendChild(tile);

    return col;
  }

  function renderGrid(items) {
    clearGallery();
    if (!galleryEl) return;
    if (!items.length) {
      if (emptyState) emptyState.style.display = "";
      return;
    } else {
      if (emptyState) emptyState.style.display = "none";
    }
    const frag = document.createDocumentFragment();
    items.forEach((it, idx) => frag.appendChild(makeTile(it, idx)));
    galleryEl.appendChild(frag);
  }

  /* -------------------- Modal navigation + progressive loader -------------------- */

  // helper to preload image URL and resolve when loaded or reject
  function preloadImage(url) {
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = () => resolve(img);
      img.onerror = (e) => reject(e);
      img.src = url;
    });
  }

  // returns true if file is likely an animated gif (cheap check)
  function isGifUrl(url) {
    return typeof url === "string" && url.toLowerCase().endsWith(".gif");
  }

  function showSpinner(show = true) {
    const spinner = document.getElementById("modalSpinner");
    if (!spinner) return;
    spinner.style.display = show ? "" : "none";
  }

  // crossfade swap: replace current modalImage.src with newImageElement's src
  function swapModalImageElement(newImgEl) {
    // current element
    if (!modalImage) return;
    try {
      modalImage.classList.remove("modal-img-loaded");
      modalImage.classList.add("modal-img-fade");
      requestAnimationFrame(() => {
        modalImage.src = newImgEl.src;
        modalImage.alt = newImgEl.alt || modalImage.alt || "";
        modalImage.classList.remove("modal-img-blur");
        modalImage.classList.add("modal-img-loaded");
        showSpinner(false);
        modalImage.classList.add("modal-img-visible");
      });
    } catch (e) {
      modalImage.src = newImgEl.src;
      showSpinner(false);
      modalImage.classList.remove("modal-img-blur");
      modalImage.classList.add("modal-img-loaded", "modal-img-visible");
    }
  }

  // If an error occurs loading full-res, show a fallback svg block
  function showModalImageError() {
    if (!modalImage) return;
    showSpinner(false);
    modalImage.className = "";
    modalImage.removeAttribute("src");
    modalImage.outerHTML = `<div class="modal-image-error">Image failed to load</div>`;
  }

  function openPreviewAtIndex(idx) {
    if (!Array.isArray(filtered) || idx < 0 || idx >= filtered.length) return;
    currentIndex = idx;
    showImageAt(currentIndex);
    if (modal) modal.show();
  }

  async function showImageAt(idx) {
    const item = filtered[idx];
    if (!item) return;

    // Recreate modalImage if it was replaced by an error box earlier
    if (!document.getElementById("modalImage")) {
      const wrap = document.querySelector(".modal-preview-wrap");
      if (!wrap) return;
      const newImg = document.createElement("img");
      newImg.id = "modalImage";
      newImg.className = "img-fluid rounded shadow-lg";
      newImg.style.maxHeight = "80vh";
      newImg.style.objectFit = "contain";
      wrap.appendChild(newImg);
      modalImage = document.getElementById("modalImage");
    }

    // metadata
    if (modalFilename) modalFilename.textContent = item.filename;
    if (modalMeta)
      modalMeta.textContent = `${new Date(
        item.modified
      ).toLocaleString()} • ${humanSize(item.size)}`;
    if (modalDownload) {
      modalDownload.href = item.url;
      modalDownload.setAttribute("download", item.filename);
    }

    // nav buttons states
    if (modalPrevBtn) modalPrevBtn.disabled = idx <= 0;
    if (modalNextBtn) modalNextBtn.disabled = idx >= filtered.length - 1;

    // Clear any classes from previous loads
    modalImage.className = "img-fluid rounded shadow-lg";
    modalImage.classList.remove(
      "modal-img-blur",
      "modal-img-loaded",
      "modal-img-fade",
      "modal-img-visible"
    );

    const hasThumb = item.thumb_url && item.thumb_url.trim().length;
    const urlIsGif = isGifUrl(item.url);

    if (hasThumb && !urlIsGif) {
      // show thumbnail immediately (fast)
      modalImage.src = item.thumb_url;
      modalImage.alt = item.filename;
      modalImage.classList.add("modal-img-blur", "modal-img-visible");
      showSpinner(true);

      // preload full image in background
      try {
        const loaded = await preloadImage(item.url);
        swapModalImageElement(loaded);
      } catch (err) {
        console.warn("Full image failed to preload:", item.url, err);
        showSpinner(false);
        modalImage.classList.remove("modal-img-blur");
        modalImage.classList.add("modal-img-loaded", "modal-img-visible");
      }
      return;
    }

    // If there's no thumbnail or it is a gif: load the actual URL directly.
    modalImage.classList.add("modal-img-fade");
    showSpinner(true);

    try {
      const loaded = await preloadImage(item.url);
      swapModalImageElement(loaded);
    } catch (err) {
      console.error("Modal image load error:", err);
      showModalImageError();
    }
  }

  function showNext() {
    if (currentIndex < filtered.length - 1) {
      currentIndex++;
      showImageAt(currentIndex);
    }
  }

  function showPrev() {
    if (currentIndex > 0) {
      currentIndex--;
      showImageAt(currentIndex);
    }
  }

  // attach nav button handlers
  if (modalPrevBtn)
    modalPrevBtn.addEventListener("click", (e) => {
      e.preventDefault();
      showPrev();
    });
  if (modalNextBtn)
    modalNextBtn.addEventListener("click", (e) => {
      e.preventDefault();
      showNext();
    });

  if (previewModalEl) {
    previewModalEl.addEventListener("shown.bs.modal", () => {
      modalVisible = true;
    });
    previewModalEl.addEventListener("hidden.bs.modal", () => {
      modalVisible = false;
    });
  }

  // keyboard navigation for modal
  document.addEventListener("keydown", (ev) => {
    if (!modalVisible) return;
    if (ev.key === "ArrowRight") {
      ev.preventDefault();
      showNext();
    } else if (ev.key === "ArrowLeft") {
      ev.preventDefault();
      showPrev();
    } else if (ev.key === "Escape") {
      // let bootstrap handle
    }
  });

  /* -------------------- Sorting, searching, loading -------------------- */

  function applySearchSort() {
    const q =
      searchInput && searchInput.value
        ? searchInput.value.trim().toLowerCase()
        : "";
    filtered = data.filter((it) => {
      if (
        selectedCategory &&
        selectedCategory !== "all" &&
        it.category !== selectedCategory
      )
        return false;
      if (!q) return true;
      if (it.filename.toLowerCase().includes(q)) return true;
      if (humanSize(it.size).toLowerCase().includes(q)) return true;
      if (new Date(it.modified).toLocaleString().toLowerCase().includes(q))
        return true;
      return false;
    });
    renderSummary();
    renderGrid(filtered);
  }

  function applySortMode(mode) {
    switch (mode) {
      case "name-asc":
        filtered.sort((a, b) => a.filename.localeCompare(b.filename));
        break;
      case "name-desc":
        filtered.sort((a, b) => b.filename.localeCompare(a.filename));
        break;
      case "time-desc":
        filtered.sort((a, b) => new Date(b.modified) - new Date(a.modified));
        break;
      case "time-asc":
        filtered.sort((a, b) => new Date(a.modified) - new Date(b.modified));
        break;
      case "size-desc":
        filtered.sort((a, b) => b.size - a.size);
        break;
      case "size-asc":
        filtered.sort((a, b) => a.size - b.size);
        break;
      default:
        break;
    }
    renderGrid(filtered);
  }

  async function loadWallpapers() {
    try {
      const resp = await fetch(JSON_PATH, { cache: "no-store" });
      if (!resp.ok) throw new Error("Could not load wallpapers.json");
      const json = await resp.json();
      return json.wallpapers || [];
    } catch (err) {
      console.error("Failed to load", JSON_PATH, err);
      return [];
    }
  }

  async function loadCategories() {
    try {
      const resp = await fetch(CATEGORIES_PATH, { cache: "no-store" });
      if (!resp.ok) throw new Error("Could not load categories.json");
      const json = await resp.json();
      return json || {};
    } catch (err) {
      console.warn(
        "Could not load categories.json — will compute locally",
        err
      );
      return null;
    }
  }

  async function loadFavoritesList() {
    // try favorites.json first
    try {
      const resp = await fetch(FAVORITES_JSON, { cache: "no-store" });
      if (resp.ok) {
        const json = await resp.json();
        if (Array.isArray(json.favorites)) return json.favorites;
      }
    } catch (e) {
      // ignore; fallback to INLINE_FAVORITES
    }
    // fallback to inline list
    return INLINE_FAVORITES || [];
  }

  // category state
  let categories = { desktop: [] };
  let selectedCategory = "all";

  /**
   * Render category chips, ordering by count (high -> low).
   * Keeps "All" as the first chip.
   */
  async function renderCategoryChips() {
    if (!chipsContainer) return;
    chipsContainer.innerHTML = "";

    // Use a shallow copy so we don't mutate original categories.desktop array
    const rawList =
      categories.desktop && categories.desktop.length
        ? categories.desktop.slice()
        : [{ name: "all", label: "All", count: data.length }];

    // Extract 'all' (if present), otherwise create it
    let allItem = null;
    const allIndex = rawList.findIndex((c) => c.name === "all");
    if (allIndex === -1) {
      allItem = { name: "all", label: "All", count: data.length };
    } else {
      allItem = rawList.splice(allIndex, 1)[0];
      // make sure its count matches data length if count missing/zero
      if (!allItem.count) allItem.count = data.length;
    }

    // Sort remaining categories by count desc, then by label/name as tiebreaker
    const others = rawList.slice().sort((a, b) => {
      const ca = a.count || 0;
      const cb = b.count || 0;
      if (cb !== ca) return cb - ca; // high -> low
      const la = (a.label || a.name || "").toString();
      const lb = (b.label || b.name || "").toString();
      return la.localeCompare(lb);
    });

    // Append 'All' first
    const isActiveAll = allItem.name === selectedCategory;
    chipsContainer.appendChild(
      buildChip(
        allItem.name,
        allItem.label || allItem.name,
        allItem.count || 0,
        isActiveAll
      )
    );

    // Then append the sorted others
    others.forEach((c) => {
      const isActive = c.name === selectedCategory;
      chipsContainer.appendChild(
        buildChip(c.name, c.label || c.name, c.count || 0, isActive)
      );
    });

    // update nav visibility
    requestAnimationFrame(showHideChipNav);
  }

  async function init() {
    const catObj = await loadCategories();
    if (catObj) categories = catObj;

    const all = await loadWallpapers();

    if (MODE === "all") {
      data = all.slice();
      // default newest first
      data.sort((a, b) => new Date(b.modified) - new Date(a.modified));
      filtered = data.slice();
      selectedCategory = "all";
      renderCategoryChips();
      renderSummary();
      renderGrid(filtered);
      // ensure chip nav configured
      requestAnimationFrame(showHideChipNav);
      // set download button to global asset (no per-category)
      // (fetchReleaseAssetAndSetButton already called on load)
    } else if (MODE === "favorites") {
      const favList = await loadFavoritesList();
      if (!favList.length) {
        data = [];
        filtered = [];
        renderSummary();
        renderGrid(filtered);
        renderCategoryChips();
        return;
      }
      const lookup = new Map(all.map((i) => [i.filename, i]));
      const favEntries = [];
      favList.forEach((name) => {
        if (lookup.has(name)) favEntries.push(lookup.get(name));
      });
      data = favEntries;
      filtered = data.slice();

      // compute categories from favorites and sort by count desc
      const counts = {};
      data.forEach((it) => {
        const c = it.category || "uncategorized";
        counts[c] = (counts[c] || 0) + 1;
      });

      // Build categories.desktop: "All" first, then entries sorted by count desc
      const entries = Object.keys(counts).map((k) => ({
        name: k,
        label: k,
        count: counts[k],
      }));

      entries.sort((a, b) => {
        if (b.count !== a.count) return b.count - a.count;
        return (a.name || "").localeCompare(b.name || "");
      });

      categories.desktop = [
        { name: "all", label: "All", count: data.length },
      ].concat(entries);

      selectedCategory = "all";
      renderCategoryChips();
      renderSummary();
      renderGrid(filtered);
    }

    // ensure chip nav reacts to DOM sizes
    requestAnimationFrame(showHideChipNav);
  }

  // events
  if (searchInput)
    searchInput.addEventListener("input", () => applySearchSort());
  sortOptions.forEach((opt) =>
    opt.addEventListener("click", (e) => {
      e.preventDefault();
      applySortMode(opt.getAttribute("data-sort"));
    })
  );

  // init
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
