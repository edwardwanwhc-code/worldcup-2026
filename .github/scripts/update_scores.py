#!/usr/bin/env python3
"""
World Cup 2026 Score Updater

This script fetches the latest match results from various APIs and updates
the worldcup-2026.html file with new scores, standings, and scorers.

Supported APIs:
- football-data.org (free tier: 10 calls/min)
- API-Football (free tier: 100 calls/day)
- FIFA (public endpoints if available)

Usage:
    python update_scores.py

Environment Variables:
    FOOTBALL_DATA_API_KEY: API key for football-data.org
    API_FOOTBALL_KEY: API key for API-Football
    API_SOURCE: Which API to use (football-data, api-football, fifa)
    DRY_RUN: If 'true', don't commit changes
"""

import json
import os
import re
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import requests


# Constants
HTML_FILE = "index.html"
WORLD_CUP_ID = 2000  # FIFA World Cup competition ID (football-data.org)
CURRENT_YEAR = 2026
HKT_OFFSET = timedelta(hours=8)


class DataSource:
    """Base class for data sources."""
    
    def fetch_matches(self, date: str) -> List[Dict]:
        """Fetch matches for a given date. Returns list of match dicts."""
        raise NotImplementedError
    
    def fetch_standings(self, group: str) -> List[Dict]:
        """Fetch standings for a group."""
        raise NotImplementedError
    
    def fetch_scorers(self) -> List[Dict]:
        """Fetch top scorers."""
        raise NotImplementedError


class FootballDataSource(DataSource):
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
            return data.get("matches", [])
        except requests.exceptions.RequestException as e:
            print(f"Error fetching matches from football-data.org: {e}")
            return []
    
    def fetch_standings(self, group: str) -> List[Dict]:
        """Fetch group standings."""
        # Map group letters to football-data group IDs if needed
        url = f"{self.BASE_URL}/competitions/WC/standings"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Find the group
            for standing in data.get("standings", []):
                if standing.get("group") == f"GROUP_{group}":
                    return standing.get("table", [])
            return []
        except requests.exceptions.RequestException as e:
            print(f"Error fetching standings from football-data.org: {e}")
            return []
    
    def fetch_scorers(self) -> List[Dict]:
        """Fetch top scorers."""
        url = f"{self.BASE_URL}/competitions/WC/scorers"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            return data.get("scorers", [])
        except requests.exceptions.RequestException as e:
            print(f"Error fetching scorers from football-data.org: {e}")
            return []


