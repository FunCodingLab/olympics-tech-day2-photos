/**
 * PhotoGallery Controller
 * Manages the thumbnail grid, lightbox modal, filmstrip navigation,
 * autoplay slideshow with top progress bar, and metadata side panel.
 */
class PhotoGallery {
  constructor(manifestUrl, slideDurationMs = 4000) {
    this.manifestUrl = manifestUrl;
    this.slideDurationMs = slideDurationMs;
    this.photos = [];
    this.currentIndex = 0;
    this.isOpen = false;
    this.isPlaying = false;

    this.rafId = null;
    this.slideStartTime = null;
    this.touchStartX = 0;

    this.cacheDomElements();
    this.bindEvents();
  }

  cacheDomElements() {
    this.gridEl = document.getElementById("gallery-grid");
    this.lightboxEl = document.getElementById("lightbox");
    this.counterEl = document.getElementById("lightbox-counter");
    this.stageImgEl = document.getElementById("lightbox-img");
    this.stageLoaderEl = document.getElementById("stage-loader");
    this.filmstripWrapperEl = document.getElementById("filmstrip-wrapper");
    this.filmstripEl = document.getElementById("filmstrip");

    this.progressContainerEl = document.getElementById("autoplay-progress-container");
    this.progressBarEl = document.getElementById("autoplay-progress-bar");

    this.btnPlay = document.getElementById("btn-play");
    this.iconPlay = document.getElementById("icon-play");
    this.iconPause = document.getElementById("icon-pause");
    this.btnDownload = document.getElementById("btn-download");
    this.btnInfo = document.getElementById("btn-info");
    this.btnClose = document.getElementById("btn-close");
    this.btnPrev = document.getElementById("btn-prev");
    this.btnNext = document.getElementById("btn-next");
    this.btnToggleThumbs = document.getElementById("btn-toggle-thumbs");

    this.infoSidebarEl = document.getElementById("info-sidebar");
    this.btnCloseInfo = document.getElementById("btn-close-info");
    this.infoFilenameEl = document.getElementById("info-filename");
    this.infoSizeEl = document.getElementById("info-size");
  }

  async init() {
    try {
      const response = await fetch(this.manifestUrl);
      if (!response.ok) {
        throw new Error(`Failed to fetch manifest (${response.status})`);
      }
      this.photos = await response.json();
      this.renderGrid();
      this.renderFilmstrip();
      this.checkInitialHash();
    } catch (error) {
      console.error("Error initializing gallery:", error);
      this.gridEl.innerHTML = "<p>Unable to load gallery photos.</p>";
    }
  }

  renderGrid() {
    const fragment = document.createDocumentFragment();
    this.photos.forEach((photo, index) => {
      const item = document.createElement("div");
      item.className = "grid-item";
      item.dataset.index = index;

      const img = document.createElement("img");
      img.src = photo.thumb;
      img.alt = photo.filename;
      img.loading = "lazy";
      img.decoding = "async";

      item.appendChild(img);
      fragment.appendChild(item);
    });
    this.gridEl.appendChild(fragment);
  }

  renderFilmstrip() {
    const fragment = document.createDocumentFragment();
    this.filmstripItems = [];

    this.photos.forEach((photo, index) => {
      const item = document.createElement("div");
      item.className = "filmstrip-item";
      item.dataset.index = index;

      const img = document.createElement("img");
      img.src = photo.thumb;
      img.alt = photo.filename;
      img.loading = "lazy";
      img.decoding = "async";

      item.appendChild(img);
      fragment.appendChild(item);
      this.filmstripItems.push(item);
    });

    this.filmstripEl.appendChild(fragment);
  }

  bindEvents() {
    this.gridEl.addEventListener("click", (event) => {
      const item = event.target.closest(".grid-item");
      if (item) {
        this.openLightbox(Number(item.dataset.index));
      }
    });

    this.filmstripEl.addEventListener("click", (event) => {
      const item = event.target.closest(".filmstrip-item");
      if (item) {
        this.showPhoto(Number(item.dataset.index));
      }
    });

    this.btnClose.addEventListener("click", () => this.closeLightbox());
    this.btnPrev.addEventListener("click", () => this.prevPhoto());
    this.btnNext.addEventListener("click", () => this.nextPhoto());
    this.btnPlay.addEventListener("click", () => this.toggleAutoplay());

    this.btnToggleThumbs.addEventListener("click", () => {
      this.filmstripWrapperEl.classList.toggle("collapsed");
    });

    this.btnInfo.addEventListener("click", () => this.toggleInfoSidebar());
    this.btnCloseInfo.addEventListener("click", () => this.toggleInfoSidebar(false));

    document.addEventListener("keydown", (event) => {
      if (!this.isOpen) return;

      switch (event.key) {
        case "Escape":
          this.closeLightbox();
          break;
        case "ArrowLeft":
          this.prevPhoto();
          break;
        case "ArrowRight":
          this.nextPhoto();
          break;
        case " ":
          event.preventDefault();
          this.toggleAutoplay();
          break;
        case "i":
        case "I":
          this.toggleInfoSidebar();
          break;
      }
    });

    this.stageImgEl.addEventListener("touchstart", (event) => {
      this.touchStartX = event.changedTouches[0].screenX;
    }, { passive: true });

    this.stageImgEl.addEventListener("touchend", (event) => {
      const deltaX = event.changedTouches[0].screenX - this.touchStartX;
      if (Math.abs(deltaX) > 50) {
        if (deltaX < 0) {
          this.nextPhoto();
        } else {
          this.prevPhoto();
        }
      }
    }, { passive: true });

    window.addEventListener("hashchange", () => this.checkInitialHash());
  }

