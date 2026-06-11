import json

from src.tools.runtime_paths import RUNTIME_CONFIG_PATH


def load_config():
    with RUNTIME_CONFIG_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_config(config):
    RUNTIME_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)

    with RUNTIME_CONFIG_PATH.open("w", encoding="utf-8") as file:
        json.dump(config, file, indent=2)

    print("Runtime config updated successfully.")


_WEEK_SPECIFIC_RUNTIME_KEYS = (
    "research_gate",
    "publish_checklist_section_markers",
    "draft_validation_mode",
    "draft_article_min_words",
)


def set_active_week(week_id):
    config = load_config()

    config["active_week"] = week_id
    config["draft_path"] = f"input/{week_id}/04_Draft.md"
    config["final_path"] = f"input/{week_id}/05_Final.md"
    config["research_path"] = f"input/{week_id}/03_Research.md"
    config["seo_plan_path"] = f"input/{week_id}/02_SEO_Plan.md"
    config["publish_status"] = "In Progress"

    for key in _WEEK_SPECIFIC_RUNTIME_KEYS:
        config.pop(key, None)

    save_config(config)


def show_config():
    config = load_config()
    print(json.dumps(config, indent=2, sort_keys=True))


if __name__ == "__main__":
    show_config()
