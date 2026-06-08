#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT_NAME="${PROJECT_NAME:-robot-cloud-demo}"
STACK_ENV_FILE="${STACK_ENV_FILE:-/dev/null}"
BASE_IMAGE_PYTHON="${BASE_IMAGE_PYTHON:-robot-cloud-python-base:3.11-slim}"
BASE_IMAGE_NODE="${BASE_IMAGE_NODE:-robot-cloud-node-base:20-alpine}"
BASE_IMAGE_NGINX="${BASE_IMAGE_NGINX:-robot-cloud-nginx-base:1.27-alpine}"
BASE_IMAGE_PYTHON_SOURCE="${BASE_IMAGE_PYTHON_SOURCE:-python:3.11-slim@sha256:f987dd6c8a123021ac334bf0dabc7ef5a1d329cc318678d01c9d7b5ce52a8b57}"
BASE_IMAGE_NODE_SOURCE="${BASE_IMAGE_NODE_SOURCE:-node:20-alpine@sha256:fb4cd12c85ee03686f6af5362a0b0d56d50c58a04632e6c0fb8363f609372293}"
BASE_IMAGE_NGINX_SOURCE="${BASE_IMAGE_NGINX_SOURCE:-nginx:1.27-alpine@sha256:65645c7bb6a0661892a8b03b89d0743208a18dd2f3f17a54ef4b76fb8e2f2a10}"
BASE_IMAGE_PULL_RETRIES="${BASE_IMAGE_PULL_RETRIES:-3}"
BASE_IMAGE_PULL_RETRY_DELAY_SECONDS="${BASE_IMAGE_PULL_RETRY_DELAY_SECONDS:-3}"
HOST_PACKAGE_LOCK_WAIT_ATTEMPTS="${HOST_PACKAGE_LOCK_WAIT_ATTEMPTS:-90}"
HOST_PACKAGE_LOCK_WAIT_DELAY_SECONDS="${HOST_PACKAGE_LOCK_WAIT_DELAY_SECONDS:-2}"
DOCKER_DAEMON_WAIT_ATTEMPTS="${DOCKER_DAEMON_WAIT_ATTEMPTS:-30}"
DOCKER_DAEMON_WAIT_DELAY_SECONDS="${DOCKER_DAEMON_WAIT_DELAY_SECONDS:-2}"
COMPOSE_DAEMON_RETRIES="${COMPOSE_DAEMON_RETRIES:-1}"
export STACK_ENV_FILE BASE_IMAGE_PYTHON
COMPOSE=(docker compose -p "$PROJECT_NAME" -f "$ROOT_DIR/deploy/docker-compose.yml")
command="${1:-help}"

run_compose() {
  "${COMPOSE[@]}" "$@"
}

host_package_lock_active() {
  command -v fuser >/dev/null 2>&1 || return 1

  local lock
  for lock in \
    /var/lib/dpkg/lock-frontend \
    /var/lib/dpkg/lock \
    /var/cache/apt/archives/lock \
    /var/lib/apt/lists/lock; do
    if [ -e "$lock" ] && fuser "$lock" >/dev/null 2>&1; then
      return 0
    fi
  done

  return 1
}

wait_for_host_package_manager() {
  local attempt=1

  while host_package_lock_active; do
    if (( attempt == 1 )); then
      printf 'Host package manager lock is active; waiting before touching Docker...\n' >&2
    fi

    if (( attempt >= HOST_PACKAGE_LOCK_WAIT_ATTEMPTS )); then
      printf 'Timed out waiting for host package manager locks to clear.\n' >&2
      return 1
    fi

    sleep "$HOST_PACKAGE_LOCK_WAIT_DELAY_SECONDS"
    attempt=$((attempt + 1))
  done
}

wait_for_docker_daemon() {
  local attempt=1

  while ! docker version >/dev/null 2>&1; do
    if (( attempt >= DOCKER_DAEMON_WAIT_ATTEMPTS )); then
      printf 'Timed out waiting for Docker daemon to become ready.\n' >&2
      return 1
    fi

    sleep "$DOCKER_DAEMON_WAIT_DELAY_SECONDS"
    attempt=$((attempt + 1))
  done
}

compose_failure_is_daemon_disconnect() {
  local output_file="$1"
  grep -Eiq \
    'connection reset by peer|error during connect|Cannot connect to the Docker daemon|Is the docker daemon running|request canceled while waiting for connection|unexpected EOF|context canceled' \
    "$output_file"
}

