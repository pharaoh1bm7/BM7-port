#!/bin/sh
# Cross-language (Python <-> Go) wire-format interoperability check.
set -e
cd "$(dirname "$0")/../.."
T=$(mktemp -d)
python3 tests/interop/gen_vectors.py "$T/py.json"
(cd reference/go && BM7_PY_VECTORS="$T/py.json" BM7_GO_VECTORS="$T/go.json" go test -count=1 -v ./...)
python3 tests/interop/verify_go_vectors.py "$T/go.json"
echo "INTEROP PASS"
