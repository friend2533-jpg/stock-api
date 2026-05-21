from http.server import BaseHTTPRequestHandler
import urllib.request
import urllib.parse
import json
import re

# 台股代號轉Yahoo格式 (例: 2330 -> 2330.TW)
def to_yahoo_symbol(code):
    code = code.strip()
    if '.' in code:
        return code  # 已有後綴
    # ETF或指數
    if code.startswith('^'):
        return code
    return f"{code}.TW"

# 時間週期對應Yahoo interval/range
PERIOD_MAP = {
    '5m':  {'interval': '5m',  'range': '5d'},
    '15m': {'interval': '15m', 'range': '10d'},
    '60m': {'interval': '60m', 'range': '30d'},
    'D':   {'interval': '1d',  'range': '1y'},
    'W':   {'interval': '1wk', 'range': '5y'},
    'Y':   {'interval': '1mo', 'range': '10y'},
}

class handler(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()

    def do_GET(self):
        try:
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)

            # 取得參數
            code   = params.get('code',   ['2330'])[0]
            period = params.get('period', ['D'])[0]

            symbol = to_yahoo_symbol(code)
            pm     = PERIOD_MAP.get(period, PERIOD_MAP['D'])

            # 呼叫 Yahoo Finance v8 API
            url = (
                f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(symbol)}"
                f"?interval={pm['interval']}&range={pm['range']}"
                f"&includePrePost=false&events=div,splits"
            )

            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json',
            })

            with urllib.request.urlopen(req, timeout=10) as resp:
                raw = json.loads(resp.read().decode())

            result = raw.get('chart', {}).get('result', [])
            if not result:
                self.send_json({'error': '查無資料', 'code': code}, 404)
                return

            r         = result[0]
            meta      = r.get('meta', {})
            timestamps= r.get('timestamp', [])
            quotes    = r.get('indicators', {}).get('quote', [{}])[0]

            opens   = quotes.get('open',   [])
            highs   = quotes.get('high',   [])
            lows    = quotes.get('low',    [])
            closes  = quotes.get('close',  [])
            volumes = quotes.get('volume', [])

            # 過濾 None 值
            bars = []
            for i, ts in enumerate(timestamps):
                if i >= len(closes) or closes[i] is None:
                    continue
                bars.append({
                    't': ts,
                    'o': round(opens[i]   or 0, 2),
                    'h': round(highs[i]   or 0, 2),
                    'l': round(lows[i]    or 0, 2),
                    'c': round(closes[i]  or 0, 2),
                    'v': int(volumes[i]   or 0),
                })

            data = {
                'code':          code,
                'symbol':        symbol,
                'name':          meta.get('longName') or meta.get('shortName') or code,
                'currency':      meta.get('currency', 'TWD'),
                'exchange':      meta.get('exchangeName', ''),
                'currentPrice':  round(meta.get('regularMarketPrice') or 0, 2),
                'previousClose': round(meta.get('chartPreviousClose') or meta.get('previousClose') or 0, 2),
                'period':        period,
                'interval':      pm['interval'],
                'bars':          bars,
                'total':         len(bars),
            }

            self.send_json(data)

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
        pass  # 關閉預設log
