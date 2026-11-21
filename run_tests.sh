#!/usr/bin/env sh
set -eu

cd "$(dirname "$0")"

status=0
for test_file in test*.py; do
    test_module=${test_file%.py}
    printf '\n== %s ==\n' "$test_module"
    if ! python3 -m unittest "$test_module"; then
        status=1
    fi
done

exit "$status"
