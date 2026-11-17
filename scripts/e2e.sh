#!/bin/sh
# Pruebas de punta a punta contra el stack real (Nginx -> Gunicorn -> Flask -> PostgreSQL).
# Requiere: docker compose up -d --build --wait
set -eu

BASE="http://localhost:${HTTP_PORT:-8080}"

pass() { printf '  ✅ %s\n' "$1"; }
fail() { printf '  ❌ %s\n' "$1"; exit 1; }
json() { python3 -c "import sys,json; print(json.load(sys.stdin)$1)"; }
status() { curl -s -o /dev/null -w '%{http_code}' "$@"; }

# expect_eq "descripción" "obtenido" "esperado"
expect_eq() {
  if [ "$2" = "$3" ]; then pass "$1"; else fail "$1 (esperado '$3', obtenido '$2')"; fi
}

# expect "descripción" comando...
expect() {
  desc="$1"; shift
  if "$@"; then pass "$desc"; else fail "$desc"; fi
}

has_header() { printf '%s' "$HDRS" | grep -qi "$1"; }
metrics_ok() {
  docker compose exec -T app python -c \
    "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/metrics').read().decode())" \
    | grep -q 'http_requests_total{.*endpoint="/api/notes"'
}

echo "▶ Salud"
expect_eq "liveness /healthz" "$(curl -fsS "$BASE/healthz" | json '["status"]')" ok
expect_eq "readiness /readyz (PostgreSQL)" "$(curl -fsS "$BASE/readyz" | json '["database"]')" ok

echo "▶ API"
ID=$(curl -fsS -X POST -H 'Content-Type: application/json' \
  -d '{"title":"e2e","body":"desde CI"}' "$BASE/api/notes" | json '["id"]')
pass "POST /api/notes -> id $ID"
expect_eq "GET /api/notes/$ID" "$(curl -fsS "$BASE/api/notes/$ID" | json '["body"]')" "desde CI"
expect_eq "validación devuelve 422" \
  "$(status -X POST -H 'Content-Type: application/json' -d '{}' "$BASE/api/notes")" 422

echo "▶ Nginx"
HDRS=$(curl -fsSI "$BASE/healthz")
expect "cabeceras de seguridad" has_header '^x-content-type-options: nosniff'
expect "X-Request-ID generado por Nginx y propagado" has_header '^x-request-id: [0-9a-f]\{32\}'
expect_eq "/metrics bloqueado al público" "$(status "$BASE/metrics")" 404

echo "▶ Observabilidad"
expect "métricas Prometheus (multiproceso) en red interna" metrics_ok

echo "▶ Persistencia"
docker compose restart app >/dev/null
docker compose up -d --wait app >/dev/null
expect_eq "los datos sobreviven al reinicio de la app" \
  "$(curl -fsS "$BASE/api/notes/$ID" | json '["title"]')" e2e

echo "✅ E2E OK"
