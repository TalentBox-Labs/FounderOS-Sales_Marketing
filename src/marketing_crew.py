"""Marketing content crew using BaseCrew pattern."""

from __future__ import annotations

import json
import logging
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

from crewai import Agent, Task

from src.base_crew import BaseCrew

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────

BRANDS = ("workcrew", "hirestack", "founder")
FUNNEL_STAGES = ("awareness", "consideration", "decision")

BRAND_CTA = {
    "workcrew": "Try WorkCrew free",
    "hirestack": "Get started with HireStack",
    "founder": "Read more on my blog",
}

BRAND_BASE_URL = {
    "workcrew": "https://workcrew.ai/blog",
    "hirestack": "https://hirestack.io/blog",
    "founder": "https://cyril.ai/posts",
}

BRAND_COLORS = {
    "workcrew": "deep navy blue (#0f1c3f) and white, with electric blue (#3b82f6) accent",
    "hirestack": "teal (#0d9488) and dark charcoal (#1a1a2e), with lime (#84cc16) accent",
    "founder": "warm off-white (#faf8f5) and dark slate (#1e293b), with terracotta (#c2714f) accent",
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


class MarketingCrew(BaseCrew):
    """Marketing content crew for multi-brand, multi-channel content generation."""

    def __init__(self, repo_root: Path | None = None):
        """Initialize marketing crew."""
        super().__init__(
            name="marketing",
            agents_yaml_path="src/agents_marketing.yaml",
            tasks_yaml_path="src/tasks_marketing.yaml",
            repo_root=repo_root,
        )
        self.brand: str | None = None
        self.topic: str | None = None
        self.target_keyword: str | None = None
        self.geo_target: str = ""
        self.funnel_stage: str = "consideration"
        self.output_root: str | None = None

    def build_agents_and_tasks(self) -> tuple[list[Agent], list[Task]]:
        """Build marketing crew agents and tasks."""
        brand = self.brand or "workcrew"
        topic = self.topic or ""
        target_keyword = self.target_keyword or ""
        geo_target = self.geo_target or "global"
        funnel_stage = self.funnel_stage or "consideration"

        slug = self._slug_from_keyword(target_keyword)
        canonical_url = f"{BRAND_BASE_URL[brand]}/{slug}"
        brand_colors = BRAND_COLORS[brand]
        cta = BRAND_CTA[brand]

        # Create agents
        strat_agent = Agent(
            config=self.agents_config.get("content_strategist", {}),
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
        )
        blog_agent = Agent(
            config=self.agents_config.get("blog_writer", {}),
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
        )
        li_agent = Agent(
            config=self.agents_config.get("social_copywriter", {}),
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
        )
        ig_agent = Agent(
            config=self.agents_config.get("social_copywriter", {}),
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
        )
        yt_agent = Agent(
            config=self.agents_config.get("social_copywriter", {}),
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
        )
        img_agent = Agent(
            config=self.agents_config.get("image_director", {}),
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
        )
        seo_agent = Agent(
            config=self.agents_config.get("seo_optimiser", {}),
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
        )

        # Build context string
        ctx_str = f"""## Context
- Brand: {brand}
- Topic: {topic}
- Primary keyword: {target_keyword}
- GEO target: {geo_target}
- Funnel stage: {funnel_stage}
- Canonical URL: {canonical_url}
- Brand CTA: {cta}
- Brand colors: {brand_colors}
- Date: {date.today()}
"""

        # Create tasks with descriptions
        strat_cfg = self.tasks_config.get("strategy_brief_task", {})
        strat_task = Task(
            config=strat_cfg,
            agent=strat_agent,
            description=f"{ctx_str}\n## Task instructions\n{strat_cfg.get('description', '')}",
        )

        blog_cfg = self.tasks_config.get("blog_article_task", {})
        blog_task = Task(
            config=blog_cfg,
            agent=blog_agent,
            description=f"{ctx_str}\n## Task instructions\n{blog_cfg.get('description', '')}",
        )

        li_cfg = self.tasks_config.get("linkedin_post_task", {})
        li_task = Task(
            config=li_cfg,
            agent=li_agent,
            description=f"{ctx_str}\n## Task instructions\n{li_cfg.get('description', '')}",
        )

        ig_cfg = self.tasks_config.get("instagram_post_task", {})
        ig_task = Task(
            config=ig_cfg,
            agent=ig_agent,
            description=f"{ctx_str}\n## Task instructions\n{ig_cfg.get('description', '')}",
        )

        yt_cfg = self.tasks_config.get("youtube_content_task", {})
        yt_task = Task(
            config=yt_cfg,
            agent=yt_agent,
            description=f"{ctx_str}\n## Task instructions\n{yt_cfg.get('description', '')}",
        )

        img_cfg = self.tasks_config.get("image_prompt_task", {})
        img_task = Task(
            config=img_cfg,
            agent=img_agent,
            description=f"{ctx_str}\n## Task instructions\n{img_cfg.get('description', '')}",
        )

        seo_cfg = self.tasks_config.get("seo_metadata_task", {})
        seo_task = Task(
            config=seo_cfg,
            agent=seo_agent,
            description=f"{ctx_str}\n## Task instructions\n{seo_cfg.get('description', '')}",
        )

        # Set context dependencies for sequential processing
        blog_task.context = [strat_task]
        li_task.context = [blog_task]
        ig_task.context = [blog_task]
        yt_task.context = [blog_task]
        img_task.context = [blog_task, ig_task, yt_task]
        seo_task.context = [blog_task]

        return (
            [strat_agent, blog_agent, li_agent, ig_agent, yt_agent, img_agent, seo_agent],
            [strat_task, blog_task, li_task, ig_task, yt_task, img_task, seo_task],
        )

    def validate_output(self, output: str) -> tuple[bool, list[str]]:
        """Validate marketing crew output."""
        errors = []
        if not output or len(output.strip()) < 50:
            errors.append("Marketing output is too short")
        return len(errors) == 0, errors

    def run_marketing_crew(
        self,
        *,
        brand: str,
        topic: str,
        target_keyword: str,
        geo_target: str = "",
        funnel_stage: str = "consideration",
        output_root: str | None = None,
    ) -> dict[str, str]:
        """
        Run marketing crew and save outputs.

        Args:
            brand: Brand name (workcrew, hirestack, founder)
            topic: Content topic
            target_keyword: Primary SEO keyword
            geo_target: Geographic target (default: global)
            funnel_stage: Funnel stage (awareness, consideration, decision)
            output_root: Output directory (repo-relative; auto-generated if None)

        Returns:
            Mapping of filename → relative_path for all artifacts produced
        """
        brand = brand.lower().strip()
        if brand not in BRANDS:
            raise ValueError(f"brand must be one of {BRANDS}, got {brand!r}")
        funnel_stage = funnel_stage.lower().strip()
        if funnel_stage not in FUNNEL_STAGES:
            funnel_stage = "consideration"

        self.brand = brand
        self.topic = topic
        self.target_keyword = target_keyword
        self.geo_target = geo_target
        self.funnel_stage = funnel_stage
        self.output_root = output_root

        out_dir = self._output_dir()
        out_dir.mkdir(parents=True, exist_ok=True)

        result_text = self.run()

        slug = self._slug_from_keyword(target_keyword)
        canonical_url = f"{BRAND_BASE_URL[brand]}/{slug}"

        # Save artifacts from task outputs
        # In a real CrewAI run, we'd extract individual task outputs
        # For now, save the result to all output files
        results = {}
        for fname in OUTPUT_FILES[:-1]:  # All except JSON status
            path = out_dir / fname
            path.write_text(result_text, encoding="utf-8")
            results[fname] = str(path.relative_to(self.repo_root))

        # Create publish status manifest
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
        results["08_Publish_Status.json"] = str(status_path.relative_to(self.repo_root))

        logger.info(
            "Wrote marketing content",
            extra={"brand": brand, "keyword": target_keyword, "output_dir": str(out_dir)},
        )

        return results

    def _output_dir(self) -> Path:
        """Determine output directory."""
        if self.output_root:
            return self.repo_root / self.output_root.strip().rstrip("/")
        slug = self._slug_from_keyword(self.target_keyword or "")
        return self.repo_root / "output" / "marketing" / (self.brand or "workcrew") / slug

    @staticmethod
    def _slug_from_keyword(keyword: str) -> str:
        """Convert keyword to slug."""
        return re.sub(r"[^a-z0-9]+", "-", keyword.lower().strip()).strip("-")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Marketing Content Agent — SEO/GEO/AEO blog + social"
    )
    parser.add_argument(
        "--brand", required=True, choices=list(BRANDS), help="workcrew | hirestack | founder"
    )
    parser.add_argument("--topic", required=True, help="Article topic or content angle")
    parser.add_argument(
        "--keyword", required=True, dest="target_keyword", help="Primary SEO keyword"
    )
    parser.add_argument(
        "--geo", default="", dest="geo_target", help="Geographic target (e.g. 'United States')"
    )
    parser.add_argument(
        "--funnel",
        default="consideration",
        dest="funnel_stage",
        choices=list(FUNNEL_STAGES),
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output directory (repo-relative). Default: output/marketing/{brand}/{slug}",
    )
    args = parser.parse_args()

    try:
        crew = MarketingCrew()
        results = crew.run_marketing_crew(
            brand=args.brand,
            topic=args.topic,
            target_keyword=args.target_keyword,
            geo_target=args.geo_target,
            funnel_stage=args.funnel_stage,
            output_root=args.output,
        )
        print("\n" + "=" * 80)
        print("MARKETING CREW RESULTS")
        print("=" * 80)
        for fname, rel in results.items():
            print(f"  {fname}: {rel}")
        print()
    except ValueError as err:
        print(f"ERROR: {err}", file=sys.stderr)
        sys.exit(1)
