#!/usr/bin/env python3
"""Generate a stable SVG profile card from live GitHub GraphQL data."""

from __future__ import annotations

import argparse
import html
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import date, timedelta
from pathlib import Path
from typing import Any

GRAPHQL_URL = "https://api.github.com/graphql"
OUTPUT_PATH = Path("assets/github-metrics.svg")

QUERY = """
query ProfileMetrics($login: String!, $cursor: String) {
  user(login: $login) {
    followers { totalCount }
    repositories(
      first: 100
      after: $cursor
      ownerAffiliations: [OWNER]
      privacy: PUBLIC
      orderBy: { field: UPDATED_AT, direction: DESC }
    ) {
      totalCount
      pageInfo { hasNextPage endCursor }
      nodes { isFork stargazerCount }
    }
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays { contributionCount date }
        }
      }
    }
  }
}
"""


def graphql(token: str, variables: dict[str, Any]) -> dict[str, Any]:
    request = urllib.request.Request(
        GRAPHQL_URL,
        data=json.dumps({"query": QUERY, "variables": variables}).encode(),
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "kuntal1461-profile-metrics",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as error:
        detail = error.read().decode(errors="replace")
        raise RuntimeError(f"GitHub API returned HTTP {error.code}: {detail}") from error

    if payload.get("errors"):
        raise RuntimeError(f"GitHub GraphQL error: {payload['errors']}")
    return payload["data"]["user"]


def fetch_metrics(username: str, token: str) -> dict[str, Any]:
    cursor = None
    repository_count = 0
    stars = 0
    user: dict[str, Any] | None = None

    while True:
        page = graphql(token, {"login": username, "cursor": cursor})
        if page is None:
            raise RuntimeError(f"GitHub user {username!r} was not found")
        user = page
        repositories = page["repositories"]
        repository_count = repositories["totalCount"]
        stars += sum(
            repository["stargazerCount"]
            for repository in repositories["nodes"]
            if not repository["isFork"]
        )
        if not repositories["pageInfo"]["hasNextPage"]:
            break
        cursor = repositories["pageInfo"]["endCursor"]

    assert user is not None
    contributions = user["contributionsCollection"]
    calendar = contributions["contributionCalendar"]
    days = {
        item["date"]: item["contributionCount"]
        for week in calendar["weeks"]
        for item in week["contributionDays"]
    }
    weekly_counts = [
        sum(item["contributionCount"] for item in week["contributionDays"])
        for week in calendar["weeks"]
    ]
    streak, today_count = calculate_streak(days)

    return {
        "username": username,
        "followers": user["followers"]["totalCount"],
        "repositories": repository_count,
        "stars": stars,
        "total_contributions": calendar["totalContributions"],
        "streak": streak,
        "today": today_count,
        "active_days": sum(count > 0 for count in days.values()),
        "weekly_counts": weekly_counts[-52:],
    }


def calculate_streak(days: dict[str, int]) -> tuple[int, int]:
    today = date.today()
    today_count = days.get(today.isoformat(), 0)
    cursor = today if today_count else today - timedelta(days=1)
    streak = 0
    while days.get(cursor.isoformat(), 0) > 0:
        streak += 1
        cursor -= timedelta(days=1)
    return streak, today_count


def compact(value: int) -> str:
    if value < 1_000:
        return str(value)
    if value < 1_000_000:
        return f"{value / 1_000:.1f}k".replace(".0k", "k")
    return f"{value / 1_000_000:.1f}m".replace(".0m", "m")


def activity_bars(weekly: list[int]) -> str:
    peak = max(weekly, default=1) or 1
    bars = []
    for index, count in enumerate(weekly):
        height = max(2, round(34 * count / peak)) if count else 2
        opacity = 0.18 if count == 0 else 0.4 + (0.6 * count / peak)
        bars.append(
            f'<rect x="{42 + index * 11}" y="{220 - height}" width="7" height="{height}" '
            f'rx="2" fill="#2f81f7" opacity="{opacity:.2f}"/>'
        )
    return "".join(bars)


def render_svg(metrics: dict[str, Any]) -> str:
    username = html.escape(str(metrics["username"]))
    streak_unit = "day" if metrics["streak"] == 1 else "days"
    tiles = [
        ("CONTRIBUTIONS · 12 MONTHS", compact(metrics["total_contributions"])),
        ("CURRENT STREAK", f'{compact(metrics["streak"])} {streak_unit}'),
        ("TODAY", compact(metrics["today"])),
        ("PUBLIC REPOSITORIES", compact(metrics["repositories"])),
        ("SOURCE STARS", compact(metrics["stars"])),
        ("FOLLOWERS", compact(metrics["followers"])),
    ]
    tile_markup = []
    for index, (label, value) in enumerate(tiles):
        x = 28 + (index % 3) * 201
        y = 52 + (index // 3) * 74
        tile_markup.append(
            f'<g transform="translate({x} {y})">'
            '<rect width="185" height="60" rx="8" fill="#161b22" stroke="#30363d"/>'
            f'<text x="14" y="22" class="label">{html.escape(label)}</text>'
            f'<text x="14" y="47" class="value">{html.escape(value)}</text>'
            "</g>"
        )

    peak_week = max(metrics["weekly_counts"], default=0)
    details = f'{compact(metrics["active_days"])} active days  ·  {compact(peak_week)} contributions in the busiest week'
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="640" height="268" viewBox="0 0 640 268" role="img" aria-labelledby="title desc">
  <title id="title">Live GitHub activity for {username}</title>
  <desc id="desc">Rolling contribution totals, current activity streak, repositories, stars, followers, and weekly activity.</desc>
  <style>
    .heading {{ font: 600 14px -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; fill: #e6edf3; }}
    .label {{ font: 600 9px -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; letter-spacing: .45px; fill: #8b949e; }}
    .value {{ font: 700 20px -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; fill: #58a6ff; }}
    .detail {{ font: 500 11px -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; fill: #8b949e; }}
  </style>
  <rect width="640" height="268" rx="12" fill="#0d1117" stroke="#30363d"/>
  <text x="28" y="31" class="heading">GITHUB / {username}</text>
  {''.join(tile_markup)}
  <text x="28" y="201" class="label">ACTIVITY · LAST 52 WEEKS</text>
  {activity_bars(metrics["weekly_counts"])}
  <text x="28" y="250" class="detail">{html.escape(details)}</text>
</svg>
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, help="Read normalized metrics JSON instead of calling GitHub")
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.input:
        metrics = json.loads(args.input.read_text())
    else:
        token = os.environ.get("GITHUB_TOKEN")
        username = os.environ.get("GITHUB_USERNAME", "kuntal1461")
        if not token:
            print("GITHUB_TOKEN is required when --input is not supplied", file=sys.stderr)
            return 2
        metrics = fetch_metrics(username, token)

    output = render_svg(metrics)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists() and args.output.read_text() == output:
        print(f"{args.output} is already current")
        return 0
    args.output.write_text(output)
    print(f"Updated {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