  checkInitialHash() {
    const match = window.location.hash.match(/^#photo=(\d+)$/);
    if (match) {
      const idx = parseInt(match[1], 10) - 1;
      if (idx >= 0 && idx < this.photos.length) {
        this.openLightbox(idx, false);
      }
    } else if (this.isOpen) {
      this.closeLightbox(false);
    }
  }

  openLightbox(index, updateHash = true) {
    this.isOpen = true;
    document.body.classList.add("no-scroll");
    this.lightboxEl.classList.remove("hidden");
    this.showPhoto(index, updateHash);
  }

  closeLightbox(updateHash = true) {
    this.stopAutoplay();
    this.isOpen = false;
    document.body.classList.remove("no-scroll");
    this.lightboxEl.classList.add("hidden");

    if (updateHash && window.location.hash) {
      history.pushState("", document.title, window.location.pathname + window.location.search);
    }
  }

  showPhoto(index, updateHash = true) {
    if (index < 0 || index >= this.photos.length) return;

    const prevIndex = this.currentIndex;
    this.currentIndex = index;
    const photo = this.photos[index];

    if (updateHash) {
      history.replaceState(null, "", `#photo=${index + 1}`);
    }

    this.counterEl.textContent = `${index + 1} / ${this.photos.length}`;
    this.btnDownload.href = photo.download_url;
    this.btnDownload.setAttribute("download", photo.filename);

    this.infoFilenameEl.textContent = photo.filename;
    this.infoSizeEl.textContent = photo.size;

    if (this.filmstripItems[prevIndex]) {
      this.filmstripItems[prevIndex].classList.remove("active");
    }
    const activeThumb = this.filmstripItems[index];
    if (activeThumb) {
      activeThumb.classList.add("active");
      this.scrollThumbIntoView(activeThumb);
    }

    this.loadStageImage(photo.large);
    this.preloadAdjacentImages(index);
  }

  loadStageImage(src) {
    this.cancelProgressAnimation();
    this.progressBarEl.style.width = "0%";
    this.stageLoaderEl.classList.remove("hidden");
    this.stageImgEl.style.opacity = "0.35";

    const imgLoader = new Image();
    imgLoader.onload = () => {
      if (this.photos[this.currentIndex]?.large !== src) return;
      this.stageImgEl.src = src;
      this.stageImgEl.alt = this.photos[this.currentIndex].filename;
      this.stageImgEl.style.opacity = "1";
      this.stageLoaderEl.classList.add("hidden");

      if (this.isPlaying) {
        this.startSlideTimer();
      }
    };
    imgLoader.onerror = () => {
      this.stageLoaderEl.classList.add("hidden");
      this.stageImgEl.style.opacity = "1";
    };
    imgLoader.src = src;
  }

  preloadAdjacentImages(index) {
    const nextIdx = (index + 1) % this.photos.length;
    const prevIdx = (index - 1 + this.photos.length) % this.photos.length;

    [nextIdx, prevIdx].forEach((idx) => {
      const preloadImg = new Image();
      preloadImg.src = this.photos[idx].large;
    });
  }

  scrollThumbIntoView(thumbEl) {
    const containerWidth = this.filmstripEl.clientWidth;
    const thumbLeft = thumbEl.offsetLeft;
    const thumbWidth = thumbEl.offsetWidth;
    const targetScroll = thumbLeft - containerWidth / 2 + thumbWidth / 2;

    this.filmstripEl.scrollTo({
      left: targetScroll,
      behavior: "smooth",
    });
  }

  prevPhoto() {
    const targetIndex =
      this.currentIndex > 0 ? this.currentIndex - 1 : this.photos.length - 1;
    this.showPhoto(targetIndex);
  }

  nextPhoto() {
    const targetIndex =
      this.currentIndex < this.photos.length - 1 ? this.currentIndex + 1 : 0;
    this.showPhoto(targetIndex);
  }

  toggleAutoplay() {
    if (this.isPlaying) {
      this.stopAutoplay();
    } else {
      this.startAutoplay();
    }
  }

  startAutoplay() {
    this.isPlaying = true;
    this.iconPlay.classList.add("hidden");
    this.iconPause.classList.remove("hidden");
    this.progressContainerEl.classList.remove("hidden");
    this.startSlideTimer();
  }

  stopAutoplay() {
    this.isPlaying = false;
    this.iconPlay.classList.remove("hidden");
    this.iconPause.classList.add("hidden");
    this.progressContainerEl.classList.add("hidden");
    this.cancelProgressAnimation();
    this.progressBarEl.style.width = "0%";
  }

  startSlideTimer() {
    this.cancelProgressAnimation();
    this.slideStartTime = performance.now();

    const step = (now) => {
      if (!this.isPlaying) return;
      const elapsed = now - this.slideStartTime;
      const percentage = Math.min((elapsed / this.slideDurationMs) * 100, 100);
      this.progressBarEl.style.width = `${percentage}%`;

      if (elapsed >= this.slideDurationMs) {
        this.nextPhoto();
      } else {
        this.rafId = requestAnimationFrame(step);
      }
    };

    this.rafId = requestAnimationFrame(step);
  }

  cancelProgressAnimation() {
    if (this.rafId !== null) {
      cancelAnimationFrame(this.rafId);
      this.rafId = null;
    }
  }

  toggleInfoSidebar(forceState) {
    const shouldShow =
      typeof forceState === "boolean"
        ? forceState
        : this.infoSidebarEl.classList.contains("hidden");

    this.infoSidebarEl.classList.toggle("hidden", !shouldShow);

    setTimeout(() => {
      const activeThumb = this.filmstripItems[this.currentIndex];
      if (activeThumb) {
        this.scrollThumbIntoView(activeThumb);
      }
    }, 50);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const gallery = new PhotoGallery("media/photos.json", 4000);
  gallery.init();
});