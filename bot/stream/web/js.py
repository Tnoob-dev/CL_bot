def scripts()->str:
    return f"""<script src="https://cdn.plyr.io/3.7.8/plyr.polyfilled.js"></script>
        <script>
            document.addEventListener('DOMContentLoaded', () => {{
                const video = document.getElementById('player');
                const source = document.getElementById('player-source');
                const overlay = document.getElementById('reconnect-overlay');
                const overlayText = document.getElementById('reconnect-text');
                const qualitySelector = document.getElementById('quality-selector');
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

                video.addEventListener('waiting', () => {{
                    clearTimeout(stallTimer);
                    // Si el video se queda "esperando" datos por más de 8s, asumimos
                    // que la conexión se cortó y forzamos una reconexión.
                    stallTimer = setTimeout(() => {{
                        if (video.paused) return;
                        attemptReconnect();
                    }}, 8000);
                    showOverlay('Cargando...');
                }});

                video.addEventListener('playing', () => {{
                    clearTimeout(stallTimer);
                    reconnectAttempts = 0;
                    hideOverlay();
                }});

                // ---------- Selector de calidad (limita velocidad de envío) ----------
                if (qualitySelector) {{
                    qualitySelector.addEventListener('change', (e) => {{
                        const url = currentBaseUrl();
                        url.searchParams.set('quality', e.target.value);
                        showOverlay('Cambiando calidad...');
                        reloadPreservingPosition(url, true);
                    }});
                }}

                // ---------- Subtítulos por archivo local ----------
                document.getElementById('sub-upload').addEventListener('change', function(e) {{
                    const file = e.target.files[0];
                    if (!file) return;

                    const url = URL.createObjectURL(file);
                    const track = document.createElement('track');
                    track.kind = 'captions';
                    track.label = file.name;
                    track.srclang = 'es';
                    track.src = url;
                    track.default = true;

                    Array.from(video.querySelectorAll('track')).forEach(t => t.remove());
                    video.appendChild(track);

                    // Animación de éxito
                    const label = this.parentElement;
                    const originalText = label.innerHTML;
                    label.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="#4ade80" stroke-width="2"><path d="M20 6L9 17l-5-5"/></svg> Cargado con éxito`;
                    label.style.borderColor = '#4ade80';
                    label.style.color = '#4ade80';

                    setTimeout(() => {{
                        track.mode = 'showing';
                        setTimeout(() => {{
                            label.innerHTML = originalText;
                            label.style.borderColor = '';
                            label.style.color = '';
                        }}, 3000);
                    }}, 500);
                }});

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