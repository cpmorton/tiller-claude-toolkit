#!/bin/bash
# Fail if staged (or, with --all, tracked) files look like financial data.
# Used by .githooks/pre-commit and CI. Patterns are deliberately blunt: a false positive
# costs a rename; a false negative publishes a bank export.
set -euo pipefail
mode=${1:---staged}
if [[ $mode == --all ]]; then files=$(git ls-files); else files=$(git diff --cached --name-only --diff-filter=ACM); fi
[[ -z $files ]] && exit 0

bad=0
while IFS= read -r f; do
  case $f in
    defaults/*.csv|tests/fixtures/*.csv|rules/*.csv) ;;                 # curated, reviewed
    *.csv|*.xlsx|*.xls|*.ofx|*.qfx|*.qbo|data/*|exports/*)
      echo "blocked: $f (financial export?)"; bad=1 ;;
  esac
  [[ -f $f ]] || continue
  # Tiller transaction/account IDs and long digit runs (account/card numbers)
  if grep -nE '\b[A-Za-z0-9]{37}\b|\b[0-9a-f]{24}\b|\b[0-9]{12,19}\b' "$f" >/dev/null 2>&1; then
    case $f in *.lock|*.svg) ;; *)
      echo "blocked: $f contains an ID-like or account-number-like token:"
      grep -nE '\b[A-Za-z0-9]{37}\b|\b[0-9a-f]{24}\b|\b[0-9]{12,19}\b' "$f" | head -3; bad=1 ;;
    esac
  fi
done <<< "$files"
exit $bad
