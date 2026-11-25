/**
 * Nightly backup of a Tiller Google Sheet, with retention.
 *
 * Runs in YOUR Google account as a standalone Apps Script project, on a daily time trigger.
 * Each run:
 *   1. copies the live sheet into the backup folder as
 *        BACKUP <yyyy-MM-dd> nightly - <sheet title>
 *      (skipped if today's copy already exists);
 *   2. moves to the Trash (recoverable for 30 days) the nightly copies this script made that
 *      fall outside the retention policy: keep the last KEEP_DAYS days, plus the earliest
 *      copy of every month before that.
 *
 * Pruning only ever touches files that (a) sit in the backup folder, (b) carry this script's
 * tag in their Drive description, (c) are named like a nightly copy, and (d) are not the live
 * sheet. Hand-made "pre-<step>" copies and anything else in the folder are never touched.
 *
 * Paste this whole file into Code.gs. The editor's Run menu then lists the four functions you
 * use: nightlyBackup, dryRunPrune, installTrigger and removeTrigger. Names ending in "_" are
 * helpers that Apps Script hides from that menu.
 *
 * Settings live in Script Properties (Project Settings > Script properties), not in code:
 *   SOURCE_SHEET_ID   required  the live Tiller sheet's ID (from its URL)
 *   BACKUP_FOLDER_ID  optional  the backup folder's ID; if unset, a single folder named
 *                               "Tiller Backups" in My Drive is used, created if missing
 *   KEEP_DAYS         optional  default 30
 *   MAX_TRASH_PER_RUN optional  default 5, a brake in case something is misconfigured
 *
 * A copy is a new file with a new ID. Tiller's Direct Fills fill the sheets linked to your
 * Tiller account, so a copy receives nothing unless someone links it. Never link a backup.
 */

var TAG = 'tiller-nightly-backup v1';
var NAME_RE = /^BACKUP (\d{4}-\d{2}-\d{2}) nightly - /;
var DEFAULT_FOLDER_NAME = 'Tiller Backups';

/** Entry point for the daily trigger. */
function nightlyBackup() {
  // A manual Run and the trigger can overlap; only one may copy at a time.
  var lock = LockService.getScriptLock();
  if (!lock.tryLock(30 * 1000)) {
    console.log('Another run is in progress; skipping this one.');
    return;
  }
  try {
    backupAndPrune_();
  } finally {
    lock.releaseLock();
  }
}

function backupAndPrune_() {
  var cfg = readConfig_();
  var source = DriveApp.getFileById(cfg.sourceId);
  var folder = backupFolder_(cfg);
  var today = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'yyyy-MM-dd');
  var name = 'BACKUP ' + today + ' nightly - ' + source.getName();

  if (hasLiveFile_(folder.getFilesByName(name))) {
    console.log('Already backed up today: ' + name);
  } else {
    var copy = source.makeCopy(name, folder);
    copy.setDescription(TAG + ' source=' + cfg.sourceId + ' made=' + new Date().toISOString());
    console.log('Copied: ' + name + ' (' + copy.getId() + ')');
  }
  prune_(cfg, folder, false);
}

/** Lists what pruning would trash, without trashing anything. Run it by hand first. */
function dryRunPrune() {
  var cfg = readConfig_();
  prune_(cfg, backupFolder_(cfg), true);
}

/** Creates the daily trigger (between 2 and 3 AM in the script's time zone). Run once. */
function installTrigger() {
  removeTrigger();
  ScriptApp.newTrigger('nightlyBackup').timeBased().everyDays(1).atHour(2).create();
  console.log('Daily trigger installed for nightlyBackup, 2-3 AM ' + Session.getScriptTimeZone());
}

/** Removes this project's nightlyBackup triggers. */
function removeTrigger() {
  ScriptApp.getProjectTriggers().forEach(function (t) {
    if (t.getHandlerFunction() === 'nightlyBackup') ScriptApp.deleteTrigger(t);
  });
}

/** True if the iterator holds a file that isn't in the Trash. */
function hasLiveFile_(files) {
  while (files.hasNext()) {
    if (!files.next().isTrashed()) return true;
  }
  return false;
}

function readConfig_() {
  var p = PropertiesService.getScriptProperties();
  var sourceId = (p.getProperty('SOURCE_SHEET_ID') || '').trim();
  if (!sourceId) throw new Error('Set SOURCE_SHEET_ID in Project Settings > Script properties.');
  return {
    sourceId: sourceId,
    folderId: (p.getProperty('BACKUP_FOLDER_ID') || '').trim(),
    keepDays: parseInt(p.getProperty('KEEP_DAYS') || '30', 10),
    maxTrash: parseInt(p.getProperty('MAX_TRASH_PER_RUN') || '5', 10)
  };
}

function backupFolder_(cfg) {
  if (cfg.folderId) return DriveApp.getFolderById(cfg.folderId);
  var it = DriveApp.getRootFolder().getFoldersByName(DEFAULT_FOLDER_NAME);
  if (!it.hasNext()) return DriveApp.getRootFolder().createFolder(DEFAULT_FOLDER_NAME);
  var folder = it.next();
  if (it.hasNext()) {
    throw new Error('More than one "' + DEFAULT_FOLDER_NAME + '" folder in My Drive; set BACKUP_FOLDER_ID.');
  }
  return folder;
}

function prune_(cfg, folder, dryRun) {
  var me = Session.getEffectiveUser().getEmail();
  var candidates = [];
  var files = folder.getFiles();
  while (files.hasNext()) {
    var f = files.next();
    if (f.getId() === cfg.sourceId || f.isTrashed()) continue;
    if ((f.getDescription() || '').indexOf(TAG) !== 0) continue;
    var owner = f.getOwner();
    if (!owner || owner.getEmail() !== me) continue;
    var m = NAME_RE.exec(f.getName());
    if (!m) continue;
    candidates.push({ id: f.getId(), name: f.getName(), date: m[1], file: f });
  }
  var today = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'yyyy-MM-dd');
  var doomed = selectForTrash_(candidates, today, cfg.keepDays);
  if (doomed.length > cfg.maxTrash) {
    throw new Error('Pruning wants to trash ' + doomed.length + ' copies, more than MAX_TRASH_PER_RUN (' +
        cfg.maxTrash + '). Nothing was trashed. Check the folder, then raise the limit if this is expected.');
  }
  doomed.forEach(function (c) {
    console.log((dryRun ? 'Would trash: ' : 'Trashed: ') + c.name);
    if (!dryRun) c.file.setTrashed(true);
  });
  console.log(candidates.length + ' nightly copies, ' + doomed.length + (dryRun ? ' would be' : '') + ' trashed.');
}

/**
 * Pure retention rule, kept free of Google services so it can be tested anywhere.
 * items: [{date: 'yyyy-MM-dd', ...}]; today: 'yyyy-MM-dd'. Returns the items to trash:
 * older than keepDays AND not the earliest copy of their month.
 */
function selectForTrash_(items, today, keepDays) {
  var cutoff = new Date(today + 'T00:00:00Z');
  cutoff.setUTCDate(cutoff.getUTCDate() - keepDays);
  var cut = cutoff.toISOString().slice(0, 10);
  var earliest = {};
  items.forEach(function (it) {
    var month = it.date.slice(0, 7);
    if (!earliest[month] || it.date < earliest[month].date) earliest[month] = it;
  });
  return items.filter(function (it) {
    return it.date < cut && earliest[it.date.slice(0, 7)] !== it;
  });
}
