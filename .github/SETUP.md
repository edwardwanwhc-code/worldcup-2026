# GitHub Actions 自動更新設定指南

## 概述

呢個 GitHub Actions workflow 會每日自動喺以下時間更新世界盃賽程數據：
- **早上 10:00 HKT** (02:00 UTC)
- **晚上 10:00 HKT** (14:00 UTC)

## 設定步驟

### 1. 註冊 API Key（必需）

選擇以下其中一個免費 API 服務：

#### 選項 A: football-data.org（推薦）
1. 去 https://www.football-data.org/ 註冊免費帳號
2. 獲取 API Key
3. 喺 GitHub repo 入面，去 **Settings → Secrets and variables → Actions**
4. 新增 Repository secret：`FOOTBALL_DATA_API_KEY`

#### 選項 B: API-Football
1. 去 https://www.api-football.com/ 註冊
2. 獲取 API Key
3. 喺 GitHub repo 入面新增 Repository secret：`API_FOOTBALL_KEY`

### 2. 手動觸發 Workflow

你可以隨時手動觸發更新：
1. 去 GitHub repo 嘅 **Actions** 分頁
2. 選擇 **Update World Cup 2026 Scores**
3. 點擊 **Run workflow**
4. 選擇 API source（預設 football-data）
5. 點擊 **Run workflow**

### 3. 檢查運行狀態

- 去 GitHub repo 嘅 **Actions** 分頁
- 可以睇到每次運行嘅日誌
- 如果有錯誤，會顯示紅色 ❌
- 成功會顯示綠色 ✅

## 注意事項

### 免費額度限制
- **football-data.org**: 每分鐘 10 次呼叫，每日約 100 次
- **API-Football**: 每日 100 次呼叫

### 如果 API 冇數據
如果 API 暫時冇數據（例如比賽未開始），workflow 會正常完成，唔會更新任何嘢。

### 手動修正
如果你想手動更新分數（例如 API 數據有延遲）：
1. 直接修改 `worldcup-2026.html` 文件
2. Commit 同 push
3. GitHub Pages 會自動更新

## 故障排除

### Workflow 冇運行
- 檢查 GitHub Actions 有冇啟用（repo Settings → Actions → General）
- 檢查 cron 設定係咪正確

### API 錯誤
- 檢查 API key 係咪正確設定
- 檢查 API 免費額度係咪用完
- 檢查 API 服務狀態

### 想轉用其他 API
修改 workflow 文件入面嘅 `API_SOURCE` 環境變量：
- `football-data` - football-data.org
- `api-football` - API-Football
- `fifa` - FIFA API（未實現）

## 技術細節

### Workflow 檔案結構
```
.github/
├── workflows/
│   └── update-scores.yml    # GitHub Actions 定義
└── scripts/
    └── update_scores.py     # Python 更新腳本
```

### Python 腳本功能
- 支援多個 API 來源
- 自動更新比分、積分、射手榜
- 錯誤處理同重試機制
- 乾跑模式（dry run）用於測試

## 聯絡支援

如有問題，可以：
1. 檢查 GitHub Actions 日誌
2. 開一個 GitHub Issue
3. 或者繼續用 WorkBuddy 手動更新
