/**
 * Cinema Player — client logic
 * Plyr, reconnect, local/online subs, audio tracks, gestures, lock, i18n (es default).
 * Icons are inlined in HTML (Reicon SVGs) — no icon package at runtime.
 */
(function () {
  "use strict";

  const STRINGS = {
    es: {
      brand: "CinemaLibrary",
      download: "Descargar",
      subtitles: "Subtítulos",
      audio: "Audio",
      streaming: "Streaming",
      volume: "Volumen",
      brightness: "Brillo",
      lock: "Bloquear",
      unlock: "Desbloquear",
      sheetSubs: "Subtítulos",
      sheetAudio: "Pista de audio",
      searchPlaceholder: "Título, película o serie…",
      search: "Buscar",
      uploadSub: "Añadir archivo",
      pickSub: "Elige un subtítulo…",
      searching: "Buscando subtítulos…",
      downloading: "Descargando subtítulo…",
      noSubs: "No se encontraron subtítulos. Prueba con otro título.",
      searchError: "Error buscando subtítulos. Intenta de nuevo.",
      downloadError: "No se pudo descargar ese subtítulo. Prueba con otro.",
      subLoaded: "Subtítulo cargado",
      reconnecting: "Reconectando…",
      loading: "Cargando…",
      reconnectFail:
        "No se pudo reconectar. Revisa tu conexión y recarga la página.",
      formatUnsupported:
        "Este navegador no puede reproducir este archivo. Prueba un MP4 (H.264 + AAC).",
      formatDecode:
        "No se pudo decodificar el video. Prueba un MP4 (H.264 + AAC).",
      attempt: "intento",
      audioPick: "Elegir pista de audio",
      audioNote:
        "Tu navegador no expone varias pistas de audio. Ábrelo en VLC o MX Player para elegir el audio.",
      quality: "Calidad",
      speed: "Velocidad",
      captions: "Subtítulos",
      disabled: "Desactivado",
      enabled: "Activado",
    },
    en: {
      brand: "CinemaLibrary",
      download: "Download",
      subtitles: "Subtitles",
      audio: "Audio",
      streaming: "Streaming",
      volume: "Volume",
      brightness: "Brightness",
      lock: "Lock",
      unlock: "Unlock",
      sheetSubs: "Subtitles",
      sheetAudio: "Audio track",
      searchPlaceholder: "Title, movie, or show…",
      search: "Search",
      uploadSub: "Add file",
      pickSub: "Choose a subtitle…",
      searching: "Searching subtitles…",
      downloading: "Downloading subtitle…",
      noSubs: "No subtitles found. Try another title.",
      searchError: "Could not search subtitles. Try again.",
      downloadError: "Could not download that subtitle. Try another.",
      subLoaded: "Subtitle loaded",
      reconnecting: "Reconnecting…",
      loading: "Loading…",
      reconnectFail: "Could not reconnect. Check your connection and reload.",
      formatUnsupported:
        "This browser cannot play this file. Try an MP4 (H.264 + AAC).",
      formatDecode: "Could not decode the video. Try an MP4 (H.264 + AAC).",
      attempt: "attempt",
      audioPick: "Choose audio track",
      audioNote:
        "Your browser does not expose multiple audio tracks. Open in VLC or MX Player to pick audio.",
      quality: "Quality",
      speed: "Speed",
      captions: "Captions",
      disabled: "Disabled",
      enabled: "Enabled",
    },
  };

  /* ---------- Shared timing / gesture constants (no magic values) ---------- */
  const SEEK_STEP_S = 10;
  const DOUBLE_TAP_MS = 320;
  const LONG_PRESS_MS = 450;
  const TAP_MOVE_MAX_PX = 14;
  const DOUBLE_TAP_DIST_PX = 64;
  const SWIPE_DOWN_MIN_PX = 100;
  const VERTICAL_LOCK_PX = 14;
  const AXIS_DOMINANCE = 1.05;
  const SWIPE_AXIS_DOMINANCE = 1.2;
  const TOP_EDGE_RATIO = 0.12;
  const BRIGHTNESS_MIN = 0.35;
  const BRIGHTNESS_MAX = 1.45;
  const BRIGHTNESS_DEFAULT = 1;
  const HOLD_SPEED = 2;
  const UNMUTE_VOLUME_FLOOR = 0.01;
  const SEEK_FLASH_MS = 520;
  const LEVEL_HIDE_MS = 500;
  const SUBTITLE_SHOW_DELAY_MS = 300;
  const UPLOAD_SUCCESS_MS = 2800;
  const SUB_STATUS_OK_MS = 2500;
  const SHEET_CLOSE_FALLBACK_MS = 280;
  const SHEET_SCROLL_DELAY_MS = 40;
  const LOADING_OVERLAY_DELAY_MS = 450;
  const STALL_RECONNECT_MS = 30000;
  const MAX_RECONNECT_ATTEMPTS = 6;
  const RECONNECT_BASE_MS = 1000;
  const RECONNECT_GROWTH = 1.6;
  const RECONNECT_MAX_MS = 12000;
  const SCROLL_BORDER_PX = 2;
  const VIBRATE_MS = 10;
  const HAVE_FUTURE_DATA = 3;
  const LOCK_CHROME_MS = 3000;

  function detectLang() {
    const forced = document.documentElement.dataset.lang;
    if (forced && STRINGS[forced]) return forced;
    const nav = (navigator.language || "es").slice(0, 2).toLowerCase();
    return STRINGS[nav] ? nav : "es";
  }

  const lang = detectLang();
  const t = STRINGS[lang];

  function applyI18n() {
    document.querySelectorAll("[data-i18n]").forEach((el) => {
      const key = el.getAttribute("data-i18n");
      if (t[key] != null) el.textContent = t[key];
    });
    document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
      const key = el.getAttribute("data-i18n-placeholder");
      if (t[key] != null) el.setAttribute("placeholder", t[key]);
    });
    document.querySelectorAll("[data-i18n-aria]").forEach((el) => {
      const key = el.getAttribute("data-i18n-aria");
      if (t[key] != null) el.setAttribute("aria-label", t[key]);
    });
  }

  function readConfig() {
    const node = document.getElementById("player-config");
    if (!node) return {};
    try {
      return JSON.parse(node.textContent || "{}");
    } catch (_) {
      return {};
    }
  }

  /**
   * Minimal SRT → WebVTT so browsers can load uploaded .srt as TextTrack.
   * Already-VTT input is returned with a WEBVTT header if missing.
   */
  function srtToVtt(text) {
    const raw = String(text || "").replace(/^\uFEFF/, "").trim();
    if (!raw) return "WEBVTT\n\n";
    if (/^WEBVTT/i.test(raw)) return raw.endsWith("\n") ? raw : raw + "\n";

    const body = raw
      .replace(/\r\n/g, "\n")
      .replace(/\r/g, "\n")
      // SRT uses comma for fractional seconds; VTT uses a dot.
      .replace(
        /(\d{2}:\d{2}:\d{2}),(\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}),(\d{3})/g,
        "$1.$2 --> $3.$4"
      );

    return "WEBVTT\n\n" + body + "\n";
  }

  function boot() {
    applyI18n();

    const config = readConfig();
    const video = document.getElementById("player");
    const source = document.getElementById("player-source");
    const overlay = document.getElementById("reconnect-overlay");
    const overlayText = document.getElementById("reconnect-text");
    const topbar = document.querySelector(".topbar");
    const audioSelector = document.getElementById("audio-track-selector");
    const audioPanel = document.getElementById("audio-tracks-panel");
    const audioNote = document.getElementById("audio-track-note");
    let hasMultiAudio = false;

    if (!video || !source) return;

    if (topbar) {
      const onScroll = () => {
        topbar.classList.toggle(
          "is-scrolled",
          window.scrollY > SCROLL_BORDER_PX
        );
      };
      window.addEventListener("scroll", onScroll, { passive: true });
      onScroll();
    }

    const player = new Plyr(video, {
      captions: { active: true, update: true, language: "auto" },
      seekTime: SEEK_STEP_S,
      clickToPlay: false,
      // We own show/hide via single-tap toggle — disable Plyr's auto-hide
      // (it was racing us and flashing the bar on/off).
      hideControls: false,
      keyboard: { focused: true, global: true },
      fullscreen: {
        enabled: true,
        fallback: true,
        iosNative: false,
        container: null,
      },
      controls: [
        "play-large",
        "play",
        "progress",
        "current-time",
        "mute",
        "volume",
        "captions",
        "settings",
        "fullscreen",
      ],
      i18n: {
        quality: t.quality,
        speed: t.speed,
        captions: t.captions,
        disabled: t.disabled,
        enabled: t.enabled,
      },
    });

    /* ---------- Gestures + lock (mounted inside .plyr so FS works) ---------- */
    let uiLocked = false;
    let brightness = BRIGHTNESS_DEFAULT;
    let flashTimer = null;
    let levelHideTimer = null;
    let longTimer = null;
    let longActive = false;
    let speedBeforeHold = 1;
    let pendingTapTimer = null;
    let pendingTapToken = 0;
    let lastTapAt = 0;
    let lastTapX = 0;
    let lastTapY = 0;
    let pointerId = null;
    let startX = 0;
    let startY = 0;
    let movedFar = false;
    let dragMode = null; // null | 'volume' | 'brightness'
    let dragOriginVolume = 1;
    let dragOriginBrightness = BRIGHTNESS_DEFAULT;
    // Explicit latch: tap shows and stays; next tap hides. Don't trust Plyr timers.
    let controlsOpen = false;
    let hitEl = null;
    let gesturesMounted = false;
    let lockControlBtn = null;
    let lockPeekBtn = null;
    let lockChromeTimer = null;

    const gestureUi = document.querySelector("[data-gesture-ui]");
    const flashLeft = document.querySelector('[data-seek-flash="left"]');
    const flashRight = document.querySelector('[data-seek-flash="right"]');
    const speedBadge = document.querySelector("[data-speed-badge]");
    const levelBrightness = document.querySelector(
      '[data-level-badge="brightness"]'
    );
    const levelVolume = document.querySelector('[data-level-badge="volume"]');

    function mediaEl() {
      return (
        (player.media && player.media.nodeName === "VIDEO" && player.media) ||
        video
      );
    }

    function applyBrightness(value) {
      brightness = Math.min(BRIGHTNESS_MAX, Math.max(BRIGHTNESS_MIN, value));
      const el = mediaEl();
      if (el) el.style.filter = `brightness(${brightness})`;
      const wrap =
        player.elements &&
        player.elements.container &&
        player.elements.container.querySelector(".plyr__video-wrapper");
      if (wrap) wrap.style.filter = `brightness(${brightness})`;
    }
    applyBrightness(BRIGHTNESS_DEFAULT);

    function setControlsOpen(open) {
      if (uiLocked && open) return;
      controlsOpen = Boolean(open);
      try {
        player.toggleControls(controlsOpen);
      } catch (_) {}
      const c = player.elements && player.elements.container;
      if (c) {
        c.classList.toggle("plyr--hide-controls", !controlsOpen);
      }
    }

    function hideControlsNow() {
      setControlsOpen(false);
    }

    function showControlsNow() {
      setControlsOpen(true);
    }

    function showSeekFlash(side) {
      const el = side === "left" ? flashLeft : flashRight;
      if (!el) return;
      if (flashLeft) flashLeft.classList.remove("is-on");
      if (flashRight) flashRight.classList.remove("is-on");
      void el.offsetWidth;
      el.classList.add("is-on");
      clearTimeout(flashTimer);
      flashTimer = setTimeout(
        () => el.classList.remove("is-on"),
        SEEK_FLASH_MS
      );
    }

    function seekBy(delta) {
      const duration = Number.isFinite(player.duration) ? player.duration : 0;
      let next = (player.currentTime || 0) + delta;
      if (duration > 0) next = Math.max(0, Math.min(duration, next));
      else next = Math.max(0, next);
      player.currentTime = next;
      showSeekFlash(delta < 0 ? "left" : "right");
    }

    function setSpeedBadge(on) {
      if (speedBadge) speedBadge.classList.toggle("is-on", on);
    }

    function levelEl(kind) {
      return kind === "volume" ? levelVolume : levelBrightness;
    }

    function showLevel(kind, ratio01) {
      const el = levelEl(kind);
      if (!el) return;
      const pct = Math.round(Math.min(1, Math.max(0, ratio01)) * 100);
      const other = kind === "volume" ? levelBrightness : levelVolume;
      if (other) {
        other.classList.remove("is-on");
        other.hidden = true;
      }
      const kindNode = el.querySelector("[data-level-kind]");
      const valueNode = el.querySelector("[data-level-value]");
      const fillNode = el.querySelector("[data-level-fill]");
      if (kindNode) {
        kindNode.textContent = kind === "volume" ? t.volume : t.brightness;
      }
      if (valueNode) valueNode.textContent = `${pct}%`;
      if (fillNode) fillNode.style.height = `${pct}%`;
      el.hidden = false;
      void el.offsetWidth;
      el.classList.add("is-on");
      clearTimeout(levelHideTimer);
    }

    function hideLevelSoon() {
      clearTimeout(levelHideTimer);
      levelHideTimer = setTimeout(() => {
        [levelBrightness, levelVolume].forEach((el) => {
          if (!el) return;
          el.classList.remove("is-on");
          el.hidden = true;
        });
      }, LEVEL_HIDE_MS);
    }

    function lockIconHtml() {
      const tpl = document.getElementById("tpl-icon-lock");
      if (tpl && tpl.content && tpl.content.firstElementChild) {
        return tpl.content.firstElementChild.outerHTML;
      }
      return (
        '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">' +
        '<rect x="5" y="11" width="14" height="10" rx="2"/>' +
        '<path d="M8 11V8a4 4 0 0 1 8 0v3"/>' +
        "</svg>"
      );
    }

    function hideLockChrome() {
      clearTimeout(lockChromeTimer);
      lockChromeTimer = null;
      document.documentElement.classList.remove("lock-chrome-visible");
      if (lockPeekBtn) {
        lockPeekBtn.hidden = true;
        lockPeekBtn.setAttribute("aria-hidden", "true");
      }
    }

    function revealLockChrome() {
      if (!uiLocked || !lockPeekBtn) return;
      // Independent of Plyr's .plyr--hide-controls (which slides the bar away).
      document.documentElement.classList.add("lock-chrome-visible");
      lockPeekBtn.hidden = false;
      lockPeekBtn.setAttribute("aria-hidden", "false");
      clearTimeout(lockChromeTimer);
      lockChromeTimer = setTimeout(hideLockChrome, LOCK_CHROME_MS);
    }

    function unlockFromPeek(e) {
      if (e) {
        e.preventDefault();
        e.stopPropagation();
      }
      if (!uiLocked) return;
      setLocked(false);
      showControlsNow();
    }

    function setLocked(locked) {
      uiLocked = locked;
      document.documentElement.classList.toggle("player-locked", locked);
      hideLockChrome();
      if (lockControlBtn) {
        lockControlBtn.setAttribute("aria-pressed", locked ? "true" : "false");
        lockControlBtn.setAttribute("aria-label", t.lock);
        const tip = lockControlBtn.querySelector(".plyr__tooltip");
        if (tip) tip.textContent = t.lock;
      }
      if (lockPeekBtn) {
        lockPeekBtn.setAttribute("aria-label", t.unlock);
      }
      // Disable Plyr keyboard while locked (global shortcuts would bypass the lock).
      try {
        if (player.keyboard) {
          player.keyboard.focused = !locked;
          player.keyboard.global = !locked;
        }
      } catch (_) {}
      if (locked) {
        hideControlsNow();
        endLongPress();
        dragMode = null;
        [levelBrightness, levelVolume].forEach((el) => {
          if (!el) return;
          el.classList.remove("is-on");
          el.hidden = true;
        });
        setSpeedBadge(false);
      }
    }

    function injectLockControl(container) {
      const controls = player.elements && player.elements.controls;
      if (controls) {
        lockControlBtn = controls.querySelector("[data-plyr-lock]");
        if (!lockControlBtn) {
          const btn = document.createElement("button");
          btn.type = "button";
          btn.className = "plyr__controls__item plyr__control";
          btn.setAttribute("data-plyr-lock", "");
          btn.setAttribute("aria-label", t.lock);
          btn.setAttribute("aria-pressed", "false");
          btn.innerHTML =
            lockIconHtml() +
            `<span class="plyr__tooltip" role="tooltip">${t.lock}</span>`;

          // Sit next to fullscreen — lock is a player control, not page chrome.
          const fs = controls.querySelector('[data-plyr="fullscreen"]');
          if (fs && fs.parentNode) {
            fs.parentNode.insertBefore(btn, fs);
          } else {
            controls.appendChild(btn);
          }

          btn.addEventListener("click", (e) => {
            e.preventDefault();
            e.stopPropagation();
            if (!uiLocked) setLocked(true);
          });
          lockControlBtn = btn;
        }
      }

      // Peek unlock control lives on the player surface (not inside Plyr's bar).
      if (container) {
        lockPeekBtn = container.querySelector("[data-lock-peek]");
        if (!lockPeekBtn) {
          lockPeekBtn = document.createElement("button");
          lockPeekBtn.type = "button";
          lockPeekBtn.className = "lock-peek";
          lockPeekBtn.setAttribute("data-lock-peek", "");
          lockPeekBtn.setAttribute("aria-label", t.unlock);
          lockPeekBtn.hidden = true;
          lockPeekBtn.setAttribute("aria-hidden", "true");
          lockPeekBtn.innerHTML = lockIconHtml();
          lockPeekBtn.addEventListener("click", unlockFromPeek);
          // pointerdown so we don't lose the tap to the gesture hit layer race.
          lockPeekBtn.addEventListener("pointerdown", (e) => {
            e.stopPropagation();
          });
          container.appendChild(lockPeekBtn);
        }
      }
    }

    function startLongPress() {
      clearTimeout(longTimer);
      longTimer = setTimeout(() => {
        if (uiLocked || movedFar || pointerId == null || dragMode) return;
        longActive = true;
        speedBeforeHold = player.speed || 1;
        player.speed = Math.max(speedBeforeHold, HOLD_SPEED);
        setSpeedBadge(true);
        try {
          if (navigator.vibrate) navigator.vibrate(VIBRATE_MS);
        } catch (_) {}
      }, LONG_PRESS_MS);
    }

    function endLongPress() {
      clearTimeout(longTimer);
      longTimer = null;
      if (longActive) {
        player.speed = speedBeforeHold || 1;
        longActive = false;
        setSpeedBadge(false);
      }
    }

    function cancelPendingTap() {
      clearTimeout(pendingTapTimer);
      pendingTapTimer = null;
      pendingTapToken += 1;
    }

    function onSingleTapConfirmed() {
      if (uiLocked) return;
      setControlsOpen(!controlsOpen);
    }

    function onPointerDown(e) {
      if (e.pointerType === "mouse" && e.button !== 0) return;
      if (uiLocked) {
        // Tap while locked: flash only the lock icon in the control bar (3s).
        e.preventDefault();
        revealLockChrome();
        return;
      }

      // Kill blue tap/hold selection highlight (HTML selection overlay).
      e.preventDefault();

      pointerId = e.pointerId;
      startX = e.clientX;
      startY = e.clientY;
      movedFar = false;
      dragMode = null;
      dragOriginVolume =
        typeof player.volume === "number"
          ? player.volume
          : mediaEl().volume || 1;
      dragOriginBrightness = brightness;

      try {
        hitEl.setPointerCapture(e.pointerId);
      } catch (_) {}
      startLongPress();
    }

    function onPointerMove(e) {
      if (uiLocked) return;
      if (pointerId == null || e.pointerId !== pointerId) return;

      const dx = e.clientX - startX;
      const dy = e.clientY - startY;
      const dist = Math.hypot(dx, dy);

      if (dist > TAP_MOVE_MAX_PX) {
        movedFar = true;
        cancelPendingTap();
        if (!longActive) {
          clearTimeout(longTimer);
          longTimer = null;
        }
      }

      if (!dragMode && !longActive && dist >= VERTICAL_LOCK_PX) {
        if (Math.abs(dy) >= Math.abs(dx) * AXIS_DOMINANCE) {
          const rect = hitEl.getBoundingClientRect();
          const mid = rect.left + rect.width / 2;
          dragMode = startX < mid ? "brightness" : "volume";
          clearTimeout(longTimer);
          longTimer = null;
          cancelPendingTap();
        }
      }

      if (!dragMode) return;

      const rect = hitEl.getBoundingClientRect();
      const h = Math.max(rect.height, 1);
      // Full-height drag ≈ full range; drag up increases.
      const delta = -dy / h;

      if (dragMode === "volume") {
        let next = dragOriginVolume + delta;
        next = Math.min(1, Math.max(0, next));
        try {
          player.volume = next;
        } catch (_) {}
        const m = mediaEl();
        if (m) m.volume = next;
        if (next > UNMUTE_VOLUME_FLOOR) {
          try {
            player.muted = false;
          } catch (_) {}
          if (m) m.muted = false;
        }
        showLevel("volume", next);
      } else {
        const span = BRIGHTNESS_MAX - BRIGHTNESS_MIN;
        applyBrightness(dragOriginBrightness + delta * span);
        showLevel(
          "brightness",
          (brightness - BRIGHTNESS_MIN) / (BRIGHTNESS_MAX - BRIGHTNESS_MIN)
        );
      }
    }

    function onPointerUp(e) {
      if (pointerId == null || e.pointerId !== pointerId) return;
      if (uiLocked) {
        pointerId = null;
        return;
      }

      const dx = e.clientX - startX;
      const dy = e.clientY - startY;
      const wasLong = longActive;
      const wasDrag = Boolean(dragMode);
      endLongPress();
      try {
        hitEl.releasePointerCapture(e.pointerId);
      } catch (_) {}
      pointerId = null;

      if (wasDrag) {
        hideLevelSoon();
        dragMode = null;
        return;
      }
      if (wasLong) return;

      const rect = hitEl.getBoundingClientRect();
      const fromTopEdge = startY - rect.top < rect.height * TOP_EDGE_RATIO;
      if (
        isFullscreenActive() &&
        fromTopEdge &&
        dy > SWIPE_DOWN_MIN_PX &&
        Math.abs(dy) > Math.abs(dx) * SWIPE_AXIS_DOMINANCE
      ) {
        try {
          player.fullscreen.exit();
        } catch (_) {}
        return;
      }

      if (movedFar || Math.hypot(dx, dy) > TAP_MOVE_MAX_PX) return;

      const now = Date.now();
      const x = e.clientX;
      const y = e.clientY;
      const isDouble =
        now - lastTapAt <= DOUBLE_TAP_MS &&
        Math.hypot(x - lastTapX, y - lastTapY) < DOUBLE_TAP_DIST_PX;

      if (isDouble) {
        cancelPendingTap();
        const mid = rect.left + rect.width / 2;
        if (x < mid) seekBy(-SEEK_STEP_S);
        else seekBy(SEEK_STEP_S);
        lastTapAt = 0;
        return;
      }

      lastTapAt = now;
      lastTapX = x;
      lastTapY = y;
      cancelPendingTap();
      const token = ++pendingTapToken;
      pendingTapTimer = setTimeout(() => {
        if (token !== pendingTapToken) return;
        if (lastTapAt !== now) return;
        onSingleTapConfirmed();
      }, DOUBLE_TAP_MS);
    }

    function onPointerCancel(e) {
      if (pointerId == null || e.pointerId !== pointerId) return;
      endLongPress();
      if (dragMode) hideLevelSoon();
      dragMode = null;
      pointerId = null;
    }

    function onContainerDblClick(e) {
      e.preventDefault();
      e.stopPropagation();
    }

    function onContainerSelectStart(e) {
      e.preventDefault();
    }

    function onContainerDragStart(e) {
      e.preventDefault();
    }

    function onContextMenu(e) {
      e.preventDefault();
    }

    // Block space / arrows / media keys while the UI is locked.
    function onKeydownWhileLocked(e) {
      if (!uiLocked) return;
      const tag = (e.target && e.target.tagName) || "";
      if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return;
      e.preventDefault();
      e.stopPropagation();
    }

    function mountGestureLayer() {
      if (gesturesMounted) return;
      const container = player.elements && player.elements.container;
      if (!container) return;

      // Must live inside .plyr so fullscreen includes hit target + feedback.
      if (gestureUi && gestureUi.parentElement !== container) {
        container.appendChild(gestureUi);
      }

      injectLockControl(container);

      hitEl = container.querySelector(".gesture-hit");
      if (!hitEl) {
        hitEl = document.createElement("div");
        hitEl.className = "gesture-hit";
        hitEl.setAttribute("aria-hidden", "true");
        const controls = player.elements.controls;
        if (controls && controls.parentNode === container) {
          container.insertBefore(hitEl, controls);
        } else {
          container.appendChild(hitEl);
        }
      }
      // When locked, hit layer must sit above residual Plyr chrome so taps register.
      hitEl.style.zIndex = "";

      container.addEventListener("dblclick", onContainerDblClick, true);
      container.addEventListener("selectstart", onContainerSelectStart, true);
      container.addEventListener("dragstart", onContainerDragStart, true);

      hitEl.addEventListener("pointerdown", onPointerDown);
      hitEl.addEventListener("pointermove", onPointerMove);
      hitEl.addEventListener("pointerup", onPointerUp);
      hitEl.addEventListener("pointercancel", onPointerCancel);
      hitEl.addEventListener("contextmenu", onContextMenu);

      document.addEventListener("keydown", onKeydownWhileLocked, true);

      gesturesMounted = true;
    }

    function onPlayerReady() {
      mountGestureLayer();
      setControlsOpen(false);
    }

    // Single path into mount: ready event, or immediate if already ready.
    if (player.ready) {
      onPlayerReady();
    } else {
      player.on("ready", onPlayerReady);
    }

    /* ---------- Fullscreen → force landscape ---------- */
    function lockLandscape() {
      const orientation =
        screen.orientation || screen.mozOrientation || screen.msOrientation;
      if (!orientation || typeof orientation.lock !== "function") return;

      const tryLock = (mode) =>
        Promise.resolve(orientation.lock(mode)).catch(() => null);

      tryLock("landscape")
        .then((ok) => ok || tryLock("landscape-primary"))
        .then((ok) => ok || tryLock("landscape-secondary"))
        .catch(() => {});
    }

    function unlockOrientation() {
      const orientation =
        screen.orientation || screen.mozOrientation || screen.msOrientation;
      if (orientation && typeof orientation.unlock === "function") {
        try {
          orientation.unlock();
        } catch (_) {}
      }
    }

    function isFullscreenActive() {
      return Boolean(
        document.fullscreenElement ||
          document.webkitFullscreenElement ||
          document.mozFullScreenElement ||
          document.msFullscreenElement ||
          (player.fullscreen && player.fullscreen.active) ||
          video.webkitDisplayingFullscreen
      );
    }

    player.on("enterfullscreen", lockLandscape);
    player.on("exitfullscreen", unlockOrientation);

    video.addEventListener("webkitbeginfullscreen", lockLandscape);
    video.addEventListener("webkitendfullscreen", unlockOrientation);

    document.addEventListener("fullscreenchange", () => {
      if (isFullscreenActive()) lockLandscape();
      else unlockOrientation();
    });
    document.addEventListener("webkitfullscreenchange", () => {
      if (isFullscreenActive()) lockLandscape();
      else unlockOrientation();
    });

    /* ---------- Reconnect / loading overlay ----------
       Only show "Cargando…" after a short delay while playback is actually
       waiting for data. Immediate show-on-waiting stuck the UI forever when
       the browser buffered before play (no `playing` event yet). */
    let reconnectAttempts = 0;
    let reconnecting = false;
    let stallTimer = null;
    let loadingShowTimer = null;
    let reconnectDelayTimer = null;
    let reloadMetaHandler = null;

    function showOverlay(text) {
      if (overlayText) overlayText.textContent = text;
      if (overlay) overlay.dataset.open = "true";
    }
    function hideOverlay() {
      clearTimeout(loadingShowTimer);
      loadingShowTimer = null;
      if (overlay) overlay.dataset.open = "false";
    }

    function clearStallWatch() {
      clearTimeout(stallTimer);
      stallTimer = null;
    }

    function clearReloadMetaHandler() {
      if (reloadMetaHandler) {
        video.removeEventListener("loadedmetadata", reloadMetaHandler);
        reloadMetaHandler = null;
      }
    }

    function markReady() {
      clearStallWatch();
      clearReloadMetaHandler();
      reconnectAttempts = 0;
      reconnecting = false;
      hideOverlay();
    }

    function scheduleLoadingOverlay() {
      if (video.paused && !reconnecting) return;
      clearTimeout(loadingShowTimer);
      loadingShowTimer = setTimeout(() => {
        loadingShowTimer = null;
        if (video.paused && !reconnecting) return;
        if (video.readyState >= HAVE_FUTURE_DATA && !video.seeking) return;
        showOverlay(t.loading);
      }, LOADING_OVERLAY_DELAY_MS);
    }

    function armStallReconnect() {
      clearStallWatch();
      stallTimer = setTimeout(() => {
        stallTimer = null;
        if (video.paused || reconnecting) return;
        attemptReconnect();
      }, STALL_RECONNECT_MS);
    }

    function currentBaseUrl() {
      return new URL(source.src, window.location.href);
    }

    function subsEndpointBase(kind) {
      const streamUrl = currentBaseUrl();
      const parts = streamUrl.pathname.split("/");
      const messageId = parts[2];
      const hash = streamUrl.searchParams.get("hash");
      const url = new URL(`/subs/${kind}/${messageId}`, window.location.href);
      if (hash) url.searchParams.set("hash", hash);
      return url;
    }

    let currentSubtitleBlobUrl = null;
    function setSubtitleTrack(url, label, isBlob) {
      if (currentSubtitleBlobUrl) {
        URL.revokeObjectURL(currentSubtitleBlobUrl);
        currentSubtitleBlobUrl = null;
      }
      Array.from(video.querySelectorAll("track")).forEach((tr) => tr.remove());

      const track = document.createElement("track");
      track.kind = "captions";
      track.label = label;
      track.srclang = lang;
      track.src = url;
      track.default = true;
      video.appendChild(track);
      if (isBlob) currentSubtitleBlobUrl = url;
      setTimeout(() => {
        track.mode = "showing";
      }, SUBTITLE_SHOW_DELAY_MS);
    }

    function reloadPreservingPosition(newUrl, resumePlayback) {
      const wasPaused = video.paused;
      const resumeAt = video.currentTime || 0;

      clearReloadMetaHandler();
      reloadMetaHandler = () => {
        try {
          video.currentTime = resumeAt;
        } catch (_) {}
        if (resumePlayback && !wasPaused) {
          video.play().catch(() => {});
        }
        // markReady also clears reconnecting + handler.
        markReady();
      };
      video.addEventListener("loadedmetadata", reloadMetaHandler);
      source.src = newUrl.toString();
      video.load();
    }

    function attemptReconnect() {
      if (reconnecting) return;
      if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
        showOverlay(t.reconnectFail);
        reconnecting = false;
        return;
      }
      reconnecting = true;
      reconnectAttempts += 1;
      const delay = Math.min(
        RECONNECT_BASE_MS * Math.pow(RECONNECT_GROWTH, reconnectAttempts - 1),
        RECONNECT_MAX_MS
      );
      showOverlay(
        `${t.reconnecting} (${t.attempt} ${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS})`
      );
      clearTimeout(reconnectDelayTimer);
      reconnectDelayTimer = setTimeout(() => {
        reconnectDelayTimer = null;
        const url = currentBaseUrl();
        url.searchParams.set("_r", Date.now().toString());
        // Stay in reconnecting until markReady (loadedmetadata) or a later error path.
        reloadPreservingPosition(url, true);
      }, delay);
    }

    video.addEventListener("error", () => {
      if (!source.src) return;
      const mediaError = video.error;
      const code = mediaError ? mediaError.code : 0;
      // 3 MEDIA_ERR_DECODE, 4 MEDIA_ERR_SRC_NOT_SUPPORTED — reconnect won't help.
      if (code === 4) {
        clearStallWatch();
        clearTimeout(reconnectDelayTimer);
        reconnecting = false;
        showOverlay(t.formatUnsupported);
        return;
      }
      if (code === 3) {
        clearStallWatch();
        clearTimeout(reconnectDelayTimer);
        reconnecting = false;
        showOverlay(t.formatDecode);
        return;
      }
      // If a reload is mid-flight and errors, allow another attempt.
      if (reconnecting && reloadMetaHandler) {
        clearReloadMetaHandler();
        reconnecting = false;
      }
      attemptReconnect();
    });

    video.addEventListener("waiting", () => {
      armStallReconnect();
      scheduleLoadingOverlay();
    });

    video.addEventListener("stalled", () => {
      armStallReconnect();
      scheduleLoadingOverlay();
    });

    ["playing", "canplay", "canplaythrough", "loadeddata", "seeked"].forEach(
      (evt) => {
        video.addEventListener(evt, markReady);
      }
    );
    video.addEventListener("pause", () => {
      if (!reconnecting) hideOverlay();
      clearStallWatch();
    });

    /* ---------- Sheet toggles (interruptible open/close) ---------- */
    function setSheetOpen(sheet, open) {
      if (!sheet) return;
      if (open) {
        sheet.hidden = false;
        sheet.setAttribute("aria-hidden", "false");
        // Double rAF so grid/opacity transitions run after display is restored.
        requestAnimationFrame(() => {
          requestAnimationFrame(() => {
            sheet.classList.add("is-open");
          });
        });
      } else {
        sheet.classList.remove("is-open");
        sheet.setAttribute("aria-hidden", "true");
        const finish = (e) => {
          if (e && e.target !== sheet) return;
          if (e && e.propertyName && e.propertyName !== "opacity") return;
          if (!sheet.classList.contains("is-open")) {
            sheet.hidden = true;
          }
          sheet.removeEventListener("transitionend", finish);
        };
        sheet.addEventListener("transitionend", finish);
        setTimeout(finish, SHEET_CLOSE_FALLBACK_MS);
      }
    }

    function openSheet(id) {
      const sheet = document.getElementById(id);
      if (!sheet) return;
      const wasOpen = sheet.classList.contains("is-open");

      document.querySelectorAll(".sheet").forEach((s) => {
        if (s !== sheet) setSheetOpen(s, false);
      });
      document.querySelectorAll(".rail-btn[aria-pressed]").forEach((b) => {
        b.setAttribute("aria-pressed", "false");
      });

      if (wasOpen) {
        setSheetOpen(sheet, false);
        return;
      }

      if (id === "sheet-audio") syncAudioSheetContent();

      setSheetOpen(sheet, true);
      const btn = document.querySelector(`[data-sheet="${id}"]`);
      if (btn) btn.setAttribute("aria-pressed", "true");
      setTimeout(() => {
        sheet.scrollIntoView({ behavior: "smooth", block: "nearest" });
      }, SHEET_SCROLL_DELAY_MS);
    }

    document.querySelectorAll("[data-sheet]").forEach((btn) => {
      btn.addEventListener("click", () => {
        openSheet(btn.getAttribute("data-sheet"));
      });
    });

    /* ---------- Local subtitles ---------- */
    const subUpload = document.getElementById("sub-upload");
    const uploadLabel = document.getElementById("sub-upload-label");

    if (subUpload) {
      subUpload.addEventListener("change", function (e) {
        const file = e.target.files && e.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = () => {
          const text = String(reader.result || "");
          const blob = new Blob([srtToVtt(text)], { type: "text/vtt" });
          const url = URL.createObjectURL(blob);
          setSubtitleTrack(url, file.name, true);

          if (uploadLabel) {
            uploadLabel.classList.add("is-success");
            const textEl = uploadLabel.querySelector("[data-upload-text]");
            const prev = textEl ? textEl.textContent : "";
            if (textEl) textEl.textContent = t.subLoaded;
            setTimeout(() => {
              uploadLabel.classList.remove("is-success");
              if (textEl) textEl.textContent = prev || t.uploadSub;
            }, UPLOAD_SUCCESS_MS);
          }
        };
        reader.onerror = () => {
          // Fall back to raw object URL (VTT-only browsers may still work).
          const url = URL.createObjectURL(file);
          setSubtitleTrack(url, file.name, true);
        };
        reader.readAsText(file);
      });
    }

    /* ---------- Online subtitles ---------- */
    const subsQueryInput = document.getElementById("subs-query-input");
    const subsSearchBtn = document.getElementById("subs-search-btn");
    const subsSelector = document.getElementById("subs-results-selector");
    const subsStatus = document.getElementById("subs-status");

    function showSubsStatus(text, tone) {
      if (!subsStatus) return;
      subsStatus.hidden = false;
      subsStatus.textContent = text;
      if (tone) subsStatus.dataset.tone = tone;
      else delete subsStatus.dataset.tone;
    }
    function hideSubsStatus() {
      if (subsStatus) {
        subsStatus.hidden = true;
        subsStatus.textContent = "";
      }
    }

    async function searchSubtitles(query) {
      showSubsStatus(t.searching);
      if (subsSelector) {
        subsSelector.hidden = true;
        subsSelector.innerHTML = "";
      }
      try {
        const url = subsEndpointBase("search");
        if (query) url.searchParams.set("query", query);
        const res = await fetch(url.toString());
        if (!res.ok) {
          showSubsStatus(t.searchError, "error");
          return;
        }
        const data = await res.json();

        if (data.error) {
          showSubsStatus(data.error, "error");
          return;
        }
        if (subsQueryInput && data.query) {
          subsQueryInput.value = data.query;
        }
        if (!data.results || data.results.length === 0) {
          showSubsStatus(t.noSubs, "warn");
          return;
        }

        hideSubsStatus();
        if (subsSelector) {
          const blank = document.createElement("option");
          blank.value = "";
          blank.textContent = t.pickSub;
          subsSelector.appendChild(blank);
          data.results.forEach((item) => {
            const opt = document.createElement("option");
            opt.value = item.file_id;
            const dl =
              item.download_count != null
                ? ` · ${item.download_count}`
                : "";
            const hi = item.hearing_impaired ? " · [SDH]" : "";
            opt.textContent = `${item.release || "Sub"} (${(
              item.language || "?"
            ).toUpperCase()})${dl}${hi}`;
            subsSelector.appendChild(opt);
          });
          subsSelector.hidden = false;
        }
      } catch (_) {
        showSubsStatus(t.searchError, "error");
      }
    }

    async function applySelectedSubtitle(fileId, label) {
      showSubsStatus(t.downloading);
      try {
        const url = subsEndpointBase("get");
        url.searchParams.set("file_id", fileId);
        const res = await fetch(url.toString());
        if (!res.ok) {
          showSubsStatus(t.downloadError, "error");
          return;
        }
        const vttText = await res.text();
        const blob = new Blob([srtToVtt(vttText)], { type: "text/vtt" });
        const blobUrl = URL.createObjectURL(blob);
        setSubtitleTrack(blobUrl, label, true);
        showSubsStatus(t.subLoaded, "ok");
        setTimeout(hideSubsStatus, SUB_STATUS_OK_MS);
      } catch (_) {
        showSubsStatus(t.downloadError, "error");
      }
    }

    if (subsSearchBtn) {
      subsSearchBtn.addEventListener("click", () => {
        searchSubtitles(subsQueryInput ? subsQueryInput.value.trim() : "");
      });
    }
    if (subsQueryInput) {
      subsQueryInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
          e.preventDefault();
          searchSubtitles(subsQueryInput.value.trim());
        }
      });
    }
    if (subsSelector) {
      subsSelector.addEventListener("change", (e) => {
        const fileId = e.target.value;
        if (!fileId) return;
        const label = e.target.selectedOptions[0].textContent;
        applySelectedSubtitle(fileId, label);
      });
    }

    // Only when the host explicitly enables it (local demo keeps this false).
    if (config.autoSearchSubs === true) {
      searchSubtitles("");
    }

    /* ---------- Audio tracks ----------
       Audio button always visible. Sheet shows the track picker when the
       browser exposes 2+ tracks; otherwise the honest fallback note. */
    function syncAudioSheetContent() {
      if (hasMultiAudio) {
        if (audioPanel) audioPanel.hidden = false;
        if (audioNote) audioNote.hidden = true;
      } else {
        if (audioPanel) audioPanel.hidden = true;
        if (audioNote) audioNote.hidden = false;
      }
    }

    syncAudioSheetContent();

    video.addEventListener("loadedmetadata", () => {
      const audioTracks = video.audioTracks;
      hasMultiAudio = Boolean(audioTracks && audioTracks.length > 1);

      if (hasMultiAudio && audioSelector) {
        audioSelector.innerHTML = "";
        for (let i = 0; i < audioTracks.length; i++) {
          const option = document.createElement("option");
          option.value = i;
          option.text =
            audioTracks[i].label ||
            audioTracks[i].language ||
            `Track ${i + 1}`;
          if (audioTracks[i].enabled) option.selected = true;
          audioSelector.appendChild(option);
        }
        audioSelector.onchange = (e) => {
          const idx = parseInt(e.target.value, 10);
          for (let i = 0; i < audioTracks.length; i++) {
            audioTracks[i].enabled = i === idx;
          }
        };
      }

      syncAudioSheetContent();
    });

    // Keep a reference so Plyr isn't GC'd in strict engines.
    window.__cinemaPlayer = player;
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
