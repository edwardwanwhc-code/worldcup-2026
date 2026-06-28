#!/usr/bin/env python3
"""
FIFA World Cup 2026 - Daily Auto Update Script
Fetches latest match results and updates worldcup-2026.html
"""

import os
import re
import json
import requests
from datetime import datetime, timezone, timedelta

# ── CONFIG ────────────────────────────────────────────────────────
HTML_FILE = "worldcup-2026.html"
GITHUB_REPO = "edwardwanwhc-code/worldcup-2026"  # for API calls
HKT = timezone(timedelta(hours=8))
# ────────────────────────────────────────────────────────────────────


def fetch_latest_results():
    """
    Fetch latest match results from FIFA API or ESPN API.
    Returns a dict: { match_id: {"score": "X-X", "status": "finished"} }
    """
    results = {}

    # Try FIFA API first
    try:
        url = "https://api.fifa.com/api/competitions/17/matches?count=32"
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            for match in data.get("matches", []):
                home = match.get("homeTeam", {}).get("name", {}).get("fullName", "")
                away = match.get("awayTeam", {}).get("name", {}).get("fullName", "")
                score = match.get("score", {})
                if score.get("home") is not None and score.get("away") is not None:
                    mid = match.get("id")
                    results[mid] = {
                        "home": home,
                        "away": away,
                        "score": f"{score['home']}-{score['away']}",
                        "status": "finished"
                    }
    except Exception as e:
        print(f"[WARN] FIFA API failed: {e}")

    # Fallback: ESPN API
    if not results:
        try:
            url = "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.worldq/scoreboard"
            resp = requests.get(url, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                for event in data.get("events", []):
                    if event.get("status", {}).get("type", {}).get("completed"):
                        competitors = event.get("competitions", [{}])[0].get("competitors", [])
                        # parse score...
                        # (ESPN API structure is complex, using FIFA as primary)
                        pass
        except Exception as e:
            print(f"[WARN] ESPN API failed: {e}")

    return results


def load_html_data(html_path):
    """
    Read worldcup-2026.html and extract DATA.matches and DATA.groups.
    Returns (matches_list, groups_dict, full_html, matches_start, matches_end).
    """
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    # Find DATA.matches array
    matches_pattern = r"(const DATA = \{.*?matches:\s*\[)(.*?)(\],\s*\n\s*scorers:)"
    groups_pattern = r"(groups:\s*\{)(.*?)(\},\s*\n\s*// REAL 2026)"

    # Use a simpler approach: eval-save the JS object
    # Find the DATA block
    data_start = html.find("const DATA = {")
    if data_start == -1:
        raise ValueError("Could not find 'const DATA = {' in HTML")

    # Find end of DATA object (before // ======= or function)
    # We'll extract matches and groups via regex on the raw text
    matches = []

    # Extract matches via regex
    match_pattern = re.compile(
        r"\{ id:(\d+),\s*date:\"(.*?)\",\s*time:\"(.*?)\",\s*group:\"(.*?)\",\s*homeTeam:\"(.*?)\",\s*homeFlag:\"(.*?)\",\s*awayTeam:\"(.*?)\",\s*awayFlag:\"(.*?)\",\s*venue:\"(.*?)\",\s*score:(null|\"\d+-\d+\"),\s*status:\"(.*?)\"\s*\}"
    )

    for m in match_pattern.finditer(html):
        mid = int(m.group(1))
        score_raw = m.group(10)
        score = None if score_raw == "null" else score_raw.strip('"')
        status = m.group(11)
        matches.append({
            "id": mid,
            "date": m.group(2),
            "time": m.group(3),
            "group": m.group(4),
            "homeTeam": m.group(5),
            "awayTeam": m.group(7),
            "score": score,
            "status": status,
        })

    print(f"[INFO] Loaded {len(matches)} matches from HTML")
    return matches, html


def update_matches_in_html(html, new_results):
    """
    Given the HTML string and a dict of new results,
    update score:null → score:"X-X" and status:"upcoming" → status:"finished".
    Returns (updated_html, num_updated).
    """
    num_updated = 0

    for match_id, result in new_results.items():
        score_str = result["score"]
        # Match the exact match block in HTML
        # Pattern: id:67, ... score:null, status:"upcoming"
        pattern = re.compile(
            r"(\{ id:" + str(match_id) + r",[\s\S]*?score:)null,\s*status:\"upcoming\""
        )
        replacement = r"\1\"" + score_str + r"\", status:\"finished\""
        new_html, n = re.subn(pattern, replacement, html)
        if n > 0:
            html = new_html
            num_updated += 1
            print(f"[OK] Updated match id={match_id}: score={score_str}")
        else:
            # Maybe already updated?
            pattern2 = re.compile(
                r"(\{ id:" + str(match_id) + r",[\s\S]*?score:\"\d+-\d+\",\s*status:\"finished\")"
            )
            if pattern2.search(html):
                print(f"[SKIP] Match id={match_id} already updated")
            else:
                print(f"[WARN] Could not find match id={match_id} with score:null")

    return html, num_updated


def update_groups_in_html(html, updated_match_ids):
    """
    TODO: Re-calculate group standings based on updated matches.
    For now, this is a placeholder — group updates are done manually
    because they require full group logic.
    """
    # In production, you'd recalculate p/w/d/l/gf/ga/gd/pts for each team
    # For safety, we skip auto group update and notify via issue
    if updated_match_ids:
        print(f"[INFO] Group standings may need manual update for match IDs: {updated_match_ids}")
    return html


def write_html(html_path, html):
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[OK] Written updated HTML to {html_path}")


def create_github_issue_if_manual_needed(updated_ids):
    """Create a GitHub issue if group standings need manual update."""
    if not updated_ids:
        return
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        return
    url = f"https://api.github.com/repos/{GITHUB_REPO}/issues"
    headers = {"Authorization": f"token {token}"}
    body = f"""## ⚠️ 需要手動更新小組積分

以下比賽已自動更新比分，但 **小組積分 (DATA.groups) 需要手動更新**：

{chr(10).join(f"- Match id={mid}" for mid in updated_ids)}

請更新 `worldcup-2026.html` 中的 `DATA.groups` 部分。

> 此 issue 由 GitHub Actions 自動建立。
"""
    data = {
        "title": f"📊 小組積分需手動更新 ({datetime.now(HKT).strftime('%Y-%m-%d')})",
        "body": body,
        "labels": ["manual-update-needed"]
    }
    try:
        resp = requests.post(url, headers=headers, json=data, timeout=10)
        if resp.status_code == 201:
            print(f"[OK] Created GitHub issue for manual group update")
        else:
            print(f"[WARN] Failed to create issue: {resp.status_code} {resp.text}")
    except Exception as e:
        print(f"[WARN] Could not create GitHub issue: {e}")


def main():
    print(f"🏆 FIFA World Cup 2026 — Daily Auto Update")
    print(f"⏰ Run time: {datetime.now(HKT).strftime('%Y-%m-%d %H:%M HKT')}")
    print("=" * 50)

    html_path = os.path.join(os.path.dirname(__file__), HTML_FILE)
    if not os.path.exists(html_path):
        print(f"[ERROR] HTML file not found: {html_path}")
        return

    # Step 1: Load current data
    matches, html = load_html_data(html_path)

    # Step 2: Fetch latest results
    print("\n[STEP 1] Fetching latest match results...")
    new_results = fetch_latest_results()

    if not new_results:
        print("[INFO] No new results found. Checking for upcoming matches to update...")
        # Try web scraping as fallback
        # (Implement fallback scraper here if needed)
        print("[INFO] No updates needed. Exiting.")
        return

    print(f"[INFO] Found {len(new_results)} new result(s)")

    # Step 3: Update HTML
    print("\n[STEP 2] Updating HTML...")
    html, num_updated = update_matches_in_html(html, new_results)

    if num_updated == 0:
        print("[INFO] No matches were updated (may already be up-to-date). Exiting.")
        return

    # Step 4: Update groups (placeholder)
    print("\n[STEP 3] Checking group standings...")
    html = update_groups_in_html(html, list(new_results.keys()))

    # Step 5: Write back
    print("\n[STEP 4] Writing updated HTML...")
    write_html(html_path, html)

    # Step 6: Create GitHub issue for manual group update
    print("\n[STEP 5] Creating notification issue (if needed)...")
    create_github_issue_if_manual_needed(list(new_results.keys()))

    print("\n✅ Update complete!")


if __name__ == "__main__":
    main()
