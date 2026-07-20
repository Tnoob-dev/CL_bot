def scripts()->str:
    return f"""<script src="https://cdn.plyr.io/3.7.8/plyr.polyfilled.js"></script>
        <script>
            document.addEventListener('DOMContentLoaded', () => {{
                const video = document.getElementById('player');
                const source = document.getElementById('player-source');
                const overlay = document.getElementById('reconnect-overlay');
                const overlayText = document.getElementById('reconnect-text');
                const audioSelector = document.getElementById('audio-track-selector');
                const audioNote = document.getElementById('audio-track-note');

                const player = new Plyr(video, {{
                    captions: {{ active: true, update: true, language: 'auto' }},
                    fullscreen: {{
                        enabled: true,
                        fallback: true,
                        iosNative: true,
                        container: null
                    }},
                    i18n: {{
                        quality: 'Calidad',
                        speed: 'Velocidad',
                        captions: 'Subtítulos',
                        disabled: 'Desactivado',
                        enabled: 'Activado',
                    }}
                }});

                // ---------- Reconexión automática ante cortes de conexión ----------
                let reconnectAttempts = 0;
                const maxReconnectAttempts = 6;
                let reconnecting = false;
                let stallTimer = null;

                function showOverlay(text) {{
                    if (overlayText) overlayText.textContent = text;
                    if (overlay) overlay.style.display = 'flex';
                }}
                function hideOverlay() {{
                    if (overlay) overlay.style.display = 'none';
                }}

                function currentBaseUrl() {{
                    const url = new URL(source.src, window.location.href);
                    return url;
                }}

                function subsEndpointBase(kind) {{
                    // Reutiliza el mismo message_id y hash que ya viven en la URL
                    // del stream, así no hace falta inyectar variables nuevas.
                    const streamUrl = currentBaseUrl();
                    const parts = streamUrl.pathname.split('/'); // ['', 'stream', '123']
                    const messageId = parts[2];
                    const hash = streamUrl.searchParams.get('hash');
                    const url = new URL(`/subs/${{kind}}/${{messageId}}`, window.location.href);
                    if (hash) url.searchParams.set('hash', hash);
                    return url;
                }}

                let currentSubtitleBlobUrl = null;
                function setSubtitleTrack(url, label, isBlob) {{
                    if (currentSubtitleBlobUrl) {{
                        URL.revokeObjectURL(currentSubtitleBlobUrl);
                        currentSubtitleBlobUrl = null;
                    }}
                    Array.from(video.querySelectorAll('track')).forEach(t => t.remove());

                    const track = document.createElement('track');
                    track.kind = 'captions';
                    track.label = label;
                    track.srclang = 'es';
                    track.src = url;
                    track.default = true;
                    video.appendChild(track);

                    if (isBlob) currentSubtitleBlobUrl = url;

                    setTimeout(() => {{ track.mode = 'showing'; }}, 300);
                }}

                function reloadPreservingPosition(newUrl, resumePlayback) {{
                    const wasPaused = video.paused;
                    const resumeAt = video.currentTime || 0;

                    const onLoaded = () => {{
                        try {{
                            video.currentTime = resumeAt;
                        }} catch (e) {{ /* noop */ }}
                        if (resumePlayback && !wasPaused) {{
                            video.play().catch(() => {{}});
                        }}
                        hideOverlay();
                        video.removeEventListener('loadedmetadata', onLoaded);
                    }};
                    video.addEventListener('loadedmetadata', onLoaded);

                    source.src = newUrl.toString();
                    video.load();
                }}

                function attemptReconnect() {{
                    if (reconnecting) return;
                    if (reconnectAttempts >= maxReconnectAttempts) {{
                        showOverlay('No se pudo reconectar. Revisa tu conexión y recarga la página.');
                        return;
                    }}
                    reconnecting = true;
                    reconnectAttempts += 1;
                    const delay = Math.min(1000 * Math.pow(1.6, reconnectAttempts - 1), 12000);
                    showOverlay(`Reconectando... (intento ${{reconnectAttempts}}/${{maxReconnectAttempts}})`);

                    setTimeout(() => {{
                        const url = currentBaseUrl();
                        // cache-buster para forzar una nueva conexión con el servidor
                        url.searchParams.set('_r', Date.now().toString());
                        reloadPreservingPosition(url, true);
                        reconnecting = false;
                    }}, delay);
                }}

                video.addEventListener('error', () => {{
                    attemptReconnect();
                }});

                // 'waiting' se dispara constantemente durante buffering normal
                // (no significa que la conexión se cortó). El backend puede
                // tardar en recuperar un chunk lento gracias a sus propios
                // reintentos, así que el margen antes de intervenir debe ser
                // generoso: si es muy corto, se reinicia la descarga antes de
                // que el backend tenga chance de resolverlo solo, y el video
                // nunca llega a terminar de cargar (bucle infinito).
                video.addEventListener('waiting', () => {{
                    clearTimeout(stallTimer);
                    stallTimer = setTimeout(() => {{
                        if (video.paused) return;
                        attemptReconnect();
                    }}, 30000);
                    showOverlay('Cargando...');
                }});

                // 'stalled' es más específico: el navegador intentó pedir
                // datos y no llegó nada. Se usa el mismo margen que 'waiting'.
                video.addEventListener('stalled', () => {{
                    if (!stallTimer) {{
                        stallTimer = setTimeout(() => {{
                            if (video.paused) return;
                            attemptReconnect();
                        }}, 30000);
                        showOverlay('Cargando...');
                    }}
                }});

                video.addEventListener('playing', () => {{
                    clearTimeout(stallTimer);
                    reconnectAttempts = 0;
                    hideOverlay();
                }});

                // ---------- Subtítulos por archivo local ----------
                document.getElementById('sub-upload').addEventListener('change', function(e) {{
                    const file = e.target.files[0];
                    if (!file) return;

                    const url = URL.createObjectURL(file);
                    setSubtitleTrack(url, file.name, true);

                    // Animación de éxito
                    const label = this.parentElement;
                    const originalText = label.innerHTML;
                    label.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="#4ade80" stroke-width="2"><path d="M20 6L9 17l-5-5"/></svg> Cargado con éxito`;
                    label.style.borderColor = '#4ade80';
                    label.style.color = '#4ade80';

                    setTimeout(() => {{
                        label.innerHTML = originalText;
                        label.style.borderColor = '';
                        label.style.color = '';
                    }}, 3000);
                }});

                // ---------- Subtítulos en línea (OpenSubtitles) ----------
                const subsQueryInput = document.getElementById('subs-query-input');
                const subsSearchBtn = document.getElementById('subs-search-btn');
                const subsSelector = document.getElementById('subs-results-selector');
                const subsStatus = document.getElementById('subs-status');

                function showSubsStatus(text) {{
                    if (!subsStatus) return;
                    subsStatus.style.display = 'block';
                    subsStatus.textContent = text;
                }}
                function hideSubsStatus() {{
                    if (subsStatus) subsStatus.style.display = 'none';
                }}

                async function searchSubtitles(query) {{
                    showSubsStatus('Buscando subtítulos...');
                    if (subsSelector) subsSelector.style.display = 'none';
                    try {{
                        const url = subsEndpointBase('search');
                        if (query) url.searchParams.set('query', query);
                        const res = await fetch(url.toString());
                        const data = await res.json();

                        if (data.error) {{
                            showSubsStatus(data.error);
                            return;
                        }}
                        if (subsQueryInput && data.query) {{
                            subsQueryInput.value = data.query;
                        }}

                        if (!data.results || data.results.length === 0) {{
                            showSubsStatus('No se encontraron subtítulos para esta búsqueda. Prueba con otro título.');
                            return;
                        }}

                        hideSubsStatus();
                        if (subsSelector) {{
                            subsSelector.innerHTML = '<option value="">Elige un subtítulo...</option>';
                            data.results.forEach((item) => {{
                                const opt = document.createElement('option');
                                opt.value = item.file_id;
                                const dl = item.download_count != null ? ` · ${{item.download_count}} descargas` : '';
                                const hi = item.hearing_impaired ? ' · [SDH]' : '';
                                opt.textContent = `${{item.release || 'Subtítulo'}} (${{(item.language || '?').toUpperCase()}})${{dl}}${{hi}}`;
                                subsSelector.appendChild(opt);
                            }});
                            subsSelector.style.display = 'inline-flex';
                        }}
                    }} catch (e) {{
                        showSubsStatus('Error buscando subtítulos. Intenta de nuevo.');
                    }}
                }}

                async function applySelectedSubtitle(fileId, label) {{
                    showSubsStatus('Descargando subtítulo...');
                    try {{
                        const url = subsEndpointBase('get');
                        url.searchParams.set('file_id', fileId);
                        const res = await fetch(url.toString());
                        if (!res.ok) {{
                            showSubsStatus('No se pudo descargar ese subtítulo, prueba con otro de la lista.');
                            return;
                        }}
                        const vttText = await res.text();
                        const blob = new Blob([vttText], {{ type: 'text/vtt' }});
                        const blobUrl = URL.createObjectURL(blob);
                        setSubtitleTrack(blobUrl, label, true);
                        hideSubsStatus();
                    }} catch (e) {{
                        showSubsStatus('Error descargando el subtítulo. Intenta con otro.');
                    }}
                }}

                if (subsSearchBtn) {{
                    subsSearchBtn.addEventListener('click', () => {{
                        searchSubtitles(subsQueryInput ? subsQueryInput.value.trim() : '');
                    }});
                }}
                if (subsQueryInput) {{
                    subsQueryInput.addEventListener('keydown', (e) => {{
                        if (e.key === 'Enter') {{
                            e.preventDefault();
                            searchSubtitles(subsQueryInput.value.trim());
                        }}
                    }});
                }}
                if (subsSelector) {{
                    subsSelector.addEventListener('change', (e) => {{
                        const fileId = e.target.value;
                        if (!fileId) return;
                        const label = e.target.selectedOptions[0].textContent;
                        applySelectedSubtitle(fileId, label);
                    }});
                }}

                // Búsqueda automática al cargar la página, usando el nombre
                // del archivo como punto de partida (el usuario puede editarlo
                // y volver a buscar).
                searchSubtitles('');

                // ---------- Selección de pista de audio ----------
                video.addEventListener('loadedmetadata', () => {{
                    const audioTracks = video.audioTracks;
                    if (!audioTracks) {{
                        // Navegador sin soporte de la API audioTracks (Safari/Firefox en muchos casos)
                        if (audioSelector) audioSelector.style.display = 'none';
                        if (audioNote) audioNote.style.display = 'block';
                        return;
                    }}
                    if (audioTracks.length > 1) {{
                        if (audioNote) audioNote.style.display = 'none';
                        if (audioSelector) {{
                            audioSelector.style.display = 'inline-flex';
                            audioSelector.innerHTML = '';
                            for (let i = 0; i < audioTracks.length; i++) {{
                                const option = document.createElement('option');
                                option.value = i;
                                option.text = audioTracks[i].label || audioTracks[i].language || `Audio Track ${{i + 1}}`;
                                audioSelector.appendChild(option);

                                if (audioTracks[i].enabled) {{
                                    option.selected = true;
                                }}
                            }}

                            audioSelector.addEventListener('change', (e) => {{
                                for (let i = 0; i < audioTracks.length; i++) {{
                                    audioTracks[i].enabled = (i == parseInt(e.target.value));
                                }}
                            }});
                        }}
                    }} else {{
                        // Solo hay una pista de audio (o el navegador no expone las demás):
                        // no hay nada que seleccionar.
                        if (audioSelector) audioSelector.style.display = 'none';
                        if (audioNote) audioNote.style.display = 'none';
                    }}
                }});
            }});
        </script>"""