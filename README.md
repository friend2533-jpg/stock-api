# 台股技術分析 API 後端

Yahoo Finance 中繼 API，部署於 Vercel。

## API 端點

### 取得 K 線資料
```
GET /api/quote?code=2330&period=D
```
**參數：**
- `code` — 台股代號（例：2330、0050）
- `period` — 時間週期：`5m` `15m` `60m` `D` `W` `Y`

**回傳：**
```json
{
  "code": "2330",
  "name": "台積電",
  "currentPrice": 850.0,
  "previousClose": 838.0,
  "bars": [
    { "t": 1716192000, "o": 838, "h": 862, "l": 835, "c": 850, "v": 52000000 }
  ]
}
```

### 取得即時報價（多檔）
```
GET /api/price?codes=2330,2317,0050
```
**回傳：**
```json
{
  "results": [
    { "code": "2330", "name": "台積電", "price": 850, "diff": 12, "pct": 1.43, "up": true }
  ]
}
```

## 部署到 Vercel 步驟

1. 將此資料夾上傳到 GitHub（新建一個 repository）
2. 登入 Vercel → New Project → 選擇你的 GitHub repo
3. 直接點 Deploy（不需要任何額外設定）
4. 部署完成後取得你的網址，例如：`https://your-app.vercel.app`
5. 把網址填入 APP 的設定中即可

## 注意事項
- Yahoo Finance 資料延遲約 15 分鐘
- 分鐘線（5m/15m/60m）只有最近 60 天資料
- 日線/週線有完整歷史資料
- 免費使用，無需 API Key
