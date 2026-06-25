#!/usr/bin/env python3
"""
World Cup 2026 Score Updater

This script fetches the latest match results from football-data.org API and updates
the worldcup-2026.html file with new scores, standings, and scorers.

Environment Variables:
    FOOTBALL_DATA_API_KEY: API key for football-data.org
    DRY_RUN: If 'true', don't write changes to HTML
"""

import json
import os
import re
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import requests


# Constants
HTML_FILE = "index.html"
HKT_OFFSET = timedelta(hours=8)


# Team name mapping: English (from API) -> Chinese (from HTML)
TEAM_NAME_MAP = {
    "Mexico": "墨西哥",
    "South Korea": "韓國",
    "Czech Republic": "捷克",
    "South Africa": "南非",
    "Canada": "加拿大",
    "Switzerland": "瑞士",
    "Bosnia & Herzegovina": "波黑",
    "Bosnia and Herzegovina": "波黑",
    "Qatar": "卡塔爾",
    "Brazil": "巴西",
    "Morocco": "摩洛哥",
    "Scotland": "蘇格蘭",
    "Haiti": "海地",
    "United States": "美國",
    "USA": "美國",
    "Australia": "澳大利亞",
    "Paraguay": "巴拉圭",
    "Turkey": "土耳其",
    "Germany": "德國",
    "Ivory Coast": "象牙海岸",
    "Côte d'Ivoire": "象牙海岸",
    "Ecuador": "厄瓜多爾",
    "Curacao": "庫拉索",
    "Netherlands": "荷蘭",
    "Japan": "日本",
    "Sweden": "瑞典",
    "Tunisia": "突尼斯",
    "Egypt": "埃及",
    "Iran": "伊朗",
    "Belgium": "比利時",
    "New Zealand": "新西蘭",
    "Spain": "西班牙",
    "Uruguay": "烏拉圭",
    "Cape Verde": "佛得角",
    "Saudi Arabia": "沙特阿拉伯",
    "France": "法國",
    "Norway": "挪威",
    "Senegal": "塞內加爾",
    "Iraq": "伊拉克",
    "Argentina": "阿根廷",
    "Austria": "奧地利",
    "Algeria": "阿爾及利亞",
    "Jordan": "約旦",
    "Colombia": "哥倫比亞",
    "Portugal": "葡萄牙",
    "DR Congo": "剛果民主",
    "Congo DR": "剛果民主",
    "Democratic Republic of the Congo": "剛果民主",
    "Uzbekistan": "烏茲別克",
    "England": "英格蘭",
    "Ghana": "加納",
    "Croatia": "克羅地亞",
    "Panama": "巴拿馬",
}

# Group mapping: API format -> HTML format
GROUP_MAP = {
    "GROUP_A": "A組",
    "GROUP_B": "B組",
    "GROUP_C": "C組",
    "GROUP_D": "D組",
    "GROUP_E": "E組",
    "GROUP_F": "F組",
    "GROUP_G": "G組",
    "GROUP_H": "H組",
    "GROUP_I": "I組",
    "GROUP_J": "J組",
    "GROUP_K": "K組",
    "GROUP_L": "L組",
}

# Reverse group mapping
GROUP_MAP_REVERSE = {v: k for k, v in GROUP_MAP.items()}


def get_api_key() -> Optional[str]:
    """Get football-data.org API key from environment."""
    return os.environ.get("FOOTBALL_DATA_API_KEY")


def fetch_matches(api_key: str, date_from: str, date_to: str) -> List[Dict]:
    """Fetch WC 2026 matches from football-data.org for a date range."""
    url = "https://api.football-data.org/v4/competitions/WC/matches"
    headers = {"X-Auth-Token": api_key}
    params = {"dateFrom": date_from, "dateTo": date_to}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        matches = data.get("matches", [])
        print(f"  API returned {len(matches)} match(es)")
        return matches
    except requests.exceptions.RequestException as e:
        print(f"  Error fetching matches: {e}")
        return []
    except json.JSONDecodeError as e:
        print(f"  Error parsing API response: {e}")
        return []


def fetch_standings(api_key: str) -> Dict[str, List[Dict]]:
    """Fetch WC 2026 group standings from football-data.org."""
    url = "https://api.football-data.org/v4/competitions/WC/standings"
    headers = {"X-Auth-Token": api_key}

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        standings = data.get("standings", [])

        result = {}
        for standing in standings:
            group_id = standing.get("group", "")
            if group_id in GROUP_MAP:
                html_group = GROUP_MAP[group_id]
                table = standing.get("table", [])
                result[html_group] = table

        return result
    except requests.exceptions.RequestException as e:
        print(f"  Error fetching standings: {e}")
        return {}
    except json.JSONDecodeError as e:
        print(f"  Error parsing standings response: {e}")
        return {}


