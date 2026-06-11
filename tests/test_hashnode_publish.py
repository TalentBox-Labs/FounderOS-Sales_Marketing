"""Unit tests for Hashnode publish helper (no network)."""

from __future__ import annotations

from unittest import mock

from src.tools import hashnode_publish as hp


def test_graphql_headers_default_uses_ua(monkeypatch):
    monkeypatch.delenv("HASHNODE_AUTHORIZATION_BEARER", raising=False)
    monkeypatch.delenv("HASHNODE_USER_AGENT", raising=False)
    h = hp._graphql_headers(token="secret")
    assert h["Authorization"] == "secret"
    assert "Mozilla" in h["User-Agent"]
    assert h["Accept"] == "application/json"


def test_graphql_headers_bearer_mode(monkeypatch):
    monkeypatch.setenv("HASHNODE_AUTHORIZATION_BEARER", "true")
    h = hp._graphql_headers(token="abc")
    assert h["Authorization"] == "Bearer abc"


    assert (
        hp._slug_from_canonical(
            "https://workcrew.ai/blog/engineer-onboarding-retention",
            fallback="x",
        )
        == "engineer-onboarding-retention"
    )


def test_build_publish_input_minimal():
    fm = {
        "article_title": "Hello World",
        "canonical_url": "https://example.com/blog/hello-world",
        "primary_keyword": "hello world",
    }
    inp = hp._build_publish_input(
        fm=fm,
        body_md="# Hello\n\nBody.",
        publication_id="pub123",
        slug_override=None,
    )
    assert inp["title"] == "Hello World"
    assert inp["publicationId"] == "pub123"
    assert inp["contentMarkdown"].startswith("# Hello")
    assert inp["slug"] == "hello-world"
    assert inp["tags"]


def test_cmd_publish_dry_run_runs(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data").mkdir()
    (tmp_path / "input" / "W99").mkdir(parents=True)
    final = tmp_path / "input" / "W99" / "05_Final.md"
    final.write_text(
        "---\n"
        "article_title: Dry Run Title\n"
        "canonical_url: https://workcrew.ai/blog/dry-run-title\n"
        "primary_keyword: testing\n"
        "---\n\n# Hi\n",
        encoding="utf-8",
    )
    tracker = tmp_path / "tracker.csv"
    tracker.write_text(
        "content_id,title,final_output_path\n"
        f"W99,T,{final.relative_to(tmp_path)}\n",
        encoding="utf-8",
    )
    import src.tools.go_live_helpers as glh

    monkeypatch.setattr(glh, "TRACKER_PATH", tracker)
    monkeypatch.setattr(glh, "REPO_ROOT", tmp_path)
    rc = hp._cmd_publish("W99", dry_run=True, slug=None)
    assert rc == 0


@mock.patch.object(hp, "_gql_request")
def test_cmd_publish_calls_gql(mock_gql, tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data").mkdir()
    (tmp_path / "input" / "W98").mkdir(parents=True)
    final = tmp_path / "input" / "W98" / "05_Final.md"
    final.write_text(
        "---\narticle_title: T\ncanonical_url: https://workcrew.ai/blog/t\n"
        "primary_keyword: kw\n---\n\n# B\n",
        encoding="utf-8",
    )
    tracker = tmp_path / "tracker.csv"
    tracker.write_text(
        "content_id,title,final_output_path\n"
        f"W98,T,{final.relative_to(tmp_path)}\n",
        encoding="utf-8",
    )
    import src.tools.go_live_helpers as glh

    monkeypatch.setattr(glh, "TRACKER_PATH", tracker)
    monkeypatch.setattr(glh, "REPO_ROOT", tmp_path)
    monkeypatch.setenv("HASHNODE_ACCESS_TOKEN", "tok")
    monkeypatch.setenv("HASHNODE_PUBLICATION_ID", "pubid")
    mock_gql.return_value = {
        "data": {
            "publishPost": {
                "post": {
                    "id": "p1",
                    "title": "T",
                    "slug": "t",
                    "url": "https://workcrew.ai/blog/t",
                }
            }
        }
    }
    rc = hp._cmd_publish("W98", dry_run=False, slug=None)
    assert rc == 0
    mock_gql.assert_called_once()
    args, kwargs = mock_gql.call_args
    assert kwargs["token"] == "tok"
    assert "PublishPost" in kwargs["query"]
    var = kwargs["variables"]["input"]
    assert var["publicationId"] == "pubid"
    assert var["slug"] == "t"
    out = capsys.readouterr()
    assert "workcrew.ai" in out.err or "record-live" in out.err


def test_main_publication_help():
    assert hp.main(["publication-help"]) == 0


def test_main_whoami_transport_error_exit_3(monkeypatch):
    def boom():
        raise RuntimeError("HTTP 522: connection timed out")

    monkeypatch.setattr(hp, "_cmd_whoami", boom)
    assert hp.main(["whoami"]) == 3
