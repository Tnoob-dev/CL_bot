from __future__ import annotations

import html as html_lib
import json
import re
from pathlib import Path

from ..file_properties import FileInfo

_ROOT = Path(__file__).resolve().parent
_CSS_PATH = _ROOT / "static" / "css" / "player.css"
_JS_PATH = _ROOT / "static" / "js" / "player.js"

# Reicon SVGs (currentColor; no runtime package). Source: https://reicon.dev
ICON_PLAY = (
    '<svg class="icon" width="24" height="24" aria-hidden="true" '
    'xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none">'
    '<path fill-rule="evenodd" clip-rule="evenodd" d="M7.23832 3.04445C5.65196 2.1818 '
    "3.75 3.31957 3.75 5.03299L3.75 18.9672C3.75 20.6806 5.65196 21.8184 7.23832 20.9557"
    "L20.0503 13.9886C21.6499 13.1188 21.6499 10.8814 20.0503 10.0116L7.23832 3.04445ZM"
    "2.25 5.03299C2.25 2.12798 5.41674 0.346438 7.95491 1.72669L20.7669 8.6938C23.411 "
    "10.1317 23.411 13.8685 20.7669 15.3064L7.95491 22.2735C5.41674 23.6537 2.25 "
    '21.8722 2.25 18.9672L2.25 5.03299Z" fill="currentColor"/></svg>'
)

ICON_DOWNLOAD = (
    '<svg class="icon" width="24" height="24" aria-hidden="true" '
    'xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none">'
    '<path d="M12.5535 16.5061C12.4114 16.6615 12.2106 16.75 12 16.75C11.7894 16.75 '
    "11.5886 16.6615 11.4465 16.5061L7.44648 12.1311C7.16698 11.8254 7.18822 11.351 "
    "7.49392 11.0715C7.79963 10.792 8.27402 10.8132 8.55352 11.1189L11.25 14.0682V3C"
    "11.25 2.58579 11.5858 2.25 12 2.25C12.4142 2.25 12.75 2.58579 12.75 3V14.0682L"
    "15.4465 11.1189C15.726 10.8132 16.2004 10.792 16.5061 11.0715C16.8118 11.351 "
    '16.833 11.8254 16.5535 12.1311L12.5535 16.5061Z" fill="currentColor"/>'
    '<path d="M3.75 15C3.75 14.5858 3.41422 14.25 3 14.25C2.58579 14.25 2.25 14.5858 '
    "2.25 15V15.0549C2.24998 16.4225 2.24996 17.5248 2.36652 18.3918C2.48754 19.2919 "
    "2.74643 20.0497 3.34835 20.6516C3.95027 21.2536 4.70814 21.5125 5.60825 21.6335"
    "C6.47522 21.75 7.57754 21.75 8.94513 21.75H15.0549C16.4225 21.75 17.5248 21.75 "
    "18.3918 21.6335C19.2919 21.5125 20.0497 21.2536 20.6517 20.6516C21.2536 20.0497 "
    "21.5125 19.2919 21.6335 18.3918C21.75 17.5248 21.75 16.4225 21.75 15.0549V15C"
    "21.75 14.5858 21.4142 14.25 21 14.25C20.5858 14.25 20.25 14.5858 20.25 15C20.25 "
    "16.4354 20.2484 17.4365 20.1469 18.1919C20.0482 18.9257 19.8678 19.3142 19.591 "
    "19.591C19.3142 19.8678 18.9257 20.0482 18.1919 20.1469C17.4365 20.2484 16.4354 "
    "20.25 15 20.25H9C7.56459 20.25 6.56347 20.2484 5.80812 20.1469C5.07435 20.0482 "
    "4.68577 19.8678 4.40901 19.591C4.13225 19.3142 3.9518 18.9257 3.85315 18.1919C"
    '3.75159 17.4365 3.75 16.4354 3.75 15Z" fill="currentColor"/></svg>'
)

