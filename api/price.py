from http.server import BaseHTTPRequestHandler
import urllib.request
import urllib.parse
import json

def to_yahoo_symbol(code):
    code = code.strip()
    if '.' in code or code.startswith('^'):
        return code
    return f"{code}.TW"

class handler(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()

    def do_GET(self):
        try:
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)
            codes  = params.get('codes', ['2330'])[0].split(',')

            results = []
            for code in codes[:20]:  # 最多20檔
                code   = code.strip()
                symbol = to_yahoo_symbol(code)
                url    = (
                    f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(symbol)}"
                    f"?interval=1d&range=2d&includePrePost=false"
                )
                try:
                    req = urllib.request.Request(url, headers={
                        'User-Agent': 'Mozilla/5.0',
                        'Accept':     'application/json',
                    })
                    with urllib.request.urlopen(req, timeout=8) as resp:
                        raw = json.loads(resp.read().decode())

                    r    = raw.get('chart', {}).get('result', [{}])[0]
                    meta = r.get('meta', {})

                    price = round(meta.get('regularMarketPrice') or 0, 2)
                    prev  = round(meta.get('chartPreviousClose') or meta.get('previousClose') or 0, 2)
                    diff  = round(price - prev, 2)
                    pct   = round((diff / prev * 100) if prev else 0, 2)

                    results.append({
                        'code':    code,
                        'symbol':  symbol,
                        'name':    meta.get('longName') or meta.get('shortName') or code,
                        'price':   price,
                        'prev':    prev,
                        'diff':    diff,
                        'pct':     pct,
                        'up':      diff >= 0,
                        'high':    round(meta.get('regularMarketDayHigh') or 0, 2),
                        'low':     round(meta.get('regularMarketDayLow')  or 0, 2),
                        'open':    round(meta.get('regularMarketOpen')    or 0, 2),
                        'volume':  int(meta.get('regularMarketVolume')    or 0),
                        'mktcap':  meta.get('marketCap'),
                    })
                except:
                    results.append({'code': code, 'error': '查無資料'})

            self.send_json({'results': results, 'count': len(results)})

        except Exception as e:
            self.send_json({'error': str(e)}, 500)

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_cors_headers()
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin',  '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def log_message(self, format, *args):
        pass
