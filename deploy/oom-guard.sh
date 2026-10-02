#!/usr/bin/env bash
# ============================================================================
# oom-guard.sh — mata instancias HUÉRFANAS de cloudflared.
#
# Por qué: cada arranque del bot levanta un `cloudflared tunnel`. Cuando el
# bot muere/reinicia sin limpiar (crash, kill, restart manual), quedan
# cloudflared fantasmas. Cada uno consume RAM y conexiones; en un VPS de
# 512MB-1GB con swap mínimo, eso es exactamente lo que produce:
#   - el bot "se marea" (no responde)
#   - SSH se queda cargando infinitamente (el kernel paginando a tope)
#
# Regla: se permite UNA instancia viva (la del servicio actual); cualquier
# proceso cloudflared TUNNEL cuyo padre YA no sea el bot (procesos adoptados
# por PID 1 = órfanes reales) se mata. Además se pone un tope total.
#
# Instalar junto con oom-guard.timer (ver ese archivo).
# ============================================================================
set -uo pipefail

MAX_TUNNELS="${MAX_TUNNELS:-1}"   # cuántos tuneles simultáneos se permiten
LOG_TAG="oom-guard"

log() { logger -t "$LOG_TAG" -- "$*" 2>/dev/null || echo "$*"; }

# 1) Órfanes: cloudflared en modo 'tunnel' cuyo PPID es 1 (systemd/init los
#    adoptó porque el bot murió sin recogerlos).
ORPHANS=$(ps -eo pid,ppid,args | awk '/[c]loudflared tunnel/ && $2 == 1 {print $1}')
for pid in $ORPHANS; do
    [ -n "$pid" ] || continue
    log "Matando cloudflared huérfano PID $pid"
    kill -TERM "$pid" 2>/dev/null || true
done

# 2) Exceso: si hay más de MAX_TUNNELS vivos, matar los MÁS VIEJOS primero
#    (son los fantasmas; el bueno suele ser el último en arrancar).
sleep 2  # dar tiempo a que los TERM hagan efecto antes de contar
ALL=$(pgrep -f "cloudflared tunnel" | tac)
COUNT=$(echo "$ALL" | grep -c '[0-9]' || true)
if [ "${COUNT:-0}" -gt "$MAX_TUNNELS" ]; then
    for pid in $(echo "$ALL" | tail -n +$((MAX_TUNNELS + 1))); do
        log "Exceso de tuneles ($COUNT > $MAX_TUNNELS): matando PID $pid"
        kill -KILL "$pid" 2>/dev/null || true
    done
fi

# 3) Aviso si la memoria libre es crítica (para que aparezca en journalctl)
MEM_AVAIL_KB=$(awk '/MemAvailable/ {print $2}' /proc/meminfo)
if [ "${MEM_AVAIL_KB:-999999}" -lt 80000 ]; then  # < ~80MB disponible
    log "ALERTA: memoria disponible muy baja (${MEM_AVAIL_KB} kB). Revisa servicios con 'free -m' y 'smem'/'htop'."
fi

exit 0
