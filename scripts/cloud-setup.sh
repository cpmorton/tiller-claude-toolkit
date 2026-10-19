#!/bin/bash
# Cloud environment setup script for budget automation.
# Paste into: Project settings > Cloud environment > Add cloud environment > Setup script.
# Runs as root on Ubuntu 24.04 before Claude starts; the resulting disk is cached ~7 days,
# so it only re-runs when this script changes. Must finish in ~5 min and exit 0,
# or new sessions fail to start -- hence `|| true` on everything non-critical.
set -u

# Python libs for the Tiller analysis scripts. pip skips anything already satisfied.
#   pandas/pyarrow: the analysis itself; openpyxl: .xlsx exports (Amazon order history, statements)
#   rapidfuzz: fuzzy merchant matching for AutoCat rule candidates and Amazon/receipt reconciliation
python3 -m pip install --quiet --disable-pip-version-check --root-user-action=ignore \
  'pandas>=2.2' 'pyarrow>=17' 'openpyxl>=3.1' 'rapidfuzz>=3.9' || true

# Shell-side CSV tooling: miller (mlr) is awk/sed/jq for CSV -- handy for quick slicing of exports.
if ! command -v mlr >/dev/null || ! command -v jq >/dev/null; then
  (apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq miller jq) || true
fi

# Scratch area for raw financial exports, outside any git checkout so it can never be committed.
install -d -m 700 /root/budget-data

exit 0
