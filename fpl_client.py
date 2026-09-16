"""Thin client for the official (unofficial-but-public) Fantasy Premier League API."""
import time
from typing import Any, Optional

import httpx

BASE_URL = "https://fantasy.premierleague.com/api"
CACHE_TTL_SECONDS = 15 * 60

_cache: dict[str, tuple[float, Any]] = {}


async def _get_json(path: str) -> Any:
    now = time.time()
    cached = _cache.get(path)
    if cached and now - cached[0] < CACHE_TTL_SECONDS:
        return cached[1]

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(f"{BASE_URL}{path}", headers={"User-Agent": "fpl-assistant/0.1"})
        resp.raise_for_status()
        data = resp.json()

    _cache[path] = (now, data)
    return data


async def get_bootstrap() -> dict:
    """Players, teams, gameweeks, scoring rules — the core static dataset."""
    return await _get_json("/bootstrap-static/")


async def get_fixtures(event: Optional[int] = None) -> list:
    path = "/fixtures/"
    if event is not None:
        path += f"?event={event}"
    return await _get_json(path)


async def get_player_summary(player_id: int) -> dict:
    """Per-gameweek history + upcoming fixtures for a single player."""
    return await _get_json(f"/element-summary/{player_id}/")


async def get_entry(team_id: int) -> dict:
    """A manager's team info (name, overall rank, etc.)."""
    return await _get_json(f"/entry/{team_id}/")


async def get_entry_picks(team_id: int, event: int) -> dict:
    """A manager's 15-man squad for a given gameweek."""
    return await _get_json(f"/entry/{team_id}/event/{event}/picks/")
