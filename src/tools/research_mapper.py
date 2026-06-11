from pathlib import Path

from src.tools.runtime_paths import load_runtime_config

_DEFAULT_RESEARCH = [
    "linkedin recruiter",
    "indeed",
    "ziprecruiter",
    "pricing",
    "pros",
    "cons",
    "best for",
]
_DEFAULT_SEO = [
    "alternatives to linkedin recruiter",
    "linkedin recruiter alternatives",
    "better job descriptions attract more applicants",
    "understand which skills to prioritize",
    "frequently asked questions",
]
_DEFAULT_CTA = [
    "try workcrew free",
    "try workcrew",
    "try it free",
    "explore workcrew",
    "create your workcrew profile",
]


def load(path):
    return Path(path).read_text(encoding="utf-8").lower()


def check_terms(text, terms, label):
    passed = []
    failed = []

    for term in terms:
        token = str(term).lower()
        if token in text:
            passed.append(f"- {label} contains: {term}")
        else:
            failed.append(f"- {label} missing: {term}")

    return passed, failed


def run_mapper():
    runtime = load_runtime_config()
    active = runtime["active_week"]

    research_path = runtime["research_path"]
    seo_plan_path = runtime["seo_plan_path"]
    output_path = f"{runtime['qa_output_dir']}{active}_Research_Map.md"

    gate = runtime.get("research_gate") or {}
    research_required = gate.get("research_required") or list(_DEFAULT_RESEARCH)
    seo_required = gate.get("seo_required") or list(_DEFAULT_SEO)
    cta_variants = gate.get("cta_variants") or list(_DEFAULT_CTA)

    research = load(research_path)
    seo = load(seo_plan_path)

    passed = []
    failed = []

    research_passed, research_failed = check_terms(
        research,
        research_required,
        "Research",
    )

    seo_passed, seo_failed = check_terms(
        seo,
        seo_required,
        "SEO Plan",
    )

    passed.extend(research_passed)
    passed.extend(seo_passed)

    failed.extend(research_failed)
    failed.extend(seo_failed)

    cta_found = any(str(c).lower() in seo for c in cta_variants if c is not None)

    if cta_found:
        passed.append("- SEO Plan contains approved CTA")
    else:
        failed.append("- SEO Plan missing approved CTA")

    report = []
    report.append(f"# {active} Research Mapping\n")

    report.append("## Passed Checks\n")
    report.extend(passed if passed else ["- None"])

    report.append("\n## Failed Checks\n")
    report.extend(failed if failed else ["- None"])

    report.append("\n## Final Verdict\n")
    report.append("FAIL" if failed else "PASS")

    final = "\n".join(report)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(final, encoding="utf-8")

    print(final)


if __name__ == "__main__":
    run_mapper()
