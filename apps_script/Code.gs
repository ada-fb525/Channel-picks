/**
 * Channel Picks: receives picks from the website and stores them in this Google Sheet.
 *
 * Every save becomes one new row in the "picks" tab. Rows are never edited or deleted,
 * so the Sheet is a full log. For analysis, only the latest row per code and section counts.
 *
 * Before deploying, change ORGANISER_KEY to a long phrase only you know.
 * You type it on the Results tab (index.html?organiser) to load everyone's picks.
 */
const ORGANISER_KEY = 'change-this-to-a-long-private-phrase';

const SHEET_NAME = 'picks';
const HEADER = ['received_at', 'code', 'level', 'section', 'width', 'height', 'no_channel', 'n_polygons', 'polygons', 'client_time'];
const LEVELS = ['MSc student', 'PhD student', 'Postdoc or researcher', 'Industry interpreter', 'Other'];
const MAX_POLYGON_CHARS = 45000; // a Sheet cell holds at most 50,000 characters

function doPost(e) {
  let d;
  try {
    d = JSON.parse(e.postData.contents);
  } catch (err) {
    return json_({ ok: false, error: 'bad request' });
  }
  return d.action === 'list' ? list_(d) : append_(d);
}

function doGet() {
  return json_({ ok: true, service: 'channel-picks' });
}

function append_(d) {
  const code = String(d.code || '').trim().toUpperCase();
  const section = String(d.section || '');
  const polygons = Array.isArray(d.polygons) ? d.polygons : [];
  const text = JSON.stringify(polygons);
  if (!/^(?=.*[A-Z])[A-Z0-9_-]{1,20}$/.test(code)) return json_({ ok: false, error: 'bad code' });
  if (!/^[A-Za-z0-9][\w.\- ]{0,119}$/.test(section)) return json_({ ok: false, error: 'bad section name' });
  if (text.length > MAX_POLYGON_CHARS) return json_({ ok: false, error: 'too many points' });
  const level = LEVELS.indexOf(d.level) >= 0 ? d.level : 'Other';
  const clientTime = /^[0-9T:.Z+-]{1,40}$/.test(String(d.client_time)) ? String(d.client_time) : '';

  const lock = LockService.getScriptLock();
  lock.waitLock(20000);
  try {
    sheet_().appendRow([
      new Date(), code, level, section,
      Number(d.width) || 0, Number(d.height) || 0,
      d.no_channel === true, polygons.length, text, clientTime,
    ]);
  } finally {
    lock.releaseLock();
  }
  return json_({ ok: true });
}

function list_(d) {
  if (ORGANISER_KEY.indexOf('change-this') === 0 || d.key !== ORGANISER_KEY) {
    return json_({ ok: false, error: 'wrong key' });
  }
  const values = sheet_().getDataRange().getValues();
  const head = values.shift();
  const rows = values.map(function (v) {
    const r = {};
    head.forEach(function (h, i) { r[h] = v[i]; });
    try { r.polygons = JSON.parse(r.polygons || '[]'); } catch (err) { r.polygons = []; }
    r.no_channel = r.no_channel === true || String(r.no_channel).toUpperCase() === 'TRUE';
    r.code = String(r.code);
    return r;
  });
  return json_({ ok: true, rows: rows });
}

function sheet_() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sh = ss.getSheetByName(SHEET_NAME);
  if (!sh) {
    sh = ss.insertSheet(SHEET_NAME);
    sh.appendRow(HEADER);
    sh.setFrozenRows(1);
    sh.getRange('B:B').setNumberFormat('@'); // keep codes as text
  }
  return sh;
}

function json_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}
