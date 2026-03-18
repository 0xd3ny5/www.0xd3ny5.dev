from __future__ import annotations

import logging
import time
import typing

import httpx

logger = logging.getLogger(__name__)

_BASE = "https://api.github.com"
_TIMEOUT = 10.0
_MAX_RETRIES = 2


class GitHubStats(typing.TypedDict):
    public_repos: int
    followers: int
    total_stars: int
    commits: int


class GitHubClient:
    __slots__ = ("_cached", "_cached_at", "_headers", "_ttl", "_username")

    def __init__(self, username: str, token: str = "", cache_ttl: int = 600) -> None:
        self._username = username
        self._ttl = cache_ttl
        self._cached: GitHubStats | None = None
        self._cached_at: float = 0.0
        self._headers: dict[str, str] = {"Accept": "application/vnd.github+json"}
        if token:
            self._headers["Authorization"] = f"Bearer {token}"

    async def get_stats(self) -> GitHubStats:
        now = time.monotonic()
        if self._cached and (now - self._cached_at) < self._ttl:
            return self._cached
        stats = await self._fetch_stats()
        self._cached = stats
        self._cached_at = now
        return stats

    async def get_user(self) -> dict[str, typing.Any]:
        return await self._get_json(f"/users/{self._username}")

    async def get_repos(self, page: int = 1) -> list[dict[str, typing.Any]]:
        return await self._get_json(
            f"/users/{self._username}/repos",
            params={"per_page": 100, "page": page, "type": "owner"},
        )

    async def _get_json(
        self,
        path: str,
        params: dict[str, typing.Any] | None = None,
    ) -> typing.Any:
        async with httpx.AsyncClient(
            base_url=_BASE,
            headers=self._headers,
            timeout=_TIMEOUT,
        ) as client:
            return await self._request(client, path, params)

    async def _request(
        self,
        client: httpx.AsyncClient,
        path: str,
        params: dict[str, typing.Any] | None = None,
    ) -> typing.Any:
        last_exc: Exception | None = None
        for attempt in range(_MAX_RETRIES + 1):
            try:
                resp = await client.get(path, params=params)
                remaining = resp.headers.get("x-ratelimit-remaining")
                if remaining and int(remaining) < 10:
                    logger.warning("GitHub rate limit low: %s remaining", remaining)
                resp.raise_for_status()
                return resp.json()
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 403:
                    logger.warning("GitHub rate limited on %s", path)
                    return {} if attempt == _MAX_RETRIES else None
                last_exc = exc
            except httpx.RequestError as exc:
                logger.warning(
                    "GitHub request error on %s (attempt %d): %s", path, attempt + 1, exc
                )
                last_exc = exc
        if last_exc:
            raise last_exc
        return {}

    async def _fetch_stats(self) -> GitHubStats:
        async with httpx.AsyncClient(
            base_url=_BASE,
            headers=self._headers,
            timeout=_TIMEOUT,
        ) as client:
            user = await self._request(client, f"/users/{self._username}")
            stars = await self._total_stars(client)
            commits = await self._commit_count(client)

        return GitHubStats(
            public_repos=user.get("public_repos", 0) if user else 0,
            followers=user.get("followers", 0) if user else 0,
            total_stars=stars,
            commits=commits,
        )

    async def _total_stars(self, client: httpx.AsyncClient) -> int:
        total, page = 0, 1
        while True:
            repos = await self._request(
                client,
                f"/users/{self._username}/repos",
                params={"per_page": 100, "page": page, "type": "owner"},
            )
            if not repos or not isinstance(repos, list):
                break
            total += sum(r.get("stargazers_count", 0) for r in repos)
            if len(repos) < 100:
                break
            page += 1
        return total

    async def _commit_count(self, client: httpx.AsyncClient) -> int:
        try:
            data = await self._request(
                client,
                "/search/commits",
                params={"q": f"author:{self._username}", "per_page": 1},
            )
            return data.get("total_count", 0) if data else 0
        except Exception:
            logger.warning("GitHub commit count unavailable")
            return 0