ICON_UPLOAD = (
    '<svg class="icon" width="24" height="24" aria-hidden="true" '
    'xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none">'
    '<path d="M12.5535 2.49392C12.4114 2.33852 12.2106 2.25 12 2.25C11.7894 2.25 '
    "11.5886 2.33852 11.4465 2.49392L7.44648 6.86892C7.16698 7.17462 7.18822 7.64902 "
    "7.49392 7.92852C7.79963 8.20802 8.27402 8.18678 8.55352 7.88108L11.25 4.9318V16C"
    "11.25 16.4142 11.5858 16.75 12 16.75C12.4142 16.75 12.75 16.4142 12.75 16V4.9318L"
    "15.4465 7.88108C15.726 8.18678 16.2004 8.20802 16.5061 7.92852C16.8118 7.64902 "
    '16.833 7.17462 16.5535 6.86892L12.5535 2.49392Z" fill="currentColor"/>'
    '<path d="M3.75 15C3.75 14.5858 3.41422 14.25 3 14.25C2.58579 14.25 2.25 14.5858 '
    "2.25 15V15.0549C2.24998 16.4225 2.24996 17.5248 2.36652 18.3918C2.48754 19.2919 "
    "2.74643 20.0497 3.34835 20.6516C3.95027 21.2536 4.70814 21.5125 5.60825 21.6335"
    "C6.47522 21.75 7.57754 21.75 8.94513 21.75H15.0549C16.4225 21.75 17.5248 21.75 "
    "18.3918 21.6335C19.2919 21.5125 20.0497 21.2536 20.6517 20.6516C21.2536 20.0497 "
    "21.5125 19.2919 21.6335 18.3918C21.75 17.5248 21.75 16.4225 21.75 15.0549V15C"
    "21.75 14.5858 21.4142 14.25 21 14.25C20.5858 14.25 20.25 14.5858 20.25 15C20.25 "
    "16.4354 20.2484 17.4365 20.1469 18.1919C20.0482 18.9257 19.8678 19.3142 19.591 "
    "19.591C19.3142 19.8678 18.9257 20.0482 18.1919 20.1469C17.4365 20.2484 16.4354 "
    "20.25 15 20.25H9C7.56459 20.25 6.56347 20.2484 5.80812 20.1469C5.07435 20.0482 "
    "4.68577 19.8678 4.40901 19.591C4.13225 19.3142 3.9518 18.9257 3.85315 18.1919C"
    '3.75159 17.4365 3.75 16.4354 3.75 15Z" fill="currentColor"/></svg>'
)

ICON_SEARCH = (
    '<svg class="icon" width="24" height="24" aria-hidden="true" '
    'xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none">'
    '<path fill-rule="evenodd" clip-rule="evenodd" d="M11.5 2.75C6.66751 2.75 2.75 '
    "6.66751 2.75 11.5C2.75 16.3325 6.66751 20.25 11.5 20.25C16.3325 20.25 20.25 "
    "16.3325 20.25 11.5C20.25 6.66751 16.3325 2.75 11.5 2.75ZM1.25 11.5C1.25 5.83908 "
    "5.83908 1.25 11.5 1.25C17.1609 1.25 21.75 5.83908 21.75 11.5C21.75 14.0605 "
    "20.8111 16.4017 19.2589 18.1982L22.5303 21.4697C22.8232 21.7626 22.8232 22.2374 "
    "22.5303 22.5303C22.2374 22.8232 21.7626 22.8232 21.4697 22.5303L18.1982 19.2589C"
    "16.4017 20.8111 14.0605 21.75 11.5 21.75C5.83908 21.75 1.25 17.1609 1.25 "
    '11.5Z" fill="currentColor"/></svg>'
)

