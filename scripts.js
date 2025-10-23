// scripts.js
(() => {
  const JSON_PATH = "wallpapers.json";
  const galleryEl = document.getElementById("gallery");
  const summaryEl = document.getElementById("summary");
  const emptyState = document.getElementById("emptyState");
  const searchInput = document.getElementById("searchInput");
  const sortOptions = document.querySelectorAll(".sort-option");
  const downloadAllBtn = document.getElementById("downloadAllBtn");

  // set downloadAll link (assumes a zip at repo root named wallpaper-all.zip)
  if (downloadAllBtn) {
    downloadAllBtn.href = "wallpaper-all.zip";
    downloadAllBtn.setAttribute("download", "wallpaper-all.zip");
  }

  let data = [];
  let filtered = [];

  // modal elements
  const previewModalEl = document.getElementById("previewModal");
  const modal = new bootstrap.Modal(previewModalEl);
  const modalImage = document.getElementById("modalImage");
  const modalFilename = document.getElementById("modalFilename");
  const modalMeta = document.getElementById("modalMeta");
  const modalDownload = document.getElementById("modalDownload");

  function humanSize(n) {
    if (n < 1024) return n + " B";
    if (n < 1024 * 1024) return (n / 1024).toFixed(1) + " KB";
    if (n < 1024 * 1024 * 1024) return (n / 1024 / 1024).toFixed(1) + " MB";
    return (n / 1024 / 1024 / 1024).toFixed(2) + " GB";
  }

  function renderSummary() {
    summaryEl.textContent = `${filtered.length} wallpaper${
      filtered.length !== 1 ? "s" : ""
    }`;
  }

  function clearGallery() {
    galleryEl.innerHTML = "";
  }

  function makeTile(item) {
    const col = document.createElement("div");
    col.className = "col-6 col-sm-4 col-md-3 col-xl-2";

    const tile = document.createElement("div");
    tile.className = "tile";

    const img = document.createElement("img");
    img.className = "thumb";
    img.loading = "lazy";
    img.decoding = "async";
    img.alt = item.filename;
    img.src = item.url;

    img.onerror = () => {
      img.src =
        "data:image/svg+xml;charset=UTF-8," +
        encodeURIComponent(
          `<svg xmlns='http://www.w3.org/2000/svg' width='600' height='400'><rect fill='#0b1220' width='100%' height='100%'/><text x='50%' y='50%' fill='#666' dominant-baseline='middle' text-anchor='middle' font-size='18'>Image not available</text></svg>`
        );
    };

    img.addEventListener("click", () => openPreview(item));

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

    tile.appendChild(img);
    tile.appendChild(footer);
    col.appendChild(tile);

    return col;
  }

  function renderGrid(items) {
    clearGallery();
    if (!items.length) {
      emptyState.style.display = "";
      return;
    } else {
      emptyState.style.display = "none";
    }
    const frag = document.createDocumentFragment();
    items.forEach((it) => frag.appendChild(makeTile(it)));
    galleryEl.appendChild(frag);
  }

  function openPreview(item) {
    modalImage.src = item.url;
    modalFilename.textContent = item.filename;
    modalMeta.textContent = `${new Date(
      item.modified
    ).toLocaleString()} • ${humanSize(item.size)}`;
    modalDownload.href = item.url;
    modalDownload.setAttribute("download", item.filename);
    modal.show();
  }

  function applySearchSort() {
    const q = searchInput.value.trim().toLowerCase();
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

  async function init() {
    try {
      const resp = await fetch(JSON_PATH, { cache: "no-store" });
      if (!resp.ok) throw new Error("Could not load wallpapers.json");
      const json = await resp.json();
      data = json.wallpapers || [];
      data.sort((a, b) => new Date(b.modified) - new Date(a.modified));
      filtered = data.slice();
      renderSummary();
      renderGrid(filtered);
    } catch (err) {
      summaryEl.textContent = "Failed to load wallpapers.json";
      console.error(err);
      emptyState.style.display = "";
    }
  }

  searchInput.addEventListener("input", () => applySearchSort());
  sortOptions.forEach((opt) =>
    opt.addEventListener("click", (e) => {
      e.preventDefault();
      applySortMode(opt.getAttribute("data-sort"));
    })
  );

  init();
})();
