# Quarterly sweep runbook

Do one quarter per session. A sweep is what keeps reports trustworthy enough to budget from.

1. **Back up**: `BACKUP <date> pre-<yyyy>-Q<n>-sweep - <sheet title>`.
2. **Scope** the quarter: row counts by `Categorized By` (Rules / Description Match /
   AI Suggest / blank), categories missing from the Categories tab, and blanks.
3. **P2P**: copy Venmo/PayPal/Cash App rows to a hold tab, pair each with its funding leg,
   and note who and what.
4. **Legacy names**: remap rows whose category no longer exists (`Unknown` in reports).
5. **Re-run** AutoCat on the cleared rows (see [autocat-playbook](autocat-playbook.md#safe-re-run-cleanup-mode)).
6. **Human review**: list unresolved rows over $100 and merchants with 3+ rows (rule
   candidates). The human picks the one-offs.
7. **Match card payments**: every checking-side payment should have a card-side twin with
   the same amount within ±3 days. Unmatched legs get `FLAG:identify`.
8. **Stamp** finalized rows with `SWEEP:<yyyy>-Q<n>` in Note (append).
9. **Commit** the rule changes to your private repo, so the sheet's AutoCat tab is a
   deploy target and not the source of truth.
