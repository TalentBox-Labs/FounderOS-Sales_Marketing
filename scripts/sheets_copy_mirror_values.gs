/**
 * WorkCrew CMS OS — copy from "Repo mirror" to reader tab (e.g. Content Tracker).
 *
 * Install: Google Sheet → Extensions → Apps Script → paste → Save.
 * Run syncMirrorToReader() once to test; add a time-driven trigger if desired.
 *
 * Default behaviour: **match rows by week ID in column A** (W01, W02, …).
 * That stays correct when Repo mirror rows are **reordered** (sync no longer assumes
 * the same physical row number on both tabs).
 *
 * Requirements:
 * - Both tabs use **column A** for `content_id`-style IDs (same as Repo mirror).
 * - Same 22-column contract A–V on data rows (see Phase4 PRD).
 *
 * If Content Tracker has merges / extra columns / IDs not in column A, use per-cell
 * formulas instead (see docs/Google_Sheet_Reader_Tab_Automation.md).
 */
const SOURCE_TAB = 'Repo mirror';
const TARGET_TAB = 'Content Tracker';
/** First data row (1-based) on Repo mirror (below the 22-column header row). */
const FIRST_DATA_ROW = 4;
const NUM_COLS = 22;
/** Column A (1-based) = week ID on both tabs. */
const ID_COL = 1;

function syncMirrorToReader() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const src = ss.getSheetByName(SOURCE_TAB);
  const dst = ss.getSheetByName(TARGET_TAB);
  if (!src) throw new Error('Missing source tab: ' + SOURCE_TAB);
  if (!dst) throw new Error('Missing target tab: ' + TARGET_TAB);

  const lastSrc = src.getLastRow();
  if (lastSrc < FIRST_DATA_ROW) return;

  /** @type {Object<string, string[]>} */
  const mirrorById = {};
  for (let r = FIRST_DATA_ROW; r <= lastSrc; r++) {
    const id = String(src.getRange(r, ID_COL).getDisplayValue()).trim();
    if (!id) continue;
    const rowVals = src.getRange(r, 1, r, NUM_COLS).getDisplayValues()[0];
    mirrorById[id] = rowVals;
  }

  const lastDst = dst.getLastRow();
  /** @type {Object<string, number>} */
  const dstRowById = {};
  for (let r = FIRST_DATA_ROW; r <= lastDst; r++) {
    const id = String(dst.getRange(r, ID_COL).getDisplayValue()).trim();
    if (id) dstRowById[id] = r;
  }

  let updated = 0;
  let skipped = 0;
  for (const id in mirrorById) {
    const vals = mirrorById[id];
    const destRow = dstRowById[id];
    if (destRow) {
      dst.getRange(destRow, 1, 1, NUM_COLS).setValues([vals]);
      updated++;
    } else {
      skipped++;
    }
  }

  Logger.log(
    'syncMirrorToReader: updated=' + updated + ' mirror-only-ids=' + skipped
  );
  try {
    SpreadsheetApp.getUi().alert(
      'syncMirrorToReader',
      'Updated rows: ' +
        updated +
        '. Mirror IDs with no Content Tracker row (column A): ' +
        skipped +
        '.',
      SpreadsheetApp.getUi().ButtonSet.OK
    );
  } catch (e) {
    // Time-driven triggers have no UI
  }
}
