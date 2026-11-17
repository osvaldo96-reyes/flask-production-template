#!/bin/sh
# Pruebas de punta a punta contra el stack real (Nginx -> Gunicorn -> Flask -> PostgreSQL).
# Requiere: docker compose up -d --build --wait
set -eu

BASE="http://localhost:${HTTP_PORT:-8080}"
pass() { printf '  ✅ %s\n' "$1"; }
fail() { printf '  ❌ %s\n' "$1"; exit 1; }
json() { python3 -c "import sys,json; print(json.load(sys.stdin)$1)"; }

echo "▶ Salud"
[ "$(curl -fsS "$BASE/healthz" | json '["status"]')" = ok ] && pass "liveness /healthz" || fail "liveness"
[ "$(curl -fsS "$BASE/readyz" | json '["database"]')" = ok ] && pass "readiness /readyz (PostgreSQL)" || fail "readiness"

echo "▶ API"
ID=$(curl -fsS -X POST -H 'Content-Type: application/json' -d '{"title":"e2e","body":"desde CI"}' "$BASE/api/notes" | json '["id"]')
pass "POST /api/notes -> id $ID"
[ "$(curl -fsS "$BASE/api/notes/$ID" | json '["body"]')" = "desde CI" ] && pass "GET /api/notes/$ID" || fail "GET nota"
[ "$(curl -s -o /dev/null -w '%{http_code}' -X POST -H 'Content-Type: application/json' -d '{}' "$BASE/api/notes")" = 422 ] \
  && pass "validación devuelve 422" || fail "validación"

echo "▶ Nginx"
HDRS=$(curl -fsSI "$BASE/healthz")
echo "$HDRS" | grep -qi '^x-content-type-options: nosniff' && pass "cabeceras de seguridad" || fail "cabeceras de seguridad"
echo "$HDRS" | grep -qi '^x-request-id: [0-9a-f]\{32\}' && pass "X-Request-ID generado por Nginx y propagado" || fail "request id"
[ "$(curl -s -o /dev/null -w '%{http_code}' "$BASE/metrics")" = 404 ] && pass "/metrics bloqueado al público" || fail "/metrics expuesto"

echo "▶ Observabilidad"
docker compose exec -T app python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/metrics').read().decode())" \
  | grep -q 'http_requests_total{.*endpoint="/api/notes"' && pass "métricas Prometheus (multiproceso) en red interna" || fail "métricas"

echo "▶ Persistencia"
docker compose restart app >/dev/null
docker compose up -d --wait app >/dev/null
[ "$(curl -fsS "$BASE/api/notes/$ID" | json '["title"]')" = e2e ] && pass "los datos sobreviven al reinicio de la app" || fail "persistencia"

echo "✅ E2E OK"
