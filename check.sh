#!/bin/sh
set -eu
cd "$(dirname "$0")"
export IYI_CACHE_DIR="${IYI_CACHE_DIR:-/tmp/slim-check-cache}"
RIS="${RIS:-ris}"
export IYI_PATH="$PWD:$("$RIS" env IYI_PATH)"
"$RIS" test
"$RIS" run -Dslim_string slim_test.ri
scratch=$(mktemp -d /tmp/slim-check.XXXXXX)
trap 'rm -rf "$scratch"' EXIT HUP INT TERM
# Seed every exercised specialization before consuming the artifact: a
# fixture-only producer never reaches the default-capacity constructor.
cat > "$scratch/producer.ri" <<'RI'
module producer
import slim_test
import streaming_test
RI
"$RIS" build "$scratch/producer.ri" --emit-iyimod "$scratch/modules" -o "$scratch/producer"
"$RIS" build slim_test.ri --use-iyimod "$scratch/modules" -o "$scratch/tape"
"$scratch/tape"
"$RIS" build streaming_test.ri --use-iyimod "$scratch/modules" -o "$scratch/api"
"$scratch/api"
if "$RIS" check test/refused/return.ri > "$scratch/return.log" 2>&1; then
  echo 'FAIL: tape result returned out of its scope'
  exit 1
fi
if ! rg -q 'cannot return a tape value out of' "$scratch/return.log"; then
  cat "$scratch/return.log"
  exit 1
fi
if "$RIS" check test/refused/outer.ri > "$scratch/outer.log" 2>&1; then
  echo 'FAIL: tape result assigned outside its scope'
  exit 1
fi
if ! rg -q 'is a variable of the code around this tape block' "$scratch/outer.log"; then
  cat "$scratch/outer.log"
  exit 1
fi
if "$RIS" run test/no_scope.ri > "$scratch/no-scope.log" 2>&1; then
  echo 'FAIL: default render allocated outside a tape block'
  exit 1
fi
if ! rg -q 'a tape value made outside a tape block' "$scratch/no-scope.log"; then
  cat "$scratch/no-scope.log"
  exit 1
fi
echo 'PASS: default tape, retained String, exported module and tape lifetime checks'