run_compose_with_daemon_retry() {
  local attempt=0
  local output_file
  local status

  while true; do
    output_file="$(mktemp)"
    set +e
    run_compose "$@" 2> >(tee "$output_file" >&2)
    status=$?
    set -e

    if (( status == 0 )); then
      rm -f "$output_file"
      return 0
    fi

    if (( attempt >= COMPOSE_DAEMON_RETRIES )) || ! compose_failure_is_daemon_disconnect "$output_file"; then
      rm -f "$output_file"
      return "$status"
    fi

    rm -f "$output_file"
    attempt=$((attempt + 1))
    printf 'Docker daemon connection interrupted during compose. Waiting for Docker and retrying (%s/%s)...\n' \
      "$attempt" "$COMPOSE_DAEMON_RETRIES" >&2
    wait_for_docker_daemon
  done
}

pull_with_retry() {
  local image="$1"
  local attempt=1

  while (( attempt <= BASE_IMAGE_PULL_RETRIES )); do
    if docker pull "$image"; then
      return 0
    fi

    if (( attempt == BASE_IMAGE_PULL_RETRIES )); then
      printf 'Failed to pull %s after %s attempts\n' "$image" "$BASE_IMAGE_PULL_RETRIES" >&2
      return 1
    fi

    printf 'Pull failed for %s (attempt %s/%s). Retrying in %ss...\n' \
      "$image" "$attempt" "$BASE_IMAGE_PULL_RETRIES" "$BASE_IMAGE_PULL_RETRY_DELAY_SECONDS" >&2
    sleep "$BASE_IMAGE_PULL_RETRY_DELAY_SECONDS"
    attempt=$((attempt + 1))
  done
}

prepare_base_image() {
  local source_image="$1"
  local target_image="$2"

  if docker image inspect "$target_image" >/dev/null 2>&1; then
    printf 'Base image already present: %s\n' "$target_image"
    return 0
  fi

  if ! docker image inspect "$source_image" >/dev/null 2>&1; then
    pull_with_retry "$source_image"
  fi

  docker tag "$source_image" "$target_image"
  printf 'Prepared base image alias: %s <- %s\n' "$target_image" "$source_image"
}

pull_base_images() {
  prepare_base_image "$BASE_IMAGE_PYTHON_SOURCE" "$BASE_IMAGE_PYTHON"
  prepare_base_image "$BASE_IMAGE_NODE_SOURCE" "$BASE_IMAGE_NODE"
  prepare_base_image "$BASE_IMAGE_NGINX_SOURCE" "$BASE_IMAGE_NGINX"
}

run_frontend_container() {
  docker run --rm -v "$ROOT_DIR/frontend:/app" -w /app "$BASE_IMAGE_NODE" sh -lc "$1"
}

clean_generated() {
  find "$ROOT_DIR" \
    -path "$ROOT_DIR/.venv" -prune -o \
    -path "$ROOT_DIR/.venv_test" -prune -o \
    -path "$ROOT_DIR/frontend/node_modules" -prune -o \
    -type d -name __pycache__ -prune -exec rm -rf {} +

  rm -rf "$ROOT_DIR/.pytest_cache"
  if [ -d "$ROOT_DIR/frontend/dist" ] && ! rm -rf "$ROOT_DIR/frontend/dist" 2>/dev/null; then
    run_frontend_container "rm -rf dist"
  fi
}

