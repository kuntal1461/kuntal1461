#!/usr/bin/env python3
"""Generate theme-aware GitHub profile dashboards from first-party API data."""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, timedelta
from pathlib import Path
from typing import Any

GRAPHQL_URL = "https://api.github.com/graphql"
REST_URL = "https://api.github.com"
ASSET_DIR = Path("assets")
README_PATH = Path("README.md")
RECENT_ACTIVITY_PATTERN = re.compile(
    r"(?P<start><!-- recent_activity:start -->).*?(?P<end><!-- recent_activity:end -->)",
    re.DOTALL,
)

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
      nodes {
        isFork
        stargazerCount
      }
    }
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays { contributionCount date weekday }
        }
      }
    }
  }
}
"""

THEMES = {
    "dark": {
        "background": "#0d1117",
        "panel": "#161b22",
        "border": "#30363d",
        "text": "#e6edf3",
        "muted": "#8b949e",
        "accent": "#58a6ff",
        "green": "#3fb950",
        "heat": ["#21262d", "#0e4429", "#006d32", "#26a641", "#39d353"],
    },
    "light": {
        "background": "#ffffff",
        "panel": "#f6f8fa",
        "border": "#d0d7de",
        "text": "#1f2328",
        "muted": "#656d76",
        "accent": "#0969da",
        "green": "#1a7f37",
        "heat": ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"],
    },
}


def api_headers(token: str) -> dict[str, str]:
    return {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "User-Agent": "kuntal1461-profile-metrics",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def request_json(request: urllib.request.Request) -> Any:
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            if error.code in {429, 500, 502, 503, 504} and attempt < 2:
                time.sleep(2**attempt)
                continue
            detail = error.read().decode(errors="replace")[:500]
            raise RuntimeError(f"GitHub API returned HTTP {error.code}: {detail}") from error
        except urllib.error.URLError as error:
            if attempt < 2:
                time.sleep(2**attempt)
                continue
            raise RuntimeError(f"GitHub API request failed: {error.reason}") from error
    raise RuntimeError("GitHub API request failed after retries")


def graphql(token: str, variables: dict[str, Any]) -> dict[str, Any]:
    headers = api_headers(token) | {"Content-Type": "application/json"}
    request = urllib.request.Request(
        GRAPHQL_URL,
        data=json.dumps({"query": QUERY, "variables": variables}).encode(),
        headers=headers,
    )
    payload = request_json(request)
    if payload.get("errors"):
        raise RuntimeError(f"GitHub GraphQL error: {payload['errors']}")
    return payload["data"]["user"]


def rest(token: str, path: str, params: dict[str, str] | None = None) -> Any:
    query = f"?{urllib.parse.urlencode(params)}" if params else ""
    request = urllib.request.Request(f"{REST_URL}{path}{query}", headers=api_headers(token))
    return request_json(request)


def search_count(token: str, query: str, endpoint: str = "issues") -> int:
    payload = rest(token, f"/search/{endpoint}", {"q": query, "per_page": "1"})
    return int(payload["total_count"])


def fetch_metrics(username: str, token: str) -> dict[str, Any]:
    cursor = None
    user: dict[str, Any] | None = None
    repositories: list[dict[str, Any]] = []

    while True:
        page = graphql(token, {"login": username, "cursor": cursor})
        if page is None:
            raise RuntimeError(f"GitHub user {username!r} was not found")
        user = page
        connection = page["repositories"]
        repositories.extend(connection["nodes"])
        if not connection["pageInfo"]["hasNextPage"]:
            break
        cursor = connection["pageInfo"]["endCursor"]

    assert user is not None
    calendar = user["contributionsCollection"]["contributionCalendar"]
    days = {
        item["date"]: item["contributionCount"]
        for week in calendar["weeks"]
        for item in week["contributionDays"]
    }
    streak, today_count = calculate_streak(days)
    source_repositories = [repository for repository in repositories if not repository["isFork"]]
    return {
        "username": username,
        "followers": user["followers"]["totalCount"],
        "repositories": user["repositories"]["totalCount"],
        "stars": sum(repository["stargazerCount"] for repository in source_repositories),
        "total_contributions": calendar["totalContributions"],
        "streak": streak,
        "today": today_count,
        "active_days": sum(count > 0 for count in days.values()),
        "heatmap": [
            [item["contributionCount"] for item in week["contributionDays"]]
            for week in calendar["weeks"][-52:]
        ],
        "commits": search_count(token, f"author:{username}", "commits"),
        "pull_requests": search_count(token, f"author:{username} type:pr"),
        "issues": search_count(token, f"author:{username} type:issue"),
        "reviews": search_count(token, f"reviewed-by:{username} type:pr"),
        "recent_activity": parse_recent_activity(rest(token, f"/users/{username}/events/public", {"per_page": "30"})),
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


def parse_recent_activity(events: list[dict[str, Any]], limit: int = 4) -> list[dict[str, str]]:
    grouped: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for event in sorted(events, key=lambda item: item.get("created_at", ""), reverse=True):
        event_type = event.get("type")
        payload = event.get("payload", {})
        repository = event.get("repo", {}).get("name")
        if not repository:
            continue
        event_date = str(event.get("created_at", ""))[:10]
        url = f"https://github.com/{repository}"
        action = ""
        noun = ""
        amount = 1
        if event_type == "PushEvent":
            action, noun = "Pushed", "commit"
            amount = int(payload.get("size", 0))
        elif event_type == "PullRequestEvent":
            pull_request = payload.get("pull_request", {})
            action = "Merged" if pull_request.get("merged") else str(payload.get("action", "Updated")).title()
            noun = "pull request"
            url = validated_github_url(pull_request.get("html_url"), url)
        elif event_type == "IssuesEvent":
            issue = payload.get("issue", {})
            action, noun = str(payload.get("action", "Updated")).title(), "issue"
            url = validated_github_url(issue.get("html_url"), url)
        elif event_type == "IssueCommentEvent":
            issue = payload.get("issue", {})
            action, noun = "Commented on", "issue"
            url = validated_github_url(issue.get("html_url"), url)
        elif event_type == "ReleaseEvent":
            release = payload.get("release", {})
            action, noun = "Released", str(release.get("tag_name", "a version"))
            url = validated_github_url(release.get("html_url"), url)
        elif event_type == "CreateEvent" and payload.get("ref_type") in {"repository", "branch", "tag"}:
            action, noun = "Created", str(payload["ref_type"])
        if not action:
            continue
        key = (event_date, repository, action, noun)
        if key not in grouped:
            grouped[key] = {
                "date": event_date,
                "action": action,
                "noun": noun,
                "amount": 0,
                "events": 0,
                "repository": repository,
                "url": url,
            }
        grouped[key]["amount"] += amount
        grouped[key]["events"] += 1

    activity: list[dict[str, str]] = []
    for item in grouped.values():
        count = item["amount"] if item["noun"] == "commit" and item["amount"] else item["events"]
        noun = item["noun"] + ("s" if count != 1 else "")
        quantified = f"{count} {noun}" if count > 1 or item["noun"] == "commit" and item["amount"] else noun
        activity.append(
            {
                "date": item["date"],
                "description": f'{item["action"]} {quantified}',
                "repository": item["repository"],
                "url": item["url"] if item["events"] == 1 else f'https://github.com/{item["repository"]}',
            }
        )
        if len(activity) == limit:
            break
    return activity


def validated_github_url(candidate: Any, fallback: str) -> str:
    return str(candidate) if str(candidate).startswith("https://github.com/") else fallback


def compact(value: int) -> str:
    if value < 1_000:
        return str(value)
    if value < 1_000_000:
        return f"{value / 1_000:.1f}k".replace(".0k", "k")
    return f"{value / 1_000_000:.1f}m".replace(".0m", "m")


def svg_shell(title: str, description: str, body: str, theme_name: str, height: int) -> str:
    theme = THEMES[theme_name]
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="820" height="{height}" viewBox="0 0 820 {height}" role="img" aria-labelledby="title desc">
  <title id="title">{html.escape(title)}</title>
  <desc id="desc">{html.escape(description)}</desc>
  <style>
    .title {{ font: 600 15px -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; fill: {theme['text']}; }}
    .label {{ font: 600 9px -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; letter-spacing: .55px; fill: {theme['muted']}; }}
    .value {{ font: 700 22px -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; fill: {theme['accent']}; }}
    .body {{ font: 500 12px -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; fill: {theme['text']}; }}
    .muted {{ font: 500 11px -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; fill: {theme['muted']}; }}
  </style>
  <rect x=".5" y=".5" width="819" height="{height - 1}" rx="14" fill="{theme['background']}" stroke="{theme['border']}"/>
  {body}
</svg>
"""


