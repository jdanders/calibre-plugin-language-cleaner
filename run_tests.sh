#!/usr/bin/env sh
set -eu

cd "$(dirname "$0")"

status=0
total=0
passed=0
failed=0
for test_file in test*.py; do
    test_module=${test_file%.py}
    total=$((total + 1))
    printf '\n== %s ==\n' "$test_module"
    if ! python3 -m unittest "$test_module"; then
        status=1
        failed=$((failed + 1))
    else
        passed=$((passed + 1))
    fi
done

printf '\nOverall: %s/%s test modules passed; %s failed.\n' "$passed" "$total" "$failed"
exit "$status"