ICON_SUBTITLE = (
    '<svg class="icon" width="24" height="24" aria-hidden="true" '
    'xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none">'
    '<path d="M9 22H15C20 22 22 20 22 15V9C22 4 20 2 15 2H9C4 2 2 4 2 9V15C2 20 4 22 9 22Z" '
    'stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>'
    '<path d="M17.5 17.0801H15.65" stroke="currentColor" stroke-width="1.5" '
    'stroke-linecap="round" stroke-linejoin="round"/>'
    '<path d="M12.97 17.0801H6.5" stroke="currentColor" stroke-width="1.5" '
    'stroke-linecap="round" stroke-linejoin="round"/>'
    '<path d="M17.5 13.3201H11.97" stroke="currentColor" stroke-width="1.5" '
    'stroke-linecap="round" stroke-linejoin="round"/>'
    '<path d="M9.27 13.3201H6.5" stroke="currentColor" stroke-width="1.5" '
    'stroke-linecap="round" stroke-linejoin="round"/></svg>'
)

ICON_VOLUME = (
    '<svg class="icon" width="24" height="24" aria-hidden="true" '
    'xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none">'
    '<path d="M2 10V14C2 16 3 17 5 17H6.43C6.8 17 7.17 17.11 7.49 17.3L10.41 19.13C'
    "12.93 20.71 15 19.56 15 16.59V7.41003C15 4.43003 12.93 3.29003 10.41 4.87003L7.49 "
    '6.70003C7.17 6.89003 6.8 7.00003 6.43 7.00003H5C3 7.00003 2 8.00003 2 10Z" '
    'stroke="currentColor" stroke-width="1.5"/>'
    '<path d="M18 8C19.78 10.37 19.78 13.63 18 16" stroke="currentColor" '
    'stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>'
    '<path d="M19.83 5.5C22.72 9.35 22.72 14.65 19.83 18.5" stroke="currentColor" '
    'stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>'
)

# Compact mark for the Plyr control bar (stroke only; JS clones this node).
ICON_LOCK = (
    '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">'
    '<rect x="5" y="11" width="14" height="10" rx="2" fill="none" '
    'stroke="currentColor" stroke-width="1.5"/>'
    '<path d="M8 11V8a4 4 0 0 1 8 0v3" fill="none" stroke="currentColor" '
    'stroke-width="1.5" stroke-linecap="round"/></svg>'
)

BYTES_PER_KIB = 1024
BYTES_PER_MIB = BYTES_PER_KIB * 1024
BYTES_PER_GIB = BYTES_PER_MIB * 1024
DEFAULT_MIME = "video/mp4"
DEFAULT_TITLE = "Video"
PLYR_CSS_URL = "https://cdn.plyr.io/3.7.8/plyr.css"
PLYR_JS_URL = "https://cdn.plyr.io/3.7.8/plyr.polyfilled.js"
THEME_COLOR = "#070708"


def _format_size(nbytes: int) -> str:
    if nbytes >= BYTES_PER_GIB:
        return f"{nbytes / BYTES_PER_GIB:.1f} GB"
    if nbytes >= BYTES_PER_MIB:
        return f"{nbytes / BYTES_PER_MIB:.1f} MB"
    if nbytes >= BYTES_PER_KIB:
        return f"{nbytes / BYTES_PER_KIB:.0f} KB"
    return f"{nbytes} B"


def _ext(name: str) -> str:
    if "." not in name:
        return "VIDEO"
    return name.rsplit(".", 1)[-1].upper()


def _json_for_script(data: object) -> str:
    """Serialize JSON safe to embed inside a <script> element (blocks </script> breakout)."""
    return (
        json.dumps(data, ensure_ascii=False)
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )


