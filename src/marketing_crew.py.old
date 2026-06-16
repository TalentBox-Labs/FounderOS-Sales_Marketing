"""
Marketing Content Agent — multi-brand, multi-channel.

Produces blog articles (SEO/GEO/AEO-optimised) + social content
(LinkedIn, Instagram, YouTube) for WorkCrew, HireStack, and Founder brand.

Usage:
    python -m src.marketing_crew --brand workcrew --topic "linkedin recruiter alternatives" \\
        --keyword "linkedin recruiter alternatives" --geo "United States" \\
        --funnel consideration --output output/marketing/W01

    python -m src.marketing_crew --brand founder --topic "why I left corporate recruiting" \\
        --keyword "founder story recruiting" --funnel awareness
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

import yaml
from crewai import Agent, Crew, Process, Task

from src.crew import BASE_DIR, build_crew_llm, load_yaml, save_file

# ── Constants ────────────────────────────────────────────────────────────────

BRANDS = ("workcrew", "hirestack", "founder")
FUNNEL_STAGES = ("awareness", "consideration", "decision")

BRAND_CTA = {
    "workcrew":  "Try WorkCrew free",
    "hirestack": "Get started with HireStack",
    "founder":   "Read more on my blog",
}

BRAND_BASE_URL = {
    "workcrew":  "https://workcrew.ai/blog",
    "hirestack": "https://hirestack.io/blog",
    "founder":   "https://cyril.ai/posts",
}

BRAND_COLORS = {
    "workcrew":  "deep navy blue (#0f1c3f) and white, with electric blue (#3b82f6) accent",
    "hirestack": "teal (#0d9488) and dark charcoal (#1a1a2e), with lime (#84cc16) accent",
    "founder":   "warm off-white (#faf8f5) and dark slate (#1e293b), with terracotta (#c2714f) accent",
}

OUTPUT_FILES = [
    "01_Strategy_Brief.md",
    "02_Blog_Article.md",
    "03_LinkedIn_Post.md",
    "04_Instagram_Post.md",
    "05_YouTube_Content.md",
    "06_Image_Prompts.md",
    "07_SEO_Metadata.md",
    "08_Publish_Status.json",
]

# ── Helpers ──────────────────────────────────────────────────────────────────


def _slug_from_keyword(keyword: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", keyword.lower().strip()).strip("-")


def _output_dir(brand: str, keyword: str, output_root: str | None) -> Path:
    if output_root:
        return BASE_DIR / output_root.strip().rstrip("/")
    slug = _slug_from_keyword(keyword)
    return BASE_DIR / "output" / "marketing" / brand / slug


def _run_agent_task(
    *,
    agent_cfg: dict,
    description: str,
    expected_output: str,
    llm,
    context_tasks: list[Task] | None = None,
) -> tuple[str, Task]:
    agent = Agent(
        config=agent_cfg,
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )
    task = Task(
        description=description,
        expected_output=expected_output,
        agent=agent,
        context=context_tasks or [],
    )
    return agent, task


def _inject_context(template: str, **kwargs: str) -> str:
    """Simple {key} substitution for task descriptions."""
    for k, v in kwargs.items():
        template = template.replace("{" + k + "}", v or "")
    return template


# ── Core generation ──────────────────────────────────────────────────────────


def run_marketing_crew(
    *,
    brand: str,
    topic: str,
    target_keyword: str,
    geo_target: str = "",
    funnel_stage: str = "consideration",
    output_root: str | None = None,
    skip_publish: bool = True,
) -> dict:
    """
    Run the full marketing content pipeline and save outputs.

    Returns a dict of {filename: output_path} for each artifact produced.
    """
    brand = brand.lower().strip()
    if brand not in BRANDS:
        raise ValueError(f"brand must be one of {BRANDS}, got {brand!r}")
    funnel_stage = funnel_stage.lower().strip()
    if funnel_stage not in FUNNEL_STAGES:
        funnel_stage = "consideration"

    out_dir = _output_dir(brand, target_keyword, output_root)
    out_dir.mkdir(parents=True, exist_ok=True)

    llm = build_crew_llm()
    agents_cfg = load_yaml("src/agents_marketing.yaml")
    tasks_cfg = load_yaml("src/tasks_marketing.yaml")

    slug = _slug_from_keyword(target_keyword)
    canonical_url = f"{BRAND_BASE_URL[brand]}/{slug}"
    brand_colors = BRAND_COLORS[brand]
    cta = BRAND_CTA[brand]

    ctx = dict(
        brand=brand,
        topic=topic,
        target_keyword=target_keyword,
        geo_target=geo_target or "global",
        funnel_stage=funnel_stage,
        canonical_url=canonical_url,
        brand_colors=brand_colors,
        cta=cta,
        today=str(date.today()),
    )

    # ── Build agent+task objects ─────────────────────────────────────────────
    def _task(agent_key: str, task_key: str, extra_ctx: str = "") -> tuple:
        ac = agents_cfg[agent_key]
        tc = tasks_cfg[task_key]
        desc = (
            f"## Context\n"
            f"- Brand: {brand}\n"
            f"- Topic: {topic}\n"
            f"- Primary keyword: {target_keyword}\n"
            f"- GEO target: {geo_target or 'global'}\n"
            f"- Funnel stage: {funnel_stage}\n"
            f"- Canonical URL: {canonical_url}\n"
            f"- Brand CTA: {cta}\n"
            f"- Brand colors: {brand_colors}\n"
            f"- Date: {date.today()}\n"
            + (f"\n{extra_ctx}\n" if extra_ctx else "")
            + f"\n## Task instructions\n{tc['description']}"
        )
        agent = Agent(
            config=ac, llm=llm, verbose=True, allow_delegation=False,
        )
        task = Task(
            description=desc,
            expected_output=tc["expected_output"],
            agent=agent,
        )
        return agent, task

    strat_agent, strat_task     = _task("content_strategist", "strategy_brief_task")
    blog_agent,  blog_task      = _task("blog_writer",        "blog_article_task")
    li_agent,    li_task        = _task("social_copywriter",  "linkedin_post_task")
    ig_agent,    ig_task        = _task("social_copywriter",  "instagram_post_task")
    yt_agent,    yt_task        = _task("social_copywriter",  "youtube_content_task")
    img_agent,   img_task       = _task("image_director",     "image_prompt_task")
    seo_agent,   seo_task       = _task("seo_optimiser",      "seo_metadata_task")

    # ── Set context dependencies ─────────────────────────────────────────────
    blog_task.context  = [strat_task]
    li_task.context    = [blog_task]
    ig_task.context    = [blog_task]
    yt_task.context    = [blog_task]
    img_task.context   = [blog_task, ig_task, yt_task]
    seo_task.context   = [blog_task]

    crew = Crew(
        agents=[strat_agent, blog_agent, li_agent, ig_agent,
                yt_agent, img_agent, seo_agent],
        tasks=[strat_task, blog_task, li_task, ig_task,
               yt_task, img_task, seo_task],
        process=Process.sequential,
        verbose=True,
    )

    crew.kickoff()

    # ── Save outputs ─────────────────────────────────────────────────────────
    task_file_map = {
        strat_task: "01_Strategy_Brief.md",
        blog_task:  "02_Blog_Article.md",
        li_task:    "03_LinkedIn_Post.md",
        ig_task:    "04_Instagram_Post.md",
        yt_task:    "05_YouTube_Content.md",
        img_task:   "06_Image_Prompts.md",
        seo_task:   "07_SEO_Metadata.md",
    }

    results = {}
    for task, fname in task_file_map.items():
        content = str(task.output.raw if hasattr(task, "output") and task.output else "")
        path = out_dir / fname
        path.write_text(content, encoding="utf-8")
        results[fname] = str(path.relative_to(BASE_DIR))

    # ── Publish status manifest ───────────────────────────────────────────────
    status = {
        "brand": brand,
        "topic": topic,
        "target_keyword": target_keyword,
        "canonical_url": canonical_url,
        "geo_target": geo_target or "global",
        "funnel_stage": funnel_stage,
        "generated_at": str(date.today()),
        "artifacts": results,
        "published": {
            "hashnode": False,
            "linkedin": False,
            "instagram": False,
            "youtube": False,
        },
    }
    status_path = out_dir / "08_Publish_Status.json"
    status_path.write_text(json.dumps(status, indent=2), encoding="utf-8")
    results["08_Publish_Status.json"] = str(status_path.relative_to(BASE_DIR))

    print(f"\n✓ Marketing content generated → {out_dir.relative_to(BASE_DIR)}")
    for fname, rel in results.items():
        print(f"  {fname}: {rel}")

    return results


# ── CLI ──────────────────────────────────────────────────────────────────────


def _cli() -> None:
    parser = argparse.ArgumentParser(
        description="Marketing Content Agent — SEO/GEO/AEO blog + social"
    )
    parser.add_argument("--brand", required=True, choices=list(BRANDS),
                        help="workcrew | hirestack | founder")
    parser.add_argument("--topic", required=True,
                        help="Article topic or content angle")
    parser.add_argument("--keyword", required=True, dest="target_keyword",
                        help="Primary SEO keyword")
    parser.add_argument("--geo", default="", dest="geo_target",
                        help="Geographic target (e.g. 'United States', blank = global)")
    parser.add_argument("--funnel", default="consideration", dest="funnel_stage",
                        choices=list(FUNNEL_STAGES))
    parser.add_argument("--output", default=None,
                        help="Output directory (repo-relative). Default: output/marketing/{brand}/{slug}")
    args = parser.parse_args()

    run_marketing_crew(
        brand=args.brand,
        topic=args.topic,
        target_keyword=args.target_keyword,
        geo_target=args.geo_target,
        funnel_stage=args.funnel_stage,
        output_root=args.output,
    )


if __name__ == "__main__":
    _cli()
