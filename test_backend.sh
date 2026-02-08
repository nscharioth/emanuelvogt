#!/bin/bash
# Backend Test Script für Phase 11 Migration
# Testet ob das Backend korrekt auf die neuen flat/ Dateien zugreift

echo "🧪 EMANUEL VOGT ARCHIVE - BACKEND TEST"
echo "======================================"
echo ""

# Farben für Output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Starte Backend im Hintergrund
echo "🚀 Starte Backend..."
cd "$(dirname "$0")"
python3 -m app.backend > /tmp/backend_test.log 2>&1 &
BACKEND_PID=$!

# Warte bis Backend bereit ist
echo "⏳ Warte auf Backend-Start (max. 10 Sekunden)..."
for i in {1..10}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Backend läuft (PID: $BACKEND_PID)${NC}"
        break
    fi
    sleep 1
    if [ $i -eq 10 ]; then
        echo -e "${RED}❌ Backend-Start fehlgeschlagen${NC}"
        kill $BACKEND_PID 2>/dev/null
        exit 1
    fi
done

echo ""
echo "📝 TEST 1: Werk mit Umlauten (ID 3 - Hör, hör, hör)"
echo "   URL: http://localhost:8000/pdf/3"
RESPONSE=$(curl -s -I http://localhost:8000/pdf/3 | head -n 1)
if echo "$RESPONSE" | grep -q "200 OK"; then
    echo -e "   ${GREEN}✅ ERFOLG - HTTP 200 OK${NC}"
    # Prüfe Content-Disposition Header
    DISPOSITION=$(curl -s -I http://localhost:8000/pdf/3 | grep -i "content-disposition" || echo "")
    if [ ! -z "$DISPOSITION" ]; then
        echo "   📎 $DISPOSITION"
    fi
else
    echo -e "   ${RED}❌ FEHLER - $RESPONSE${NC}"
fi

echo ""
echo "📝 TEST 2: Slug-basierter Zugriff"
echo "   URL: http://localhost:8000/pdf/by-slug/14a-hoer-hoer-hoer.pdf"
RESPONSE=$(curl -s -I http://localhost:8000/pdf/by-slug/14a-hoer-hoer-hoer.pdf | head -n 1)
if echo "$RESPONSE" | grep -q "200 OK"; then
    echo -e "   ${GREEN}✅ ERFOLG - HTTP 200 OK${NC}"
else
    echo -e "   ${RED}❌ FEHLER - $RESPONSE${NC}"
fi

echo ""
echo "📝 TEST 3: JPG-Datei (ID 204 - Pastorale für 3 Blockflöten)"
echo "   URL: http://localhost:8000/pdf/204"
RESPONSE=$(curl -s -I http://localhost:8000/pdf/204 | head -n 1)
if echo "$RESPONSE" | grep -q "200 OK"; then
    echo -e "   ${GREEN}✅ ERFOLG - HTTP 200 OK${NC}"
else
    echo -e "   ${RED}❌ FEHLER - $RESPONSE${NC}"
fi

echo ""
echo "📝 TEST 4: Normales Werk ohne Umlaute (ID 20)"
echo "   URL: http://localhost:8000/pdf/20"
RESPONSE=$(curl -s -I http://localhost:8000/pdf/20 | head -n 1)
if echo "$RESPONSE" | grep -q "200 OK"; then
    echo -e "   ${GREEN}✅ ERFOLG - HTTP 200 OK${NC}"
else
    echo -e "   ${RED}❌ FEHLER - $RESPONSE${NC}"
fi

echo ""
echo "📝 TEST 5: Werke-Liste API"
echo "   URL: http://localhost:8000/works"
RESPONSE=$(curl -s http://localhost:8000/works | python3 -c "import sys, json; data=json.load(sys.stdin); print(f\"Anzahl Werke: {len(data)}\")" 2>/dev/null)
if [ $? -eq 0 ]; then
    echo -e "   ${GREEN}✅ ERFOLG - $RESPONSE${NC}"
else
    echo -e "   ${RED}❌ FEHLER beim Abrufen der Werke-Liste${NC}"
fi

echo ""
echo "🔍 Backend-Logs (letzte 10 Zeilen):"
echo "──────────────────────────────────────"
tail -n 10 /tmp/backend_test.log
echo ""

# Stoppe Backend
echo "🛑 Stoppe Backend (PID: $BACKEND_PID)..."
kill $BACKEND_PID 2>/dev/null
wait $BACKEND_PID 2>/dev/null

echo ""
echo "======================================"
echo "✅ Tests abgeschlossen!"
echo ""
echo "💡 Hinweise:"
echo "   - Alle Tests sollten HTTP 200 OK zeigen"
echo "   - Für vollständigen Test im Browser öffnen:"
echo "   - http://localhost:8000"
echo ""
echo "🚀 Um Server dauerhaft zu starten:"
echo "   python3 -m app.backend"
