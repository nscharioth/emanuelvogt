#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate

python -m app.backend > /tmp/backend_test.log 2>&1 &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"
sleep 3

echo ""
echo "TEST 1: Werk 3"
curl -s -o /tmp/test1.pdf -w "%{http_code}" http://localhost:8000/pdf/3
echo ""

echo "TEST 2: Slug URL"  
curl -s -o /tmp/test2.pdf -w "%{http_code}" http://localhost:8000/pdf/by-slug/14a-hoer-hoer-hoer.pdf
echo ""

echo "TEST 3: JPG"
curl -s -o /tmp/test3.jpg -w "%{http_code}" http://localhost:8000/pdf/204
echo ""

echo ""
echo "Dateien:"
ls -lh /tmp/test*.pdf /tmp/test*.jpg 2>/dev/null | awk '{print $9, $5}'

echo ""
echo "Logs:"
tail -10 /tmp/backend_test.log

kill $BACKEND_PID 2>/dev/null
deactivate
rm -f /tmp/test*.pdf /tmp/test*.jpg