def fetch_scorers(api_key: str) -> List[Dict]:
    """Fetch WC 2026 top scorers from football-data.org."""
    url = "https://api.football-data.org/v4/competitions/WC/scorers"
    headers = {"X-Auth-Token": api_key}

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        scorers = data.get("scorers", [])
        print(f"  API returned {len(scorers)} scorer(s)")
        return scorers
    except requests.exceptions.RequestException as e:
        print(f"  Error fetching scorers: {e}")
        return []
    except json.JSONDecodeError as e:
        print(f"  Error parsing scorers response: {e}")
        return []


def update_match_scores(html_content: str, matches: List[Dict]) -> str:
    """Update match scores and status in the HTML content."""
    lines = html_content.split("\n")
    updated_count = 0

    for match in matches:
        match_id = match.get("id")
        status = match.get("status", "")
        score_data = match.get("score", {})
        full_time = score_data.get("fullTime", {})
        home_goals = full_time.get("home")
        away_goals = full_time.get("away")

        # Only update finished matches with a valid score
        if status != "FINISHED":
            continue
        if home_goals is None or away_goals is None:
            continue

        score_str = f"{home_goals}-{away_goals}"

        # Find and update the match line
        for i, line in enumerate(lines):
            if f"id:{match_id}," in line:
                # Check if already has the same score
                if f'score:"{score_str}"' in line:
                    print(f"    Match {match_id}: already up-to-date ({score_str})")
                    break

                # Update score
                if "score:null" in line:
                    line = line.replace("score:null", f'score:"{score_str}"')
                else:
                    # Replace existing score
                    line = re.sub(r'score:"[^"]*"', f'score:"{score_str}"', line)

                # Update status
                if 'status:"upcoming"' in line:
                    line = line.replace('status:"upcoming"', 'status:"finished"')
                elif 'status:"live"' in line:
                    line = line.replace('status:"live"', 'status:"finished"')

                lines[i] = line
                updated_count += 1
                print(f"    Match {match_id}: updated to {score_str} (finished)")
                break

    print(f"  Updated {updated_count} match(es)")
    return "\n".join(lines)


def update_group_standings(html_content: str, standings: Dict[str, List[Dict]]) -> str:
    """Update group standings in the HTML content."""
    lines = html_content.split("\n")
    updated_count = 0

    for group_name, teams in standings.items():
        for team_data in teams:
            team_info = team_data.get("team", {})
            team_name_en = team_info.get("name", "")
            team_name_cn = TEAM_NAME_MAP.get(team_name_en)

            if not team_name_cn:
                print(f"    Warning: No mapping for team '{team_name_en}'")
                continue

            # Find the team line in the HTML
            p = team_data.get("playedGames", 0)
            w = team_data.get("won", 0)
            d = team_data.get("draw", 0)
            l = team_data.get("lost", 0)
            gf = team_data.get("goalsFor", 0)
            ga = team_data.get("goalsAgainst", 0)
            gd = team_data.get("goalDifference", 0)
            pts = team_data.get("points", 0)

            for i, line in enumerate(lines):
                if f'eng: "{team_name_en}"' in line or f'eng:"{team_name_en}"' in line:
                    # Check if stats are already up to date
                    current_stats = re.search(r'p:(\d+), w:(\d+), d:(\d+), l:(\d+), gf:(\d+), ga:(\d+), gd:([-\d]+), pts:(\d+)', line)
                    if current_stats:
                        current = [int(current_stats.group(j)) for j in range(1, 9)]
                        new_stats = [p, w, d, l, gf, ga, gd, pts]
                        if current == new_stats:
                            break

                    # Update stats
                    new_stats_str = f"p:{p}, w:{w}, d:{d}, l:{l}, gf:{gf}, ga:{ga}, gd:{gd}, pts:{pts}"
                    line = re.sub(r'p:\d+, w:\d+, d:\d+, l:\d+, gf:\d+, ga:\d+, gd:[-\d]+, pts:\d+', new_stats_str, line)
                    lines[i] = line
                    updated_count += 1
                    print(f"    {team_name_cn} ({group_name}): stats updated")
                    break

    print(f"  Updated {updated_count} team stat(s)")
    return "\n".join(lines)


