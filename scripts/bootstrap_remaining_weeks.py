#!/usr/bin/env python3
"""One-off scaffold for W07B, W09A, W09B, W10 — programme placeholders + week_runtime JSON.

For canonical tracker-driven fixture sync across all weeks, use:
    python scripts/generate_week_fixtures.py
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "input"
PROFILES = ROOT / "data" / "week_runtime"

WEEKS: list[dict] = [
    {
        "id": "W07B",
        "title": "Hiring Manager Alignment: Syncing Before the Tech Interview",
        "slug": "hiring-manager-tech-interview-alignment",
        "date": "2026-07-07",
        "research": [
            "hiring manager",
            "interview alignment",
            "tech hiring",
            "debrief",
            "recruiters",
        ],
        "seo_extra": "hiring manager alignment",
        "kw": "hiring manager interview alignment",
    },
    {
        "id": "W09A",
        "title": "Tech Offer Negotiation: Closing Without Last-Minute Surprises",
        "slug": "tech-offer-negotiation-closing",
        "date": "2026-07-14",
        "research": [
            "offer negotiation",
            "compensation transparency",
            "closing candidates",
            "engineers",
            "recruiters",
        ],
        "seo_extra": "tech offer negotiation",
        "kw": "tech offer negotiation",
    },
    {
        "id": "W09B",
        "title": "Engineer Onboarding: Two Weeks That Protect Retention",
        "slug": "engineer-onboarding-retention",
        "date": "2026-07-21",
        "research": [
            "engineer onboarding",
            "retention",
            "handoff",
            "first weeks",
            "team integration",
        ],
        "seo_extra": "engineer onboarding",
        "kw": "engineer onboarding",
    },
    {
        "id": "W10",
        "title": "Q3 Tech Hiring Roadmap: Metrics That Survive Budget Reviews",
        "slug": "q3-tech-hiring-roadmap",
        "date": "2026-07-28",
        "research": [
            "hiring roadmap",
            "Q3 planning",
            "metrics review",
            "engineering hiring",
            "workcrew",
        ],
        "seo_extra": "tech hiring roadmap",
        "kw": "tech hiring roadmap",
    },
]


def gate_seo(extra: str) -> list[str]:
    return [
        "meta description",
        "title tag",
        "canonical",
        "h1 tag",
        "frequently asked questions",
        extra,
    ]


def write_week(w: dict) -> None:
    wid = w["id"]
    base = INPUT / wid
    base.mkdir(parents=True, exist_ok=True)
    canon = f"https://workcrew.ai/blog/{w['slug']}"
    rblock = "\n\n".join(f"Research note: **{t}** — operational framing for the Writer; replace with sourced detail." for t in w["research"])

    (base / "01_Content_Brief.md").write_text(
        f"# Content Brief — {wid}\n\n## {w['title']}\n\nApproved for SEO → research → draft.\n",
        encoding="utf-8",
    )
    (base / "02_SEO_Plan.md").write_text(
        "\n".join(
            [
                f"# SEO Plan — {wid}",
                f"## {w['title']}",
                f"> Primary keyword: {w['kw']}",
                f"> Canonical: `{canon}`",
                "",
                "Gate strings: **meta description**, **title tag**, **canonical**, **h1 tag**, "
                "**frequently asked questions**, **" + w["seo_extra"] + "**.",
                "",
                "## Meta description",
                "Placeholder meta description for gate: meta description title tag canonical h1 tag.",
                "",
                "## Title tag",
                "Under sixty characters for title tag checks.",
                "",
                "## H1",
                f"{w['title']}",
                "",
                "## h1 tag",
                "Single visible h1 tag must match H1 above.",
                "",
                "## CTA",
                "try workcrew free explore workcrew create your workcrew profile try workcrew",
                "",
                "## FAQ",
                "Article body must include **Frequently Asked Questions** heading.",
            ]
        ),
        encoding="utf-8",
    )
    (base / "03_Research.md").write_text(f"# Research — {wid}\n\n{rblock}\n", encoding="utf-8")
    tmpl = (INPUT / "W06B" / "04_Draft.md").read_text(encoding="utf-8")
    tmpl = tmpl.replace("W06B", wid).replace("Tech Sourcing Metrics: What to Track Before You Add Another Seat", w["title"])
    (base / "04_Draft.md").write_text(tmpl, encoding="utf-8")

    body = f"""---
