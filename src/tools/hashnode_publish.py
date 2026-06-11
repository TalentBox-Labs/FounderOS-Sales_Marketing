"""Publish ``05_Final.md`` to a Hashnode team publication via GraphQL.

Loads repo-root ``.env`` when ``python-dotenv`` is available (same pattern as
``google_sheets_verify``). Requires a Personal Access Token and publication id.

Env (see ``.env.example``):
  HASHNODE_ACCESS_TOKEN — PAT from Hashnode developer settings (never commit).
  HASHNODE_PUBLICATION_ID — team publication ObjectId (use ``whoami``).
  HASHNODE_GQL_ENDPOINT — optional; default ``https://gql.hashnode.com/graphql``.
  HASHNODE_USER_AGENT — optional; override request User-Agent if Cloudflare returns 403.
  HASHNODE_AUTHORIZATION_BEARER — set to ``true`` to send ``Authorization: Bearer <token>``.
  HASHNODE_GQL_MAX_RETRIES — optional; default ``4`` (retries on 522/5xx origin errors).
  HASHNODE_REQUEST_TIMEOUT_SEC — optional; default ``90`` (read timeout per attempt).
  HASHNODE_RETRY_AFTER_MAX_SEC — optional; default ``45`` (caps Cloudflare ``retry_after`` so waits are not minutes long).

Does not run ``record-live``; after a successful publish, confirm the live URL
then use ``go_live_helpers record-live`` as usual.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from urllib.parse import urlparse

from src.tools.go_live_helpers import (
    _final_path_for_row,
    _parse_front_matter,
    _read_tracker_rows,
)
from src.tools.runtime_paths import REPO_ROOT

_DEFAULT_GQL = "https://gql.hashnode.com/graphql"
# Cloudflare / origin blips (522 = connection to origin timed out).
_RETRIABLE_HTTP = frozenset({502, 503, 504, 522, 523, 524})
# Cloudflare often blocks Python's default ``Python-urllib/…`` User-Agent (HTTP 403, error 1010).
_DEFAULT_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 "
    "WorkCrew-CMS-OS/hashnode_publish"
)

_WHOAMI_QUERY = """
query WhoamiPublications {
  me {
    id
    username
    publications(first: 30) {
      edges {
        node {
          id
          title
          url
        }
      }
    }
  }
}
"""

_PUBLISH_MUTATION = """
mutation PublishPost($input: PublishPostInput!) {
  publishPost(input: $input) {
    post {
      id
      title
      slug
      url
      canonicalUrl
    }
  }
}
"""


def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv(REPO_ROOT / ".env")


def _env_token() -> str:
    return (os.environ.get("HASHNODE_ACCESS_TOKEN") or "").strip()


def _env_publication_id() -> str:
    return (os.environ.get("HASHNODE_PUBLICATION_ID") or "").strip()


def _gql_endpoint() -> str:
    return (os.environ.get("HASHNODE_GQL_ENDPOINT") or _DEFAULT_GQL).strip()


def _graphql_headers(*, token: str) -> dict[str, str]:
    auth = token.strip()
    if os.environ.get("HASHNODE_AUTHORIZATION_BEARER", "").strip().lower() in (
        "1",
        "true",
        "yes",
    ):
        if not auth.lower().startswith("bearer "):
            auth = f"Bearer {auth}"
    ua = (os.environ.get("HASHNODE_USER_AGENT") or _DEFAULT_UA).strip()
    return {
        "Content-Type": "application/json",
        "Authorization": auth,
        "User-Agent": ua,
        "Accept": "application/json",
    }


def _gql_max_retries() -> int:
    raw = os.environ.get("HASHNODE_GQL_MAX_RETRIES", "4").strip()
    try:
        n = int(raw)
    except ValueError:
        return 4
    return max(1, min(n, 10))


def _gql_timeout_sec() -> float:
    raw = os.environ.get("HASHNODE_REQUEST_TIMEOUT_SEC", "90").strip()
    try:
        t = float(raw)
    except ValueError:
        return 90.0
    return max(15.0, min(t, 300.0))


def _retry_after_cap_sec() -> int:
    """Cap Cloudflare ``retry_after`` so a stuck origin does not block the CLI for many minutes."""
    raw = os.environ.get("HASHNODE_RETRY_AFTER_MAX_SEC", "45").strip()
    try:
        n = int(raw)
    except ValueError:
        return 45
    return max(5, min(n, 600))


def _retry_sleep_sec(*, http_code: int, err_body: str, attempt_index: int) -> int:
    """Seconds to wait before retrying Cloudflare / origin errors."""
    if http_code not in _RETRIABLE_HTTP:
        return 0
    cap = _retry_after_cap_sec()
    try:
        j = json.loads(err_body)
        ra = j.get("retry_after")
        if isinstance(ra, (int, float)) and ra > 0:
            return int(min(max(ra, 5), cap))
    except (json.JSONDecodeError, TypeError, ValueError):
        pass
    # Exponential backoff capped at 60s when body has no retry_after.
    return min(min(15 * (2**attempt_index), 60), cap)


def _gql_request(
    *,
    token: str,
    query: str,
    variables: dict | None = None,
) -> dict:
    endpoint = _gql_endpoint()
    body = json.dumps(
        {"query": query, "variables": variables or {}},
        ensure_ascii=False,
    ).encode("utf-8")
    timeout = _gql_timeout_sec()
    max_tries = _gql_max_retries()

    for attempt in range(max_tries):
        req = urllib.request.Request(
            endpoint,
            data=body,
            headers=_graphql_headers(token=token),
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode("utf-8")
            break
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            if e.code in _RETRIABLE_HTTP and attempt < max_tries - 1:
                wait = _retry_sleep_sec(
                    http_code=e.code, err_body=err_body, attempt_index=attempt
                )
                print(
                    f"Hashnode GraphQL HTTP {e.code} (transient). "
                    f"Retry {attempt + 1}/{max_tries - 1} after {wait}s…",
                    file=sys.stderr,
                )
                time.sleep(wait)
                continue
            hint = ""
            if e.code == 403 and ("1010" in err_body or "Cloudflare" in err_body):
                hint = (
                    " Hint: Cloudflare often blocks script clients; this build sends a real "
                    "browser User-Agent. If it persists, try from another network/VPN or set "
                    "HASHNODE_USER_AGENT / HASHNODE_GQL_ENDPOINT per Hashnode docs."
                )
            elif e.code == 401:
                hint = (
                    " Hint: check HASHNODE_ACCESS_TOKEN; try HASHNODE_AUTHORIZATION_BEARER=true "
                    "if your PAT must be sent as ``Bearer <token>``."
                )
            elif e.code in _RETRIABLE_HTTP:
                hint = (
                    " Hint: HTTP 522/5xx means Cloudflare could not reach Hashnode’s origin "
                    "(often temporary). Wait a few minutes and retry; check Hashnode status "
                    "or support channels if it persists."
                )
            snippet = err_body[:600].strip()
            if len(err_body) > 600:
                snippet += "\n…(response truncated; full body was longer)"
            raise RuntimeError(f"HTTP {e.code}: {snippet}{hint}") from e
        except urllib.error.URLError as e:
            if attempt < max_tries - 1:
                wait = min(15 * (2**attempt), 60)
                print(
                    f"Hashnode GraphQL network error: {e!r}. "
                    f"Retry {attempt + 1}/{max_tries - 1} after {wait}s…",
                    file=sys.stderr,
                )
                time.sleep(wait)
                continue
            raise RuntimeError(f"Network error calling {endpoint}: {e}") from e

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Non-JSON response from {endpoint}: {raw[:500]}") from e


def _cmd_whoami() -> int:
    token = _env_token()
    if not token:
        print(
            "Missing HASHNODE_ACCESS_TOKEN (set in .env or environment).",
            file=sys.stderr,
        )
        return 2
    data = _gql_request(token=token, query=_WHOAMI_QUERY)
    errs = data.get("errors")
    if errs:
        print(json.dumps(errs, indent=2), file=sys.stderr)
        return 1
    me = (data.get("data") or {}).get("me")
    if not me:
        print(json.dumps(data, indent=2), file=sys.stderr)
        return 1
    print(json.dumps(me, indent=2, sort_keys=True))
    print(
        "\nSet HASHNODE_PUBLICATION_ID to the ``id`` of the publication "
        "that backs workcrew.ai blog.",
        file=sys.stderr,
    )
    return 0


def _print_api_unreachable_help() -> None:
    print(
        "\n---\n"
        "Hashnode GraphQL is unreachable from this machine (HTTP 522 / timeouts).\n"
        "That is almost always a Hashnode / Cloudflare origin issue, not your token.\n\n"
        "What you can do:\n"
        "  1) Wait and retry later; try another network (e.g. mobile hotspot).\n"
        "  2) Run:  python -m src.tools.hashnode_publish publication-help\n"
        "     for ways to set HASHNODE_PUBLICATION_ID without ``whoami``.\n"
        "  3) Keep publishing manually in Hashnode until the API responds again.\n",
        file=sys.stderr,
    )


def _cmd_publication_help() -> int:
    print(
        """# Finding HASHNODE_PUBLICATION_ID without ``whoami``

