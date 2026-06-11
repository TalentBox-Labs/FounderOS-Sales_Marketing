import pandas as pd

from src.tools.runtime_paths import TRACKER_PATH, load_runtime_config
from src.tools.tracker_updater import _row_matches_active_week


def read_runtime_tracker(file_path: str | None = None) -> pd.DataFrame:
    """Read the runtime tracker CSV (absolute path when file_path is omitted)."""
    path = str(TRACKER_PATH if file_path is None else file_path)
    return pd.read_csv(path)


def _series_to_row_dict(series: pd.Series) -> dict[str, str]:
    """Dict suitable for tracker matching (NaN → empty string)."""
    out: dict[str, str] = {}
    for k, v in series.items():
        if pd.isna(v):
            out[str(k)] = ""
        else:
            out[str(k)] = str(v).strip()
    return out


def get_active_content(content_id: str | None = None) -> dict:
    """
    Return the tracker row for the given content_id (default: active_week from runtime config).

    When `active_week` is a bundle folder (e.g. W05) and the tracker only has split ids
    (W05A, W05B) with `artifact_folder=W05`, returns the first row in stable `content_id` order
    (same selection rule as split updates: W05A before W05B).
    """
    if content_id is None:
        content_id = load_runtime_config()["active_week"]

    key = str(content_id).strip()
    tracker = read_runtime_tracker()

    matches: list[dict] = []
    for _, series in tracker.iterrows():
        row = _series_to_row_dict(series)
        if _row_matches_active_week(row, key):
            matches.append(row)

    if not matches:
        raise ValueError(f"No tracker row found for content_id: {content_id}")

    matches.sort(key=lambda r: r.get("content_id", ""))
    return matches[0]


if __name__ == "__main__":
    active = get_active_content()

    print("\nRUNTIME TRACKER LOADED SUCCESSFULLY\n")
    for key, value in active.items():
        print(f"{key}: {value}")
