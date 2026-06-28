# 🏆 FIFA World Cup 2026 — 自動更新系統

## ⚡ 系統概覽

呢個 repo 使用 **GitHub Actions** 每日自動更新世界盃賽果，完全唔需要你部電腦開住！

```
每日 23:00 HKT (15:00 UTC)
    ↓
GitHub Actions 自動觸發
    ↓
`update_worldcup.py` 搜尋最新賽果
    ↓
自動更新 `worldcup-2026.html` + `index.html`
    ↓
git commit + push 返去 repo
    ↓
GitHub Pages 自動更新網站 ✅
```

---

## 📂 檔案結構

| 檔案 | 用途 |
|------|------|
| `.github/workflows/daily-update.yml` | GitHub Actions 工作流程定義 |
| `update_worldcup.py` | Python 自動更新腳本 |
| `requirements.txt` | Python 依賴套件 |
| `worldcup-2026.html` | 主網站 HTML（含所有數據） |
| `index.html` | GitHub Pages 部署版本 |

---

## 🚀 如何使用

### 方法 A：自動（推薦 ✅）

1. Push 呢個 repo 去 GitHub
2. 確保 `Settings` → `Actions` → `General` → `Workflow permissions` 設為 `Read and write permissions`
3. 等每日 23:00 HKT，GitHub Actions 會自動跑
4. 你可以在 **Actions** tab 睇到每次執行嘅 log

### 方法 B：手動觸發

去 GitHub repo → **Actions** → 揀 `Daily World Cup 2026 Update` → 撳 **Run workflow**

---

## ⚙️ 自定義設定

### 改時間

編輯 `.github/workflows/daily-update.yml`：

```yaml
schedule:
  - cron: "0 15 * * *"  # UTC 時間（15:00 = HKT 23:00）
```

參考：
- `0 1 * * *` = 每日 09:00 HKT
- `0 8 * * *` = 每日 16:00 HKT
- `0 22 * * *` = 每日 06:00 HKT（翌日）

### 加 WeChat 通知

喺 GitHub repo `Settings` → `Secrets and variables` → `Actions` → 加 `WECHAT_WEBHOOK` secret，然後喺 workflow 入面 uncomment 通知部分。

---

## 🔍 監控 & 故障排除

- **睇 log**：GitHub repo → **Actions** tab → 揀個 run → 睇 Step details
- **手動重新跑**：Actions tab → 揀失敗嘅 run → **Re-run all jobs**
- **停用自動化**：去 Actions tab → 揀 workflow → **Disable workflow**

---

## ⚠️ 注意事項

- 目前 `update_worldcup.py` 使用 **FIFA API** 搜尋賽果。如果 FIFA API 改版，可能需要更新腳本。
- **小組積分 (DATA.groups)** 目前需要**手動更新**（腳本會自動開 GitHub Issue 提醒你）。
- 如果你嘅 repo 係 **private**，GitHub Actions 每月有 2000 分鐘免費額度。

---

## 🛠️ 本地測試

```bash
# 安裝依賴
pip install -r requirements.txt

# 執行更新腳本
python update_worldcup.py

# 檢查有無更新
git diff worldcup-2026.html
```

---

## 📞 支援

如有問題，可以：
1. 開 GitHub Issue
2. 或者問 Edward（edwardwanwhc-code）