# Display title cleaner: "Big_Buck_Bunny_1080_10s_5MB.mp4" → "Big Buck Bunny [1080]".
_SEP = re.compile(r"[._+\-]+")
_MULTI_SPACE = re.compile(r"\s+")
_YEAR = re.compile(r"^(?:19|20)\d{2}$")
_SEASON_EP = re.compile(r"^s(\d{1,2})e(\d{1,3})$", re.IGNORECASE)
_QUALITY = re.compile(
    r"^(?:\[|\()?("
    r"4320p?|2160p?|1440p?|1080p?|720p?|576p?|480p?|360p?|"
    r"4k|8k|uhd|fhd|hd|sd"
    r")(?:\]|\))?$",
    re.IGNORECASE,
)
_NOISE = re.compile(
    r"^(?:"
    r"\d+s|\d+m|\d+h|"  # duration crumbs: 10s, 5m, 2h
    r"\d+(?:\.\d+)?(?:kb|mb|gb|kib|mib|gib)|"  # size crumbs: 5MB
    r"\d{3,5}k|"  # bitrate
    r"\d{1,2}ch|"  # channel layouts
    r"x264|x265|h\.?264|h\.?265|hevc|avc|av1|vp9|"
    r"aac|ac3|eac3|dts|dtsma|dtshd|truehd|flac|opus|mp3|"
    r"bluray|bdrip|brrip|webrip|webdl|web-dl|hdtv|dvdrip|hdrip|remux|"
    r"proper|repack|internal|limited|readnfo|"
    r"multi|dual|subbed|dubbed|extended|unrated|directors?cut|dc|"
    r"sample|trailer|"
    r"hdr|hdr10|hdr10\+?|hdr10plus|dv|dovi|dolby|dolbyvision|atmos|vision|"
    r"10bit|8bit|hi10p|"
    r"yts|yify|rarbg|sparks|ntb|amiable|evo|ion10|rmteam|psa|flux|successfulcrab|"
    r"mp4|mkv|avi|mov|webm|m4v|ts|m2ts"
    r")$",
    re.IGNORECASE,
)
# Scene/release-group leftovers: short all-caps tokens (GROUP, FGT, …).
_RELEASE_TAG = re.compile(r"^[A-Z]{2,10}\d{0,3}$")
# Roman numerals must not be dropped as release tags (Part II, Episode IV).
_ROMAN = re.compile(r"^[IVXLCDM]+$", re.IGNORECASE)

_QUALITY_MAP = {
    "4320": "8K",
    "2160": "4K",
    "1440": "1440",
    "1080": "1080",
    "720": "720",
    "576": "576",
    "480": "480",
    "360": "360",
    "4k": "4K",
    "8k": "8K",
    "uhd": "4K",
    "fhd": "1080",
    "hd": "HD",
    "sd": "SD",
}


def _normalize_quality(raw: str) -> str:
    low = raw.lower().rstrip("p")
    if low in _QUALITY_MAP:
        return _QUALITY_MAP[low]
    return re.sub(r"(?i)p$", "", raw)


def _pretty_token(token: str) -> str:
    se = _SEASON_EP.fullmatch(token)
    if se:
        return f"S{int(se.group(1)):02d}E{int(se.group(2)):02d}"
    if _YEAR.fullmatch(token):
        return token
    if _ROMAN.fullmatch(token):
        return token.upper()
    # Keep short ALL-CAPS (USA, UK).
    if token.isupper() and 2 <= len(token) <= 4:
        return token
    # Preserve mixed internal caps (iPhone-style tokens).
    if (
        len(token) > 1
        and any(c.islower() for c in token[1:])
        and any(c.isupper() for c in token[1:])
    ):
        return token
    return token[:1].upper() + token[1:].lower()


def clean_title(filename: str) -> str:
    """Humanize a media filename for display. Never raises; falls back to stem."""
    raw = (filename or "").strip()
    if not raw:
        return DEFAULT_TITLE

    stem = Path(raw).stem
    # Soft-normalize brackets so "Name [1080p]" quality can be detected.
    text = stem.replace("(", " ").replace(")", " ").replace("[", " ").replace("]", " ")
    text = _SEP.sub(" ", text)
    text = _MULTI_SPACE.sub(" ", text).strip()
    if not text:
        return stem or raw

    tokens = text.split(" ")
    quality: str | None = None
    kept: list[str] = []

    for tok in tokens:
        if not tok:
            continue
        q = _QUALITY.fullmatch(tok)
        if q:
            if quality is None:
                quality = _normalize_quality(q.group(1))
            continue
        if _NOISE.fullmatch(tok):
            continue
        # Drop scene-group tags once we already have a title word.
        # Keep roman numerals (II, IV) and years.
        if (
            kept
            and _RELEASE_TAG.fullmatch(tok)
            and not _YEAR.fullmatch(tok)
            and not _ROMAN.fullmatch(tok)
            and tok.isupper()
            and len(tok) <= 10
        ):
            continue
        kept.append(tok)

    if not kept:
        kept = [t for t in tokens if t and not _QUALITY.fullmatch(t)]
        if not kept:
            kept = tokens

    title = _MULTI_SPACE.sub(" ", " ".join(_pretty_token(t) for t in kept)).strip(" -_")
    if not title:
        title = stem

    if quality and f"[{quality}]" not in title:
        title = f"{title} [{quality}]"

    return title


