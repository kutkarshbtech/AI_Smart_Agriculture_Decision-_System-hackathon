#!/bin/bash
# ============================================================
# SwadeshAI — AWS Endpoint Test Script
# Tests all major API endpoints against the deployed ALB URL.
#
# Usage:
#   ./scripts/test_aws_endpoint.sh <BASE_URL>
#   ./scripts/test_aws_endpoint.sh http://swadesh-ai-alb-dev-123456.ap-south-1.elb.amazonaws.com
# ============================================================
set -euo pipefail

BASE_URL="${1:?Usage: ./scripts/test_aws_endpoint.sh <BASE_URL>}"
# Strip trailing slash
BASE_URL="${BASE_URL%/}"
API="${BASE_URL}/api/v1"

PASS=0
FAIL=0

# ── Helpers ──────────────────────────────────────────────────
green()  { echo -e "\033[32m$1\033[0m"; }
red()    { echo -e "\033[31m$1\033[0m"; }
yellow() { echo -e "\033[33m$1\033[0m"; }

check() {
    local name="$1"
    local method="$2"
    local url="$3"
    local data="${4:-}"
    local expected_code="${5:-200}"

    echo -n "  [TEST] ${name} ... "

    if [ "${method}" = "GET" ]; then
        HTTP_CODE=$(curl -s -o /tmp/swadesh_resp.json -w "%{http_code}" "${url}" --max-time 30)
    else
        HTTP_CODE=$(curl -s -o /tmp/swadesh_resp.json -w "%{http_code}" \
            -X POST "${url}" \
            -H "Content-Type: application/json" \
            -d "${data}" --max-time 30)
    fi

    if [ "${HTTP_CODE}" = "${expected_code}" ]; then
        green "PASS (${HTTP_CODE})"
        PASS=$((PASS + 1))
    else
        red "FAIL (got ${HTTP_CODE}, expected ${expected_code})"
        cat /tmp/swadesh_resp.json 2>/dev/null | head -5
        echo ""
        FAIL=$((FAIL + 1))
    fi
}

echo "========================================="
echo "  SwadeshAI AWS Endpoint Tests"
echo "  Target: ${BASE_URL}"
echo "========================================="
echo ""

# ── 1. Health ────────────────────────────────────────────────
echo "[1/8] Health Check"
check "GET /health" GET "${BASE_URL}/health"
echo ""

# ── 2. API Docs ──────────────────────────────────────────────
echo "[2/8] OpenAPI Docs"
check "GET /docs" GET "${BASE_URL}/docs"
echo ""

# ── 3. Quality — Simulate Assessment ────────────────────────
echo "[3/8] Quality — Simulated Assessment"
check "GET /quality/simulate/tomato" GET "${API}/quality/simulate/tomato"
echo ""

# ── 4. Pricing — Today's Market Price ────────────────────────
echo "[4/8] Pricing — Market Price"
check "GET /pricing/market/tomato" GET "${API}/pricing/market/tomato"
echo ""

# ── 5. Pricing — Price Recommendation ───────────────────────
echo "[5/8] Pricing — Price Recommendation"
check "POST /pricing/recommend" POST "${API}/pricing/recommend" \
    '{"crop_name":"tomato","quantity_kg":100,"quality_grade":"good","spoilage_risk":"low"}'
echo ""

# ── 6. Mandi — Live Prices ──────────────────────────────────
echo "[6/8] Mandi — Live Prices"
check "GET /pricing/mandi/prices/tomato" GET "${API}/pricing/mandi/prices/tomato"
echo ""

# ── 7. Chatbot ───────────────────────────────────────────────
echo "[7/8] Chatbot"
check "POST /chatbot/message" POST "${API}/chatbot/message" \
    '{"message":"What is the best time to sell tomatoes?","language":"en"}'
echo ""

# ── 8. Quality + Price — Simulate & Price ────────────────────
echo "[8/8] Quality + Price — Simulate & Price"
check "GET /quality/simulate-and-price/tomato" GET "${API}/quality/simulate-and-price/tomato"
echo ""

# ── Summary ──────────────────────────────────────────────────
echo "========================================="
if [ ${FAIL} -eq 0 ]; then
    green "  All ${PASS} tests PASSED!"
else
    yellow "  Results: ${PASS} passed, ${FAIL} failed"
fi
echo "========================================="

# Show sample response from health
echo ""
echo "Sample health response:"
curl -s "${BASE_URL}/health" | python3 -m json.tool 2>/dev/null || curl -s "${BASE_URL}/health"
echo ""

exit ${FAIL}
