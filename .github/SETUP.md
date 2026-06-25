# GitHub Actions 自動更新設定指南

## 概述

呢個 GitHub Actions workflow 會每日自動喺以下時間更新世界盃賽程數據：
- **早上 10:00 HKT** (02:00 UTC)
- **晚上 10:00 HKT** (14:00 UTC)

## 設定步驟（只需做一次）

### 1. 添加 API Key 到 GitHub Secrets

1. 打開你嘅 GitHub repo：https://github.com/edwardwanwhc-code/worldcup-2026
2. 點擊 **Settings** → 左邊 **Secrets and variables** → **Actions**
3. 點擊 **New repository secret**
4. Name 填：`FOOTBALL_DATA_API_KEY`
5. Secret 填你嘅 API key：`71c12e35faec4428a8b6dae537bf69b4`
6. 點擊 **Add secret**

> ⚠️ 重要：API key 係敏感資料，千祈唔好直接寫入 code 或 commit 入去！

### 2. 確認 Actions 已啟用

1. 喺同一個 repo，去 **Settings** → **Actions** → **General**
2. 確保 **Actions permissions** 係 **Allow all actions and reusable workflows**
3. 確保 **Workflow permissions** 有 **Read and write permissions**（用嚟 commit & push）

### 3. 驗證 Workflow 運行

1. 去 GitHub repo 嘅 **Actions** 分頁
2. 你會見到 **Update World Cup 2026 Scores** workflow
3. 可以手動點擊 **Run workflow** 嚟測試

## 手動觸發更新

你可以隨時手動觸發：
1. 去 GitHub repo 嘅 **Actions** 分頁
2. 選擇 **Update World Cup 2026 Scores**
3. 點擊 **Run workflow**
4. 可選：選擇 Dry run（只測試唔會 commit）
5. 點擊 **Run workflow**

## 自動運行時間

Workflow 會每日自動喺以下時間運行：
- **02:00 UTC** = **10:00 HKT** (香港時間早上 10 點)
- **14:00 UTC** = **22:00 HKT** (香港時間晚上 10 點)

## 技術細節

### 更新內容
每次運行會：
1. 攞取前一日同當日嘅賽果
2. 更新 `index.html` 入面嘅 `DATA.matches` 比分同狀態
3. 更新 `DATA.groups` 積分榜
4. 更新 `DATA.scorers` 射手榜
5. 自動 commit 同 push（如果有改動）

### 如果冇新賽果
如果 API 冇新嘅已完成賽事，workflow 會正常完成，唔會做無謂嘅 commit。

### 免費額度限制
football-data.org 免費版：每分鐘 10 次呼叫，每日約 100 次。對於每日兩次更新嚟講完全足夠。

## 故障排除

### Workflow 冇運行
- 檢查 Actions 有冇啟用（repo Settings → Actions → General）
- 檢查 secrets 係咪正確設定

### API 錯誤
- 檢查 API key 係咪過期或無效
- 檢查 football-data.org 服務狀態

### 想手動修正分數
如果 API 數據有延遲或錯誤：
1. 直接修改 `index.html` 文件
2. Commit 同 push
3. GitHub Pages 會自動更新

## 聯絡支援

如有問題，可以：
1. 檢查 GitHub Actions 日誌（Actions 分頁 → 點擊 workflow run → 睇日誌）
2. 開一個 GitHub Issue
3. 或者繼續用 WorkBuddy 手動更新