def _read_static(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"Required static asset missing: {path}")
    return path.read_text(encoding="utf-8")


def styles() -> str:
    return f"<style>\n{_read_static(_CSS_PATH)}\n</style>"


def scripts() -> str:
    # Plyr without defer so the inline player script can use window.Plyr immediately.
    js = _read_static(_JS_PATH)
    return f'<script src="{PLYR_JS_URL}"></script>\n<script>\n{js}\n</script>'


def create_html(
    file_info: FileInfo,
    stream_url: str,
    *,
    auto_search_subs: bool = True,
) -> str:
    """Build a self-contained player HTML document for one streamed title.

    Parameters
    ----------
    file_info:
        Host ``FileInfo`` (or anything with file_name / file_size / mime_type).
    stream_url:
        e.g. ``/stream/<message_id>?hash=...`` — used for video + download.
    auto_search_subs:
        When True (default), client calls online subtitle search on load.
        Local demo can pass False if ``/subs/*`` is not available.
    """
    raw_name = file_info.file_name
    display_title = clean_title(raw_name)
    name = html_lib.escape(display_title)
    raw_attr = html_lib.escape(raw_name, quote=True)
    size = _format_size(file_info.file_size)
    ext = html_lib.escape(_ext(raw_name))
    mime = html_lib.escape(file_info.mime_type or DEFAULT_MIME)
    stream = html_lib.escape(stream_url, quote=True)
    download_url = html_lib.escape(
        stream_url + ("&" if "?" in stream_url else "?") + "s=1",
        quote=True,
    )
    config_json = _json_for_script(
        {
            "autoSearchSubs": auto_search_subs,
            "fileName": file_info.file_name,
        }
    )

    return f"""<!DOCTYPE html>
<html lang="es" data-lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
  <meta name="theme-color" content="{THEME_COLOR}">
  <meta name="color-scheme" content="dark">
  <title>{name} · Cinema Library</title>
  <link rel="stylesheet" href="{PLYR_CSS_URL}">
  {styles()}
</head>
<body>
  <div class="app">
    <header class="topbar">
      <div class="brand">
        <span class="brand-mark" aria-hidden="true">{ICON_PLAY}</span>
        <span class="brand-name" data-i18n="brand">Cinema Library</span>
      </div>
    </header>

    <div class="stage-wrap">
      <div class="stage">
        <div id="reconnect-overlay" class="overlay" data-open="false" role="status" aria-live="polite">
          <div class="overlay-spinner" aria-hidden="true"></div>
          <span id="reconnect-text" class="overlay-text" data-i18n="loading">Cargando…</span>
        </div>
        <!-- Moved into .plyr on ready so it survives fullscreen. -->
        <div class="gesture-ui" data-gesture-ui aria-hidden="true">
          <div class="gesture-flash gesture-flash--left" data-seek-flash="left">
            <span class="gesture-flash-label">−10</span>
          </div>
          <div class="gesture-flash gesture-flash--right" data-seek-flash="right">
            <span class="gesture-flash-label">+10</span>
          </div>
          <div class="gesture-speed" data-speed-badge>2×</div>
          <!-- Side rails: brightness left, volume right -->
          <div class="gesture-level gesture-level--left" data-level-badge="brightness" hidden>
            <span class="gesture-level-value" data-level-value></span>
            <div class="gesture-level-bar" aria-hidden="true">
              <div class="gesture-level-fill" data-level-fill></div>
            </div>
            <span class="gesture-level-kind" data-level-kind></span>
          </div>
          <div class="gesture-level gesture-level--right" data-level-badge="volume" hidden>
            <span class="gesture-level-value" data-level-value></span>
            <div class="gesture-level-bar" aria-hidden="true">
              <div class="gesture-level-fill" data-level-fill></div>
            </div>
            <span class="gesture-level-kind" data-level-kind></span>
          </div>
        </div>
        <template id="tpl-icon-lock">{ICON_LOCK}</template>
        <video id="player" playsinline controls crossorigin preload="auto">
          <source id="player-source" src="{stream}" type="{mime}">
        </video>
      </div>
    </div>

    <section class="meta">
      <h1 class="title" title="{raw_attr}">{name}</h1>
      <div class="chips">
        <span class="chip">{size}</span>
        <span class="chip">{ext}</span>
        <span class="chip chip--live">
          <span class="dot" aria-hidden="true"></span>
          <span data-i18n="streaming">Streaming</span>
        </span>
      </div>
    </section>

    <nav class="rail" aria-label="Acciones">
      <button type="button" class="rail-btn" id="rail-subs" data-sheet="sheet-subs" aria-pressed="false" data-i18n-aria="subtitles">
        {ICON_SUBTITLE}
        <span data-i18n="subtitles">Subtítulos</span>
      </button>
      <button type="button" class="rail-btn" id="rail-audio" data-sheet="sheet-audio" aria-pressed="false" data-i18n-aria="audio">
        {ICON_VOLUME}
        <span data-i18n="audio">Audio</span>
      </button>
      <a class="rail-btn" href="{download_url}" download data-i18n-aria="download">
        {ICON_DOWNLOAD}
        <span data-i18n="download">Descargar</span>
      </a>
    </nav>

    <section id="sheet-subs" class="sheet" aria-hidden="true">
      <div class="sheet-clip">
        <div class="sheet-head">
          <h2 class="sheet-title" data-i18n="sheetSubs">Subtítulos</h2>
        </div>
        <div class="sheet-body">
          <div class="field">
            <label class="field-label" for="subs-query-input" data-i18n="search">Buscar</label>
            <div class="row">
              <input class="input" type="search" id="subs-query-input" data-i18n-placeholder="searchPlaceholder" placeholder="Título, película o serie…" autocomplete="off" enterkeyhint="search">
              <button type="button" class="btn btn--primary" id="subs-search-btn" data-i18n-aria="search">
                {ICON_SEARCH}
                <span data-i18n="search">Buscar</span>
              </button>
            </div>
          </div>

          <select id="subs-results-selector" class="select" hidden aria-label="Resultados"></select>
          <p id="subs-status" class="status" hidden></p>

          <div class="divider-label"><span data-i18n="uploadSub">Añadir archivo</span></div>

          <label class="btn btn--ghost" id="sub-upload-label" for="sub-upload">
            <input class="file-input" type="file" id="sub-upload" accept=".vtt,.srt,text/vtt,application/x-subrip">
            {ICON_UPLOAD}
            <span data-upload-text data-i18n="uploadSub">Añadir archivo</span>
          </label>
        </div>
      </div>
    </section>

    <section id="sheet-audio" class="sheet" aria-hidden="true">
      <div class="sheet-clip">
        <div class="sheet-head">
          <h2 class="sheet-title" data-i18n="sheetAudio">Pista de audio</h2>
        </div>
        <div class="sheet-body">
          <div id="audio-tracks-panel" class="audio-panel" hidden>
            <label class="field-label" for="audio-track-selector" data-i18n="audioPick">Elegir pista de audio</label>
            <select id="audio-track-selector" class="select"></select>
          </div>
          <p id="audio-track-note" class="note" hidden data-i18n="audioNote">
            Tu navegador no expone varias pistas de audio. Ábrelo en VLC o MX Player para elegir el audio.
          </p>
        </div>
      </div>
    </section>
  </div>

  <script type="application/json" id="player-config">{config_json}</script>
  {scripts()}
</body>
</html>"""
