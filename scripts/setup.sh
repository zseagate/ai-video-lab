#!/usr/bin/env bash
# Local environment setup for ai-video-lab (macOS / Linux).
#
# Usage:
#   bash scripts/setup.sh          # core only
#   bash scripts/setup.sh --llm    # also install llama-cpp-python (CPU)
set -euo pipefail

WITH_LLM=0
for arg in "$@"; do
  case "$arg" in
    --llm) WITH_LLM=1 ;;
    *) echo "unknown arg: $arg"; exit 2 ;;
  esac
done

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="${PYTHON:-python3}"

echo "== ai-video-lab setup =="
echo "root: $ROOT"

echo
echo "[1/3] Python"
"$PYTHON" --version

echo
echo "[2/3] Core dependencies"
"$PYTHON" -m pip install --upgrade pip
"$PYTHON" -m pip install -r "$ROOT/requirements.txt"

echo
if [ "$WITH_LLM" -eq 1 ]; then
  echo "[3/3] Optional llama-cpp-python (CPU)"
  "$PYTHON" -m pip install --upgrade llama-cpp-python \
    --prefer-binary \
    --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu \
    --only-binary llama-cpp-python
else
  echo "[3/3] Skipping LLM (pass --llm to install llama-cpp-python)"
fi

echo
echo "== doctor =="
"$PYTHON" "$ROOT/lab/run.py" doctor

echo
echo "Done. Start the console with:"
echo "  $PYTHON $ROOT/lab/run.py serve --port 8799"
