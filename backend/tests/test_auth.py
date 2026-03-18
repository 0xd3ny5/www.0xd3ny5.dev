from __future__ import annotations

import time

import fastapi
import pytest

from backend.src.presentation.dependencies import (
    _MAX_ATTEMPTS,
    _check_rate_limit,
    _clear_failures,
    _failed,
    _record_failure,
)


@pytest.fixture(autouse=True)
def _clean_state() -> None:
    _failed.clear()


class TestRateLimit:
    def test_allows_under_limit(self) -> None:
        for _ in range(_MAX_ATTEMPTS - 1):
            _record_failure("1.2.3.4")
        _check_rate_limit("1.2.3.4")

    def test_blocks_at_limit(self) -> None:
        for _ in range(_MAX_ATTEMPTS):
            _record_failure("1.2.3.4")
        with pytest.raises(fastapi.HTTPException) as exc_info:
            _check_rate_limit("1.2.3.4")
        assert exc_info.value.status_code == 429

    def test_different_ips_independent(self) -> None:
        for _ in range(_MAX_ATTEMPTS):
            _record_failure("1.1.1.1")
        _check_rate_limit("2.2.2.2")

    def test_clear_resets(self) -> None:
        for _ in range(_MAX_ATTEMPTS):
            _record_failure("1.2.3.4")
        _clear_failures("1.2.3.4")
        _check_rate_limit("1.2.3.4")

    def test_old_attempts_expire(self) -> None:
        past = time.monotonic() - 400
        _failed["1.2.3.4"] = [past] * _MAX_ATTEMPTS
        _check_rate_limit("1.2.3.4")

    def test_mixed_old_and_new(self) -> None:
        now = time.monotonic()
        past = now - 400
        _failed["1.2.3.4"] = [past, past, now, now, now]
        _check_rate_limit("1.2.3.4")

    def test_exactly_at_limit_blocks(self) -> None:
        for _ in range(_MAX_ATTEMPTS):
            _record_failure("5.5.5.5")
        with pytest.raises(fastapi.HTTPException):
            _check_rate_limit("5.5.5.5")

    def test_clear_nonexistent_ip_safe(self) -> None:
        _clear_failures("9.9.9.9")