class APIFootballSource(DataSource):
    """API-Football client."""
    
    BASE_URL = "https://v3.football.api-sports.io"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "x-rapidapi-key": api_key,
            "x-rapidapi-host": "v3.football.api-sports.io"
        }
    
    def fetch_matches(self, date: str) -> List[Dict]:
        """Fetch matches for a specific date."""
        url = f"{self.BASE_URL}/fixtures"
        params = {
            "league": 1,  # World Cup
            "season": CURRENT_YEAR,
            "date": date
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            return data.get("response", [])
        except requests.exceptions.RequestException as e:
            print(f"Error fetching matches from API-Football: {e}")
            return []
    
    def fetch_standings(self, group: str) -> List[Dict]:
        """Fetch group standings."""
        url = f"{self.BASE_URL}/standings"
        params = {
            "league": 1,
            "season": CURRENT_YEAR
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Find the group
            for league in data.get("response", []):
                for standing in league.get("league", {}).get("standings", []):
                    for group_data in standing:
                        if group_data.get("group") == f"Group {group}":
                            return group_data.get("table", [])
            return []
        except requests.exceptions.RequestException as e:
            print(f"Error fetching standings from API-Football: {e}")
            return []
    
    def fetch_scorers(self) -> List[Dict]:
        """Fetch top scorers."""
        url = f"{self.BASE_URL}/players/topscorers"
        params = {
            "league": 1,
            "season": CURRENT_YEAR
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            return data.get("response", [])
        except requests.exceptions.RequestException as e:
            print(f"Error fetching scorers from API-Football: {e}")
            return []


class FIFADataSource(DataSource):
    """FIFA public API client (if available)."""
    
    # FIFA API endpoints (these may require authentication or change)
    BASE_URL = "https://api.fifa.com/worldcup/2026"
    
    def __init__(self):
        pass
    
    def fetch_matches(self, date: str) -> List[Dict]:
        """Fetch matches from FIFA API."""
        # Implementation would depend on FIFA's actual API structure
        print("FIFA API source not yet implemented")
        return []
    
    def fetch_standings(self, group: str) -> List[Dict]:
        print("FIFA API source not yet implemented")
        return []
    
    def fetch_scorers(self) -> List[Dict]:
        print("FIFA API source not yet implemented")
        return []


def get_data_source() -> Optional[DataSource]:
    """Get the configured data source."""
    source = os.environ.get("API_SOURCE", "football-data")
    
    if source == "football-data":
        api_key = os.environ.get("FOOTBALL_DATA_API_KEY")
        if api_key:
            return FootballDataSource(api_key)
        print("Warning: FOOTBALL_DATA_API_KEY not set")
    
    elif source == "api-football":
        api_key = os.environ.get("API_FOOTBALL_KEY")
        if api_key:
            return APIFootballSource(api_key)
        print("Warning: API_FOOTBALL_KEY not set")
    
    elif source == "fifa":
        return FIFADataSource()
    
    print(f"Error: Unknown API source '{source}' or missing API key")
    return None


def update_html_scores(html_content: str, matches: List[Dict]) -> str:
    """Update match scores in the HTML content."""
    # This is a placeholder - the actual implementation would parse
    # the HTML and update the DATA.matches array
    print(f"Would update {len(matches)} matches in HTML")
    return html_content


def update_html_standings(html_content: str, groups: Dict[str, List[Dict]]) -> str:
    """Update group standings in the HTML content."""
    print(f"Would update {len(groups)} group standings in HTML")
    return html_content


def update_html_scorers(html_content: str, scorers: List[Dict]) -> str:
    """Update scorers list in the HTML content."""
    print(f"Would update {len(scorers)} scorers in HTML")
    return html_content


def main():
    """Main entry point."""
    print("=" * 60)
    print("World Cup 2026 Score Updater")
    print("=" * 60)
    
    # Check if we're in dry run mode
    dry_run = os.environ.get("DRY_RUN", "false").lower() == "true"
    if dry_run:
        print("⚠️  DRY RUN MODE - No changes will be committed")
    
    # Get data source
    source = get_data_source()
    if not source:
        print("\n❌ No data source available. Please configure an API key.")
        print("\nSetup instructions:")
        print("1. Get a free API key from https://www.football-data.org/")
        print("2. Add it as a GitHub secret: FOOTBALL_DATA_API_KEY")
        print("\nOr use API-Football:")
        print("1. Get a key from https://www.api-football.com/")
        print("2. Add it as a GitHub secret: API_FOOTBALL_KEY")
        sys.exit(1)
    
    # Calculate dates to check
    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    print(f"\n📅 Checking matches for: {yesterday} and {today}")
    
    # Fetch matches
    matches_today = source.fetch_matches(today)
    matches_yesterday = source.fetch_matches(yesterday)
    all_matches = matches_yesterday + matches_today
    
    if not all_matches:
        print("No matches found to update")
        return
    
    print(f"Found {len(all_matches)} matches to process")
    
    # Read HTML file
    try:
        with open(HTML_FILE, "r", encoding="utf-8") as f:
            html_content = f.read()
    except FileNotFoundError:
        print(f"Error: {HTML_FILE} not found")
        sys.exit(1)
    
    # Update HTML
    html_content = update_html_scores(html_content, all_matches)
    
    # Fetch and update standings if needed
    groups_to_update = set()
    for match in all_matches:
        # Determine group from match data
        group = match.get("group", "")
        if group:
            groups_to_update.add(group)
    
    for group in groups_to_update:
        standings = source.fetch_standings(group)
        if standings:
            # Update specific group in HTML
            pass
    
    # Fetch and update scorers
    scorers = source.fetch_scorers()
    if scorers:
        html_content = update_html_scorers(html_content, scorers)
    
    # Write updated HTML
    if not dry_run:
        with open(HTML_FILE, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"\n✅ Updated {HTML_FILE}")
    else:
        print(f"\n🔍 DRY RUN: Would update {HTML_FILE}")
    
    print("\n" + "=" * 60)
    print("Update complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
