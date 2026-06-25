#!/usr/bin/env python3
"""
World Cup 2026 Score Updater

This script fetches the latest match results from API-Football or football-data.org
and updates the worldcup-2026.html file with new scores, standings, and scorers.

Environment Variables:
    API_FOOTBALL_KEY: API key for API-Football (default source)
    FOOTBALL_DATA_API_KEY: API key for football-data.org (fallback)
    API_SOURCE: Which API to use (api-football, football-data)
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


def get_configured_source() -> str:
    """Get the configured API source."""
    return os.environ.get("API_SOURCE", "api-football").lower()


def get_api_football_key() -> Optional[str]:
    """Get API-Football key from environment."""
    return os.environ.get("API_FOOTBALL_KEY")


def get_football_data_key() -> Optional[str]:
    """Get football-data.org key from environment."""
    return os.environ.get("FOOTBALL_DATA_API_KEY")


# ==================== API-Football DataSource ====================

class APIFootballSource:
    """API-Football client (v3)."""
    
    BASE_URL = "https://v3.football.api-sports.io"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "x-apisports-key": api_key
        }
    
    def fetch_matches(self, date: str) -> List[Dict]:
        """Fetch WC 2026 matches for a specific date."""
        url = f"{self.BASE_URL}/fixtures"
        params = {
            "league": 1,      # World Cup
            "season": 2026,
            "date": date
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            matches = data.get("response", [])
            print(f"  API-Football returned {len(matches)} match(es)")
            return matches
        except requests.exceptions.RequestException as e:
            print(f"  Error fetching matches from API-Football: {e}")
            return []
    
    def fetch_standings(self) -> Dict[str, List[Dict]]:
        """Fetch WC 2026 group standings."""
        url = f"{self.BASE_URL}/standings"
        params = {
            "league": 1,
            "season": 2026
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            result = {}
            for league in data.get("response", []):
                league_data = league.get("league", {})
                for standing in league_data.get("standings", []):
                    for group_data in standing:
                        group_name = group_data.get("group", "")
                        if group_name.startswith("Group "):
                            group_letter = group_name.replace("Group ", "")
                            html_group = f"{group_letter}組"
                            result[html_group] = group_data.get("table", [])
            return result
        except requests.exceptions.RequestException as e:
            print(f"  Error fetching standings from API-Football: {e}")
            return {}
    
    def fetch_scorers(self) -> List[Dict]:
        """Fetch WC 2026 top scorers."""
        url = f"{self.BASE_URL}/players/topscorers"
        params = {
            "league": 1,
            "season": 2026
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            scorers = data.get("response", [])
            print(f"  API-Football returned {len(scorers)} scorer(s)")
            return scorers
        except requests.exceptions.RequestException as e:
            print(f"  Error fetching scorers from API-Football: {e}")
            return []


# ==================== football-data.org DataSource (fallback) ====================

class FootballDataSource:
    """football-data.org API client."""
    
    BASE_URL = "https://api.football-data.org/v4"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {"X-Auth-Token": api_key}
    
    def fetch_matches(self, date: str) -> List[Dict]:
        """Fetch matches for a specific date."""
        url = f"{self.BASE_URL}/competitions/WC/matches"
        params = {"dateFrom": date, "dateTo": date}
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            matches = data.get("matches", [])
            print(f"  football-data returned {len(matches)} match(es)")
            return matches
        except requests.exceptions.RequestException as e:
            print(f"  Error fetching matches from football-data: {e}")
            return []
    
    def fetch_standings(self) -> Dict[str, List[Dict]]:
        """Fetch group standings."""
        url = f"{self.BASE_URL}/competitions/WC/standings"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            result = {}
            for standing in data.get("standings", []):
                group_id = standing.get("group", "")
                if group_id in GROUP_MAP:
                    html_group = GROUP_MAP[group_id]
                    result[html_group] = standing.get("table", [])
            return result
        except requests.exceptions.RequestException as e:
            print(f"  Error fetching standings from football-data: {e}")
            return {}
    
    def fetch_scorers(self) -> List[Dict]:
        """Fetch top scorers."""
        url = f"{self.BASE_URL}/competitions/WC/scorers"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            scorers = data.get("scorers", [])
            print(f"  football-data returned {len(scorers)} scorer(s)")
            return scorers
        except requests.exceptions.RequestException as e:
            print(f"  Error fetching scorers from football-data: {e}")
            return []


# ==================== DataSource Factory ====================

def get_data_source():
    """Get the configured data source with fallback."""
    source = get_configured_source()
    
    if source == "api-football":
        api_key = get_api_football_key()
        if api_key:
            return APIFootballSource(api_key), "api-football"
        print("  Warning: API_FOOTBALL_KEY not set, trying football-data...")
        
        # Fallback to football-data
        api_key = get_football_data_key()
        if api_key:
            return FootballDataSource(api_key), "football-data"
        print("  Warning: FOOTBALL_DATA_API_KEY also not set")
    
    elif source == "football-data":
        api_key = get_football_data_key()
        if api_key:
            return FootballDataSource(api_key), "football-data"
        print("  Warning: FOOTBALL_DATA_API_KEY not set, trying API-Football...")
        
        # Fallback to API-Football
        api_key = get_api_football_key()
        if api_key:
            return APIFootballSource(api_key), "api-football"
        print("  Warning: API_FOOTBALL_KEY also not set")
    
    print("\n❌ No API keys configured!")
    print("\nSetup:")
    print("1. Add API_FOOTBALL_KEY as a GitHub secret (recommended)")
    print("2. Or add FOOTBALL_DATA_API_KEY as a GitHub secret")
    sys.exit(1)


# ==================== HTML Update Logic ====================

def update_match_scores(html_content: str, matches: List[Dict], source_type: str) -> str:
    """Update match scores and status in the HTML content."""
    lines = html_content.split("\n")
    updated_count = 0

    for match in matches:
        if source_type == "api-football":
            # API-Football format
            fixture = match.get("fixture", {})
            match_id = fixture.get("id")
            status_data = fixture.get("status", {})
            status = status_data.get("short", "")
            score_data = fixture.get("score", {})
            full_time = score_data.get("fulltime", {})
            home_goals = full_time.get("home")
            away_goals = full_time.get("away")
            
            # Determine if match is finished
            is_finished = status in ("FT", "AET", "PEN")
        else:
            # football-data.org format
            match_id = match.get("id")
            status = match.get("status", "")
            score_data = match.get("score", {})
            full_time = score_data.get("fullTime", {})
            home_goals = full_time.get("home")
            away_goals = full_time.get("away")
            is_finished = status == "FINISHED"

        # Only update finished matches with a valid score
        if not is_finished:
            continue
        if home_goals is None or away_goals is None:
            continue

        score_str = f"{home_goals}-{away_goals}"

        # Find and update the match line by home/away team names
        for i, line in enumerate(lines):
            # Try to match by match ID first (if we have it)
            # For API-Football, we match by team names since IDs differ
            if source_type == "api-football":
                teams = match.get("teams", {})
                home_team = teams.get("home", {}).get("name", "")
                away_team = teams.get("away", {}).get("name", "")
                home_cn = TEAM_NAME_MAP.get(home_team, home_team)
                away_cn = TEAM_NAME_MAP.get(away_team, away_team)
                
                # Match by team names in the line
                match_found = (
                    f'homeTeam:"{home_cn}"' in line or f'homeTeam: "{home_cn}"' in line
                ) and (
                    f'awayTeam:"{away_cn}"' in line or f'awayTeam: "{away_cn}"' in line
                )
            else:
                # football-data: match by ID
                match_found = f"id:{match_id}," in line

            if not match_found:
                continue

            # Check if already has the same score
            if f'score:"{score_str}"' in line:
                print(f"    Match: {home_cn} vs {away_cn} already up-to-date ({score_str})")
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
            
            home_display = home_cn if source_type == "api-football" else home_team
            away_display = away_cn if source_type == "api-football" else away_team
            print(f"    Match: {home_display} vs {away_display} updated to {score_str} (finished)")
            break

    print(f"  Updated {updated_count} match(es)")
    return "\n".join(lines)


def update_group_standings(html_content: str, standings: Dict[str, List[Dict]], source_type: str) -> str:
    """Update group standings in the HTML content."""
    lines = html_content.split("\n")
    updated_count = 0

    for group_name, teams in standings.items():
        for team_data in teams:
            if source_type == "api-football":
                team_info = team_data.get("team", {})
                team_name_en = team_info.get("name", "")
                p = team_data.get("all", {}).get("played", 0)
                w = team_data.get("all", {}).get("win", 0)
                d = team_data.get("all", {}).get("draw", 0)
                l = team_data.get("all", {}).get("lose", 0)
                gf = team_data.get("all", {}).get("goals", {}).get("for", 0)
                ga = team_data.get("all", {}).get("goals", {}).get("against", 0)
                gd = gf - ga
                pts = team_data.get("points", 0)
            else:
                team_info = team_data.get("team", {})
                team_name_en = team_info.get("name", "")
                p = team_data.get("playedGames", 0)
                w = team_data.get("won", 0)
                d = team_data.get("draw", 0)
                l = team_data.get("lost", 0)
                gf = team_data.get("goalsFor", 0)
                ga = team_data.get("goalsAgainst", 0)
                gd = team_data.get("goalDifference", 0)
                pts = team_data.get("points", 0)

            team_name_cn = TEAM_NAME_MAP.get(team_name_en)
            if not team_name_cn:
                print(f"    Warning: No mapping for team '{team_name_en}'")
                continue

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


def update_scorers(html_content: str, scorers: List[Dict], source_type: str) -> str:
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

    for scorer_data in scorers:
        if source_type == "api-football":
            player = scorer_data.get("player", {})
            player_name = player.get("name", "")
            goals = scorer_data.get("statistics", [{}])[0].get("goals", {}).get("total", 0)
            team_info = scorer_data.get("statistics", [{}])[0].get("team", {})
            team_name_en = team_info.get("name", "")
        else:
            player = scorer_data.get("player", {})
            player_name = player.get("name", "")
            goals = scorer_data.get("goals", 0)
            team_info = scorer_data.get("team", {})
            team_name_en = team_info.get("name", "")

        if not player_name or goals == 0:
            continue

        # Try to find existing scorer by name
        found = False
        for i in range(scorers_start + 1, scorers_end):
            if f'eng:"{player_name}"' in lines[i] or f'eng: "{player_name}"' in lines[i]:
                current_goals = re.search(r'goals:(\d+)', lines[i])
                if current_goals and int(current_goals.group(1)) == goals:
                    found = True
                    break

                lines[i] = re.sub(r'goals:\d+', f'goals:{goals}', lines[i])
                updated_count += 1
                print(f"    {player_name}: goals updated to {goals}")
                found = True
                break
            elif player_name in lines[i]:
                current_goals = re.search(r'goals:(\d+)', lines[i])
                if current_goals and int(current_goals.group(1)) == goals:
                    found = True
                    break

                lines[i] = re.sub(r'goals:\d+', f'goals:{goals}', lines[i])
                updated_count += 1
                print(f"    {player_name} (CN): goals updated to {goals}")
                found = True
                break

        if not found:
            print(f"    {player_name}: not found in existing scorers (skipping)")

    print(f"  Updated {updated_count} scorer(s)")
    return "\n".join(lines)


# ==================== Main ====================

def main():
    """Main entry point."""
    print("=" * 60)
    print("World Cup 2026 Score Updater")
    print("=" * 60)

    # Get data source
    source, source_type = get_data_source()
    print(f"✅ Using {source_type} API")

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
    matches_today = source.fetch_matches(today)
    matches_yesterday = source.fetch_matches(yesterday)
    all_matches = matches_yesterday + matches_today

    if not all_matches:
        print("\nℹ️  No matches found to update")
        print("=" * 60)
        return

    # Filter to finished matches
    if source_type == "api-football":
        finished_matches = [
            m for m in all_matches
            if m.get("fixture", {}).get("status", {}).get("short", "") in ("FT", "AET", "PEN")
            and m.get("score", {}).get("fulltime", {}).get("home") is not None
        ]
    else:
        finished_matches = [
            m for m in all_matches
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
    html_content = update_match_scores(html_content, finished_matches, source_type)

    # Update group standings
    print("\n📊 Updating group standings...")
    standings = source.fetch_standings()
    if standings:
        html_content = update_group_standings(html_content, standings, source_type)
    else:
        print("  No standings data available")

    # Update scorers
    print("\n⚽ Updating top scorers...")
    scorers = source.fetch_scorers()
    if scorers:
        html_content = update_scorers(html_content, scorers, source_type)
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
