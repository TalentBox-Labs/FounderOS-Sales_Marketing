"""Retry/backoff helpers for Hashnode GraphQL (no network)."""

from __future__ import annotations

from src.tools import hashnode_publish as hp


def test_retry_sleep_from_cloudflare_json():
    body = '{"retry_after": 42, "status": 522}'
    assert hp._retry_sleep_sec(http_code=522, err_body=body, attempt_index=0) == 42


def test_retry_sleep_caps_retry_after():
    body = '{"retry_after": 500}'
    assert hp._retry_sleep_sec(http_code=522, err_body=body, attempt_index=0) == 45


def test_retry_sleep_respects_custom_cap(monkeypatch):
    monkeypatch.setenv("HASHNODE_RETRY_AFTER_MAX_SEC", "90")
    body = '{"retry_after": 500}'
    assert hp._retry_sleep_sec(http_code=522, err_body=body, attempt_index=0) == 90


def test_retry_sleep_non_json_backoff():
    assert hp._retry_sleep_sec(http_code=522, err_body="<html>", attempt_index=0) == 15
    assert hp._retry_sleep_sec(http_code=522, err_body="<html>", attempt_index=1) == 30


def test_retry_sleep_non_retriable():
    assert hp._retry_sleep_sec(http_code=404, err_body="{}", attempt_index=0) == 0