week_id: {wid}
article_title: "{w['title']}"
primary_keyword: {w['kw']}
search_intent: informational
funnel_stage: consideration
status: In Review
publish_status: in review
publish_date: "{w['date']}"
canonical_url: {canon}
cta_type: try_workcrew_free
word_count_target: "1800"
seo_status: Pending
---

# {w['title']}

Opening uses **{w['kw']}** and ties to programme **tech hiring** themes. Internal bridge: see [tech hiring feedback loops](https://workcrew.ai/blog/tech-hiring-feedback-loops) and [tech sourcing metrics](https://workcrew.ai/blog/tech-sourcing-metrics-recruiters).

## Why this matters

Operational section connecting research themes without invented statistics.

## What to do next

Practical checklist for recruiters and hiring managers.

## Where WorkCrew fits

When intake is structured, you can **try WorkCrew free** to test skills-native matching on the same reqs.

## Frequently Asked Questions

### Who owns this step?

Recruiting and hiring manager jointly — with dated updates.

### What is out of scope?

Legal compensation advice; this is process framing only.
"""
    (base / "05_Final.md").write_text(body, encoding="utf-8")
    (base / "06_Design_Brief.md").write_text(
        f"# Design Brief — {wid}\n\nHero: programme placeholder; slug `{w['slug']}`.\n" * 5,
        encoding="utf-8",
    )
    (base / "07_Social_Posts.md").write_text(
        f"# Social — {wid}\n\nDraft posts after final URL live. " + "x" * 120 + "\n",
        encoding="utf-8",
    )
    (base / "08_Email_Copy.md").write_text(
        f"# Email — {wid}\n\nNewsletter stub. " + "y" * 120 + "\n",
        encoding="utf-8",
    )
    checklist = (
        "\n".join(
            [
                f"# Publish Checklist — {wid}",
                "## Article Information",
                f"- Title: {w['title']}",
                "",
                "# Content QA",
                "- Final reviewed",
                "",
                "# SEO QA",
                "- Meta checked",
                "",
                "# Brand QA",
                "- Tone ok",
                "",
                "# Technical QA",
                "- Markdown ok",
                "",
                "# Final Approval",
                "- Sign-off",
            ]
        )
        + "\n"
        + ("More body text for length. " * 20)
    )
    (base / "09_Publish_Checklist.md").write_text(checklist, encoding="utf-8")

    profile = {
        "active_week": wid,
        "content_status": "Draft",
        "draft_path": f"input/{wid}/04_Draft.md",
        "final_path": f"input/{wid}/05_Final.md",
        "research_path": f"input/{wid}/03_Research.md",
        "seo_plan_path": f"input/{wid}/02_SEO_Plan.md",
        "qa_output_dir": "output/qa_reports/",
        "publish_status": "In Progress",
        "draft_validation_mode": "template",
        "research_gate": {
            "research_required": w["research"],
            "seo_required": gate_seo(w["seo_extra"]),
            "cta_variants": [
                "try workcrew",
                "try workcrew free",
                "explore workcrew",
                "create your workcrew profile",
            ],
        },
        "validators": [
            "research_mapper",
            "draft_validator",
            "structure_checker",
            "metadata_checker",
            "publish_checklist_checker",
        ],
        "enable_crewai_qa": False,
    }
    (PROFILES / f"{wid}.json").write_text(
        json.dumps(profile, indent=2) + "\n", encoding="utf-8"
    )


def main() -> None:
    for w in WEEKS:
        write_week(w)
        print("scaffolded", w["id"])


if __name__ == "__main__":
    main()