case "${command}" in
  pull-base-images)
    wait_for_host_package_manager
    wait_for_docker_daemon
    pull_base_images
    ;;
  up)
    wait_for_host_package_manager
    wait_for_docker_daemon
    pull_base_images
    run_compose_with_daemon_retry up -d --build --wait
    ;;
  down)
    run_compose down --remove-orphans
    ;;
  reset)
    run_compose down -v --remove-orphans
    ;;
  ps)
    run_compose ps
    ;;
  logs)
    shift || true
    run_compose logs -f --tail=200 "$@"
    ;;
  restart)
    shift || true
    run_compose restart "$@"
    ;;
  rebuild)
    wait_for_host_package_manager
    wait_for_docker_daemon
    pull_base_images
    run_compose build --no-cache
    ;;
  smoke)
    run_compose exec -T backend env API_BASE_URL=http://nginx python scripts/acceptance_smoke.py
    ;;
  demo-reset-admin)
    run_compose exec -T backend python -m flask --app backend.run demo-reset-admin
    ;;
  cold-smoke)
    wait_for_host_package_manager
    wait_for_docker_daemon
    pull_base_images
    run_compose down -v --remove-orphans
    run_compose_with_daemon_retry up -d --build --wait
    run_compose exec -T backend env API_BASE_URL=http://nginx python scripts/acceptance_smoke.py
    ;;
  test-backend)
    wait_for_host_package_manager
    wait_for_docker_daemon
    pull_base_images
    run_compose run --rm --no-deps --build backend python -m pytest -q tests
    ;;
  test-frontend)
    wait_for_host_package_manager
    wait_for_docker_daemon
    pull_base_images
    run_frontend_container "npm install >/tmp/npm-install.log && npm test"
    ;;
  frontend-build)
    wait_for_host_package_manager
    wait_for_docker_daemon
    pull_base_images
    run_frontend_container "npm install >/tmp/npm-install.log && npm run build"
    ;;
  clean)
    clean_generated
    ;;
  test)
    wait_for_host_package_manager
    wait_for_docker_daemon
    pull_base_images
    run_compose run --rm --no-deps --build backend python -m pytest -q tests
    run_frontend_container "npm install >/tmp/npm-install.log && npm test"
    ;;
  check)
    run_compose config -q
    ;;
  help|--help|-h)
    cat <<'EOF'
Usage: ./scripts/docker_stack.sh <command>

Commands:
  pull-base-images Pull pinned base images with retry before building
  up             Build and start the full demo stack, waiting for healthchecks
  down           Stop the stack and remove containers
  reset          Stop the stack and remove containers plus volumes
  ps             Show container status
  logs [svc...]  Tail logs for the full stack or selected services
  restart [svc]  Restart the full stack or selected services
  rebuild        Rebuild images without cache
  smoke          Run simulator-driven acceptance smoke against the running stack
  demo-reset-admin
                 Reset or create the demo admin from deploy/demo.env or STACK_ENV_FILE
  cold-smoke     Recreate volumes, start the stack, then run smoke
  test-backend   Run backend tests in the backend image
  test-frontend  Run frontend tests in a Node 20 container
  frontend-build Build the frontend in a Node 20 container
  clean          Remove generated Python caches and frontend build output
  test           Run backend and frontend tests
  check          Validate the Compose file

Environment:
  PROJECT_NAME             Compose project name, default: robot-cloud-demo
  STACK_ENV_FILE          Optional env file path for overriding deploy/demo.env
  BASE_IMAGE_PYTHON        Pinned Python base image used by backend/worker/simulator
  BASE_IMAGE_NODE          Pinned Node base image used by frontend build and test helpers
  BASE_IMAGE_NGINX         Pinned Nginx base image used by frontend runtime image
  BASE_IMAGE_PYTHON_SOURCE Upstream Python image pinned by digest before local tagging
  BASE_IMAGE_NODE_SOURCE   Upstream Node image pinned by digest before local tagging
  BASE_IMAGE_NGINX_SOURCE  Upstream Nginx image pinned by digest before local tagging
  BASE_IMAGE_PULL_RETRIES  Retry count for base image pulls, default: 3
  BASE_IMAGE_PULL_RETRY_DELAY_SECONDS
                           Delay between base image pull retries, default: 3
  HOST_PACKAGE_LOCK_WAIT_ATTEMPTS
                           Wait attempts when apt/dpkg locks are active, default: 90
  HOST_PACKAGE_LOCK_WAIT_DELAY_SECONDS
                           Delay between package-lock checks, default: 2
  DOCKER_DAEMON_WAIT_ATTEMPTS
                           Wait attempts for Docker daemon readiness, default: 30
  DOCKER_DAEMON_WAIT_DELAY_SECONDS
                           Delay between Docker readiness checks, default: 2
  COMPOSE_DAEMON_RETRIES   Retries for Docker daemon disconnects during compose up, default: 1
  APP_HTTP_PORT            Host port for nginx, default: 80
  POSTGRES_HOST_PORT       Host port for PostgreSQL, default: 5432
  REDIS_HOST_PORT          Host port for Redis, default: 6379
  MQTT_HOST_PORT           Host port for Mosquitto, default: 1883
  MINIO_API_HOST_PORT      Host port for MinIO API, default: 9000
  MINIO_CONSOLE_HOST_PORT  Host port for MinIO Console, default: 9001
EOF
    ;;
  *)
    printf 'Unknown command: %s\n\n' "${command}" >&2
    exec "$0" help
    ;;
esac
