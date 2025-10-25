// js/scripts.js - gallery renderer used by index.html and favorites.html
(() => {
  const JSON_PATH = "json/wallpapers.json";
  const FAVORITES_JSON = "json/favorites.json";
  const galleryEl = document.getElementById("gallery");
  const summaryEl = document.getElementById("summary");
  const emptyState = document.getElementById("emptyState");
  const searchInput = document.getElementById("searchInput");
  const sortOptions = document.querySelectorAll(".sort-option");
  const downloadAllBtn = document.getElementById("downloadAllBtn");
  const animatedEl = document.getElementById("animatedText");

  // GITHUB RELEASES CONFIG
  const GITHUB_OWNER = "fahim-foysal-097";
  const GITHUB_REPO = "wallpapers";
  const TAG_PREFIX = "wallpaper-archive-";
  const CACHE_TTL_MS = 10 * 60 * 1000; // 10 minutes cache

  // set downloadAll link if present (will be replaced after checking releases)
  if (downloadAllBtn) {
    // keep default as fallback, but show fetching state
    const originalHref = downloadAllBtn.href || "wallpaper-all.zip";
    downloadAllBtn.dataset.fallback = originalHref;
    // show loading state
    downloadAllBtn.classList.add("disabled");
    downloadAllBtn.setAttribute("aria-disabled", "true");
    downloadAllBtn.innerHTML = `<i class="bi bi-hourglass-split"></i>&nbsp;Checking latest...`;
    // asynchronously resolve to release asset
    fetchReleaseAssetAndSetButton("wallpaper-all.zip", downloadAllBtn);
  }

  /**
   * getLatestReleaseAsset(assetName)
   * - Looks up GitHub releases for this repo and returns the browser_download_url for the first matching asset
   * - Uses localStorage caching to reduce API requests
   */
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
          // cache and return
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
    // try to get the release asset URL
    try {
      const url = await getLatestReleaseAsset(assetName);
      if (url) {
        btnEl.href = url;
        btnEl.setAttribute("download", assetName);
        btnEl.classList.remove("disabled");
        btnEl.removeAttribute("aria-disabled");
        btnEl.innerHTML = `<i class="bi bi-file-earmark-zip-fill"></i>&nbsp;Download All (latest)`;
        btnEl.title = `Download ${assetName} from latest release`;
        return;
      }
    } catch (e) {
      console.warn("Error while resolving release asset:", e);
    }

    // fallback to local path if release not found
    const fallback = btnEl.dataset.fallback || `/${assetName}`;
    btnEl.href = fallback;
    btnEl.setAttribute("download", assetName);
    btnEl.classList.remove("disabled");
    btnEl.removeAttribute("aria-disabled");
    btnEl.innerHTML = `<i class="bi bi-file-earmark-zip-fill"></i>&nbsp;Download All`;
    btnEl.title = "Download all desktop wallpapers";
  }

  // runtime mode: "all" or "favorites"
  const MODE = window.GALLERY_MODE === "favorites" ? "favorites" : "all";
  const INLINE_FAVORITES = Array.isArray(window.FAVORITES)
    ? window.FAVORITES
    : [];

  let data = [];
  let filtered = [];

  // modal elements and navigation
  const previewModalEl = document.getElementById("previewModal");
  const modal = previewModalEl ? new bootstrap.Modal(previewModalEl) : null;
  const modalImage = document.getElementById("modalImage");
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

  /* -------------------- Typing animation -------------------- */
  // Animates text switching between phrases
  (function initTyping() {
    if (!animatedEl) return;
    const original =
      animatedEl.textContent.trim() || "Discover Beautiful Wallpapers";
    const alt = "Download Wallpapers";
    const alt2 = "If you want to add wallpapers, go to the github repository";
    const phrases = [original, alt, alt2];
    const typingSpeed = 60; // ms per char
    const deletingSpeed = 40;
    const pauseAfterTyping = 1200; // ms
    const pauseAfterDeleting = 350; // ms

    let phraseIndex = 0;
    let charIndex = 0;
    let mode = "typing"; // "typing" | "deleting"
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
          // switch phrase
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
        // initial start
        mode = "typing";
        charIndex = 0;
        timeoutId = setTimeout(step, typingSpeed);
      }
    }

    // start after small delay for smoothness
    timeoutId = setTimeout(step, 700);
  })();

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

  /* -------------------- Modal navigation -------------------- */

  function openPreviewAtIndex(idx) {
    if (!Array.isArray(filtered) || idx < 0 || idx >= filtered.length) return;
    currentIndex = idx;
    showImageAt(currentIndex);
    if (modal) modal.show();
  }

  function showImageAt(idx) {
    const item = filtered[idx];
    if (!item) return;
    if (modalImage) {
      modalImage.src = item.url;
      modalImage.alt = item.filename;
    }
    if (modalFilename) modalFilename.textContent = item.filename;
    if (modalMeta)
      modalMeta.textContent = `${new Date(
        item.modified
      ).toLocaleString()} • ${humanSize(item.size)}`;
    if (modalDownload) {
      modalDownload.href = item.url;
      modalDownload.setAttribute("download", item.filename);
    }
    // update nav visibility (if at edges)
    if (modalPrevBtn) modalPrevBtn.disabled = idx <= 0;
    if (modalNextBtn) modalNextBtn.disabled = idx >= filtered.length - 1;
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

  // track modal show/hide to enable keyboard arrows only when modal visible
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
      // let bootstrap handle escape to close modal
    }
  });

  /* -------------------- Sorting, searching, loading -------------------- */

  function applySearchSort() {
    const q =
      searchInput && searchInput.value
        ? searchInput.value.trim().toLowerCase()
        : "";
    filtered = data.filter((it) => {
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

  async function init() {
    const all = await loadWallpapers();

    if (MODE === "all") {
      data = all.slice();
      // default newest first
      data.sort((a, b) => new Date(b.modified) - new Date(a.modified));
      filtered = data.slice();
      renderSummary();
      renderGrid(filtered);
    } else if (MODE === "favorites") {
      const favList = await loadFavoritesList();
      if (!favList.length) {
        data = [];
        filtered = [];
        renderSummary();
        renderGrid(filtered);
        return;
      }
      const lookup = new Map(all.map((i) => [i.filename, i]));
      const favEntries = [];
      favList.forEach((name) => {
        if (lookup.has(name)) favEntries.push(lookup.get(name));
      });
      data = favEntries;
      filtered = data.slice();
      renderSummary();
      renderGrid(filtered);
    }
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

  // initialize
  init();
})();
