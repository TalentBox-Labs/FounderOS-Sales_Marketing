"""Unit tests for reader_tab_sync helpers."""

from __future__ import annotations

from src.tools.reader_tab_sync import _row_cells_to_dict
from src.tools.sheet_sync import SHEET_HEADERS


def test_row_cells_to_dict_pads_and_maps_headers() -> None:
    cells = ["W01", "M1/Wk1"] + [""] * (len(SHEET_HEADERS) - 2)
    d = _row_cells_to_dict(cells)
    assert d["ID"] == "W01"
    assert d["Month/Week"] == "M1/Wk1"
    assert d["Status"] == ""
    assert len(d) == len(SHEET_HEADERS)