def metric_tile(label: str, value: str, x: int, y: int, theme: dict[str, Any], width: int = 242) -> str:
    return (
        f'<g transform="translate({x} {y})">'
        f'<rect width="{width}" height="58" rx="9" fill="{theme["panel"]}" stroke="{theme["border"]}"/>'
        f'<rect x="0" y="0" width="3" height="58" rx="2" fill="{theme["accent"]}"/>'
        f'<text x="16" y="21" class="label">{html.escape(label)}</text>'
        f'<text x="16" y="46" class="value">{html.escape(value)}</text>'
        "</g>"
    )


def heatmap_markup(heatmap: list[list[int]], theme: dict[str, Any]) -> str:
    maximum = max((count for week in heatmap for count in week), default=0)
    cells = []
    for column, week in enumerate(heatmap[-52:]):
        for row, count in enumerate(week):
            if not count:
                level = 0
            elif maximum <= 1:
                level = 4
            else:
                level = min(4, max(1, round(1 + (count / maximum) * 3)))
            cells.append(
                f'<rect x="{83 + column * 13}" y="{257 + row * 12}" width="9" height="9" rx="2" '
                f'fill="{theme["heat"][level]}"><title>{count} contributions</title></rect>'
            )
    return "".join(cells)


def render_dashboard(metrics: dict[str, Any], theme_name: str) -> str:
    theme = THEMES[theme_name]
    streak_unit = "day" if metrics["streak"] == 1 else "days"
    tiles = [
        ("CONTRIBUTIONS · 12 MONTHS", compact(metrics["total_contributions"])),
        ("CURRENT STREAK", f'{compact(metrics["streak"])} {streak_unit}'),
        ("TODAY", compact(metrics["today"])),
        ("PUBLIC REPOSITORIES", compact(metrics["repositories"])),
        ("SOURCE STARS", compact(metrics["stars"])),
        ("FOLLOWERS", compact(metrics["followers"])),
    ]
    tile_markup = "".join(
        metric_tile(label, value, 24 + (index % 3) * 258, 62 + (index // 3) * 72, theme)
        for index, (label, value) in enumerate(tiles)
    )
    weekly = [sum(week) for week in metrics["heatmap"]]
    peak_week = max(weekly, default=0)
    body = f"""
  <circle cx="28" cy="28" r="5" fill="{theme['green']}"><animate attributeName="opacity" values="1;.45;1" dur="2.8s" repeatCount="indefinite"/></circle>
  <text x="42" y="33" class="title">GITHUB ENGINEERING ACTIVITY</text>
  <text x="690" y="33" class="muted">@{html.escape(metrics['username'])}</text>
  {tile_markup}
  <text x="24" y="231" class="label">CONTRIBUTION SIGNAL · LAST 52 WEEKS</text>
  <g>{heatmap_markup(metrics['heatmap'], theme)}</g>
  <text x="24" y="278" class="muted">MON</text>
  <text x="24" y="302" class="muted">WED</text>
  <text x="24" y="326" class="muted">FRI</text>
  <line x1="24" y1="365" x2="796" y2="365" stroke="{theme['border']}"/>
  <text x="24" y="389" class="body">{compact(metrics['active_days'])} active days</text>
  <text x="162" y="389" class="muted">·</text>
  <text x="180" y="389" class="body">{compact(peak_week)} contributions in the busiest week</text>
  <text x="650" y="389" class="muted">First-party GitHub data</text>"""
    return svg_shell(
        f"GitHub engineering activity for {metrics['username']}",
        "Contribution heatmap, current streak, repositories, stars, followers, and rolling activity metrics.",
        body,
        theme_name,
        410,
    )


def render_open_source(metrics: dict[str, Any], theme_name: str) -> str:
    theme = THEMES[theme_name]
    tiles = [
        ("PUBLIC COMMITS", compact(metrics["commits"])),
        ("PULL REQUESTS", compact(metrics["pull_requests"])),
        ("ISSUES OPENED", compact(metrics["issues"])),
        ("PULL REQUESTS REVIEWED", compact(metrics["reviews"])),
    ]
    tile_markup = "".join(
        metric_tile(label, value, 24 + index * 194, 58, theme, width=180)
        for index, (label, value) in enumerate(tiles)
    )
    body = f"""
  <circle cx="28" cy="28" r="5" fill="{theme['green']}"/>
  <text x="42" y="33" class="title">OPEN-SOURCE SIGNAL</text>
  <text x="678" y="33" class="muted">Public GitHub index</text>
  {tile_markup}"""
    return svg_shell(
        f"Open-source impact for {metrics['username']}",
        "Public commits, pull requests, issues, reviews, and source repository activity.",
        body,
        theme_name,
        132,
    )


def escape_markdown(value: str) -> str:
    return value.replace("[", "\\[").replace("]", "\\]")


def update_recent_activity(readme: str, activity: list[dict[str, str]]) -> str:
    if not RECENT_ACTIVITY_PATTERN.search(readme):
        raise RuntimeError("README recent activity markers are missing")
    if activity:
        lines = [
            f'- `{item["date"]}` · {escape_markdown(item["description"])} in '
            f'[{escape_markdown(item["repository"])}]({item["url"]})'
            for item in activity
        ]
    else:
        lines = ["- No recent public activity returned by GitHub."]
    replacement = "<!-- recent_activity:start -->\n" + "\n".join(lines) + "\n<!-- recent_activity:end -->"
    return RECENT_ACTIVITY_PATTERN.sub(lambda _: replacement, readme, count=1)


def write_if_changed(path: Path, content: str) -> bool:
    if path.exists() and path.read_text() == content:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, help="Read normalized metrics JSON instead of calling GitHub")
    parser.add_argument("--readme", type=Path, default=README_PATH)
    parser.add_argument("--asset-dir", type=Path, default=ASSET_DIR)
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
        try:
            metrics = fetch_metrics(username, token)
        except RuntimeError as error:
            print(f"Profile refresh skipped: {error}", file=sys.stderr)
            return 1

    outputs = {
        args.asset_dir / f"github-dashboard-{theme}.svg": render_dashboard(metrics, theme)
        for theme in THEMES
    }
    outputs.update(
        {
            args.asset_dir / f"open-source-impact-{theme}.svg": render_open_source(metrics, theme)
            for theme in THEMES
        }
    )
    outputs[args.readme] = update_recent_activity(args.readme.read_text(), metrics.get("recent_activity", []))
    changed = [str(path) for path, content in outputs.items() if write_if_changed(path, content)]
    print("Updated: " + ", ".join(changed) if changed else "Profile content is already current")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
