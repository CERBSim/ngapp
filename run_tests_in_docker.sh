#!/usr/bin/env bash
# Usage: ./run_tests_in_docker.sh [--update-baselines] [-- pytest-args...]
set -e
cd "$(dirname "$0")"

BASE_IMAGE=ngapp-base
IMAGE=ngapp-tests
EXTRA=()
PYTEST_ARGS=()

while [[ $# -gt 0 ]]; do
    case "$1" in
        --update-baselines) EXTRA+=(-e UPDATE_BASELINES=1); shift ;;
        --) shift; PYTEST_ARGS+=("$@"); break ;;
        *) PYTEST_ARGS+=("$1"); shift ;;
    esac
done

echo "==> Building base image..."
docker build -f tests/Dockerfile.base -t "$BASE_IMAGE" .

echo "==> Building test image..."
docker build -f tests/Dockerfile --build-arg BASE_IMAGE="$BASE_IMAGE" -t "$IMAGE" .

echo "==> Running tests..."
docker run --rm \
    -v "$(pwd)/tests/output:/app/tests/output" \
    -v "$(pwd)/tests/baselines:/app/tests/baselines" \
    "${EXTRA[@]}" \
    "$IMAGE" \
    ${PYTEST_ARGS:+pytest -vv -s "${PYTEST_ARGS[@]}"}

echo "==> Done."
if [[ " ${EXTRA[*]} " == *"UPDATE_BASELINES=1"* ]]; then
    echo "==> Baselines updated in tests/baselines/"
fi