def update_scorers(html_content: str, scorers: List[Dict]) -> str:
    """Update top scorers in the HTML content."""
    if not scorers:
        return html_content

    lines = html_content.split("\n")
    updated_count = 0

    # Find the scorers array section
    scorers_start = None
    scorers_end = None
    for i, line in enumerate(lines):
        if "scorers: [" in line:
            scorers_start = i
        if scorers_start is not None and "]" in line and scorers_end is None:
            scorers_end = i
            break

    if scorers_start is None or scorers_end is None:
        print("  Warning: Could not find scorers array in HTML")
        return html_content

    # Process each scorer
    for scorer_data in scorers:
        player = scorer_data.get("player", {})
        player_name = player.get("name", "")
        goals = scorer_data.get("goals", 0)
        team_info = scorer_data.get("team", {})
        team_name_en = team_info.get("name", "")
        team_name_cn = TEAM_NAME_MAP.get(team_name_en, team_name_en)

        if not player_name or goals == 0:
            continue

        # Try to find existing scorer by name (English or Chinese)
        found = False
        for i in range(scorers_start + 1, scorers_end):
            if f'eng:"{player_name}"' in lines[i] or f'eng: "{player_name}"' in lines[i]:
                # Check if goals count changed
                current_goals = re.search(r'goals:(\d+)', lines[i])
                if current_goals and int(current_goals.group(1)) == goals:
                    found = True
                    break

                # Update goals
                lines[i] = re.sub(r'goals:\d+', f'goals:{goals}', lines[i])
                updated_count += 1
                print(f"    {player_name}: goals updated to {goals}")
                found = True
                break
            elif player_name in lines[i]:
                # Partial match (name might be in Chinese)
                current_goals = re.search(r'goals:(\d+)', lines[i])
                if current_goals and int(current_goals.group(1)) == goals:
                    found = True
                    break

                lines[i] = re.sub(r'goals:\d+', f'goals:{goals}', lines[i])
                updated_count += 1
                print(f"    {player_name} (CN): goals updated to {goals}")
                found = True
                break

        # TODO: Add new scorers if not found - requires flag URL lookup
        # For now, we only update existing scorers
        if not found:
            print(f"    {player_name}: not found in existing scorers (skipping)")

    print(f"  Updated {updated_count} scorer(s)")
    return "\n".join(lines)


def main():
    """Main entry point."""
    print("=" * 60)
    print("World Cup 2026 Score Updater")
    print("=" * 60)

    # Check API key
    api_key = get_api_key()
    if not api_key:
        print("\n❌ FOOTBALL_DATA_API_KEY not set!")
        print("\nSetup:")
        print("1. Get a free API key from https://www.football-data.org/")
        print("2. Add it as a GitHub secret: FOOTBALL_DATA_API_KEY")
        sys.exit(1)
    print("✅ API key configured")

    # Check dry run mode
    dry_run = os.environ.get("DRY_RUN", "false").lower() == "true"
    if dry_run:
        print("⚠️  DRY RUN MODE - No changes will be written\n")
    else:
        print("")

    # Calculate dates to check (yesterday and today in HKT)
    now = datetime.now(HKT_OFFSET)
    today = now.strftime("%Y-%m-%d")
    yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d")

    print(f"📅 Checking matches for: {yesterday} to {today} (HKT)")

    # Fetch matches from API
    matches = fetch_matches(api_key, yesterday, today)
    if not matches:
        print("\nℹ️  No matches found to update")
        print("=" * 60)
        return

    # Filter to finished matches with scores
    finished_matches = [
        m for m in matches
        if m.get("status") == "FINISHED"
        and m.get("score", {}).get("fullTime", {}).get("home") is not None
    ]

    if not finished_matches:
        print("\nℹ️  No finished matches with scores found")
        print("=" * 60)
        return

    print(f"\n📝 Found {len(finished_matches)} finished match(es) to update")

    # Read HTML file
    try:
        with open(HTML_FILE, "r", encoding="utf-8") as f:
            html_content = f.read()
        print(f"✅ Read {HTML_FILE} ({len(html_content)} chars)")
    except FileNotFoundError:
        print(f"❌ Error: {HTML_FILE} not found")
        sys.exit(1)

    # Update match scores
    print("\n🏟️  Updating match scores...")
    html_content = update_match_scores(html_content, finished_matches)

    # Update group standings
    print("\n📊 Updating group standings...")
    standings = fetch_standings(api_key)
    if standings:
        html_content = update_group_standings(html_content, standings)
    else:
        print("  No standings data available")

    # Update scorers
    print("\n⚽ Updating top scorers...")
    scorers = fetch_scorers(api_key)
    if scorers:
        html_content = update_scorers(html_content, scorers)
    else:
        print("  No scorers data available")

    # Write updated HTML
    if not dry_run:
        with open(HTML_FILE, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"\n✅ Written updated {HTML_FILE}")
    else:
        print(f"\n🔍 DRY RUN: Would write {HTML_FILE}")

    print("\n" + "=" * 60)
    print("Update complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