When ``gql.hashnode.com`` returns HTTP 522/5xx, the CLI cannot list publications.
Use one of these **browser** workflows (same Hashnode account as your PAT):

## A) DevTools on hashnode.com (most reliable)

1. Log in at https://hashnode.com
2. Open your **team publication** dashboard (the blog that maps to workcrew.ai).
3. Open browser **DevTools** → **Network** → filter by **graphql** or **gql**.
4. Refresh the page. Click a **POST** to ``gql.hashnode.com`` that returns **200**.
5. In **Response** JSON, search for ``publicationId``, ``"id"`` under ``publications``, or a
   query that returns ``me { publications { edges { node { id } } } }`` — copy the **24-character
   hex ObjectId** for your publication.

## B) Ask a publication admin

Someone with **Owner / Admin** on the Hashnode publication can copy the publication id from
their dashboard or a working GraphQL client and send it to you securely (not in email/slack
if possible — use a password manager share).

## C) After you have the id

Put in ``.env``:

  HASHNODE_PUBLICATION_ID=your_object_id_here

Then test publish payload only (no API call):

  python -m src.tools.hashnode_publish publish W09B --dry-run

When the API is healthy again, ``whoami`` will still be the fastest way to confirm the id.

Optional env (see ``.env.example``):

- ``HASHNODE_RETRY_AFTER_MAX_SEC`` — cap wait between retries (default 45).
- ``HASHNODE_GQL_ENDPOINT`` — only if Hashnode documents a different GraphQL URL.
"""
    )
    return 0


def _tracker_row(content_id: str) -> dict[str, str]:
    _, rows = _read_tracker_rows()
    cid = content_id.strip().upper()
    for row in rows:
        if (row.get("content_id") or "").strip().upper() == cid:
            return row
    raise KeyError(f"No tracker row for content_id={content_id!r}")


def _slug_from_canonical(url: str, *, fallback: str) -> str:
    url = (url or "").strip()
    if not url:
        return _slugify(fallback)
    path = urlparse(url).path.strip("/")
    if not path:
        return _slugify(fallback)
    last = path.split("/")[-1]
    return last if last else _slugify(fallback)


def _slugify(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-") or "post"


def _tag_input(primary_keyword: str) -> list[dict[str, str]]:
    kw = (primary_keyword or "").strip()
    if not kw:
        return []
    slug = _slugify(kw)
    return [{"slug": slug, "name": kw}]


def _build_publish_input(
    *,
    fm: dict,
    body_md: str,
    publication_id: str,
    slug_override: str | None,
) -> dict:
    title = str(fm.get("article_title") or fm.get("title") or "").strip()
    if not title:
        raise ValueError("Front matter missing article_title (or title)")
    markdown = body_md.strip()
    if not markdown:
        raise ValueError("No markdown body after front matter")
    canon = str(fm.get("canonical_url", "")).strip()
    slug = (slug_override or "").strip() or _slug_from_canonical(
        canon, fallback=title
    )
    kw = str(fm.get("primary_keyword", "")).strip()
    meta: dict[str, str] = {}
    if title:
        meta["title"] = title
    if kw:
        meta["description"] = f"Article on {kw} for tech hiring teams."
    inp: dict = {
        "title": title,
        "publicationId": publication_id,
        "contentMarkdown": markdown,
        "slug": slug,
        "tags": _tag_input(kw),
    }
    if meta:
        inp["metaTags"] = meta
    return inp


def _cmd_publish(
    content_id: str,
    *,
    dry_run: bool,
    slug: str | None,
) -> int:
    _load_dotenv()
    token = _env_token()
    pub_id = _env_publication_id()
    if not dry_run and not token:
        print("Missing HASHNODE_ACCESS_TOKEN.", file=sys.stderr)
        return 2
    if not pub_id and not dry_run:
        print("Missing HASHNODE_PUBLICATION_ID (run whoami, then set .env).", file=sys.stderr)
        return 2
    row = _tracker_row(content_id)
    fp = _final_path_for_row(row)
    if not fp.is_file():
        print(f"Missing file: {fp}", file=sys.stderr)
        return 1
    text = fp.read_text(encoding="utf-8")
    fm, body = _parse_front_matter(text)
    try:
        inp = _build_publish_input(
            fm=fm,
            body_md=body,
            publication_id=pub_id or "dry-run-placeholder",
            slug_override=slug,
        )
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    if dry_run:
        print(json.dumps({"input": inp}, indent=2, ensure_ascii=False))
        print(
            "\nDry-run only — no request sent. Remove --dry-run to publish.",
            file=sys.stderr,
        )
        return 0
    data = _gql_request(
        token=token,
        query=_PUBLISH_MUTATION,
        variables={"input": inp},
    )
    errs = data.get("errors")
    if errs:
        print(json.dumps(errs, indent=2), file=sys.stderr)
        return 1
    post = ((data.get("data") or {}).get("publishPost") or {}).get("post")
    if not post:
        print(json.dumps(data, indent=2), file=sys.stderr)
        return 1
    print(json.dumps(post, indent=2, ensure_ascii=False))
    print(
        "\nNext: open the URL above on workcrew.ai / Hashnode, confirm content, then:\n"
        f"  python -m src.tools.go_live_helpers record-live {content_id.strip().upper()} "
        "--i-confirmed-url-live",
        file=sys.stderr,
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    _load_dotenv()
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser(
        "whoami",
        help="Print Hashnode user + publications (needs HASHNODE_ACCESS_TOKEN)",
    )
    sub.add_parser(
        "publication-help",
        help="How to find HASHNODE_PUBLICATION_ID when the GraphQL API is down",
    )

    pp = sub.add_parser(
        "publish",
        help="Publish one week's 05_Final.md to Hashnode",
    )
    pp.add_argument("content_id", help="Tracker content_id, e.g. W09B")
    pp.add_argument(
        "--dry-run",
        action="store_true",
        help="Print GraphQL variables only; do not call the API",
    )
    pp.add_argument(
        "--slug",
        help="Override slug (default: last segment of canonical_url)",
    )

    args = p.parse_args(argv)
    try:
        if args.cmd == "whoami":
            return _cmd_whoami()
        if args.cmd == "publication-help":
            return _cmd_publication_help()
        if args.cmd == "publish":
            return _cmd_publish(
                args.content_id,
                dry_run=args.dry_run,
                slug=args.slug,
            )
    except RuntimeError as e:
        msg = str(e)
        print(f"hashnode_publish: {msg}", file=sys.stderr)
        if args.cmd in ("whoami", "publish") and (
            "HTTP 5" in msg
            or "HTTP 522" in msg
            or "HTTP 523" in msg
            or "HTTP 524" in msg
            or "Network error calling" in msg
        ):
            _print_api_unreachable_help()
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
