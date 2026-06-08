import os
import subprocess
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
STACK_SCRIPT = ROOT_DIR / "scripts" / "docker_stack.sh"


def _write_docker_stub(tmp_path: Path, fail_mode: str) -> Path:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    log_path = tmp_path / "docker.log"
    docker_stub = bin_dir / "docker"
    fuser_stub = bin_dir / "fuser"
    fuser_stub.write_text("#!/usr/bin/env bash\nexit 1\n", encoding="utf-8")
    fuser_stub.chmod(0o755)
    docker_stub.write_text(
        """#!/usr/bin/env bash
set -euo pipefail

printf '%s\\n' "$*" >> "$DOCKER_STUB_LOG"

if [[ "${1:-} ${2:-}" == "image inspect" ]]; then
  exit 0
fi

if [[ "${1:-}" == "version" ]]; then
  exit 0
fi

if [[ "${1:-}" == "compose" && "$*" == *" up -d --build --wait"* ]]; then
  count_file="$DOCKER_STUB_STATE/up_count"
  count=0
  if [[ -f "$count_file" ]]; then
    count="$(cat "$count_file")"
  fi
  count=$((count + 1))
  printf '%s' "$count" > "$count_file"

  if [[ "$DOCKER_STUB_FAIL_MODE" == "reset" && "$count" -eq 1 ]]; then
    echo 'dependency failed to start: error during connect: Get "http://%2Fvar%2Frun%2Fdocker.sock/v1.54/containers/abc/json": read unix @->/run/docker.sock: read: connection reset by peer' >&2
    exit 1
  fi

  if [[ "$DOCKER_STUB_FAIL_MODE" == "unhealthy" && "$count" -eq 1 ]]; then
    echo 'dependency failed to start: container unhealthy' >&2
    exit 1
  fi

  exit 0
fi

echo "unexpected docker invocation: $*" >&2
exit 2
""",
        encoding="utf-8",
    )
    docker_stub.chmod(0o755)
    return log_path


def _run_stack_up(tmp_path: Path, fail_mode: str) -> tuple[subprocess.CompletedProcess, list[str]]:
    log_path = _write_docker_stub(tmp_path, fail_mode)
    env = os.environ.copy()
    # Ensure /bin and /usr/bin are in PATH so that #!/usr/bin/env bash
    # shebangs resolve correctly even in environments with a non-standard PATH
    # (e.g. conda environments that use unexpanded ${PATH} references).
    current_path = env.get("PATH", "")
    for essential_dir in ("/usr/bin", "/bin"):
        if essential_dir not in current_path.split(":"):
            current_path = f"{essential_dir}:{current_path}"
    env.update(
        {
            "PATH": f"{tmp_path / 'bin'}:{current_path}",
            "DOCKER_STUB_FAIL_MODE": fail_mode,
            "DOCKER_STUB_LOG": str(log_path),
            "DOCKER_STUB_STATE": str(tmp_path / "state"),
            "PROJECT_NAME": "robot-cloud-script-test",
            "BASE_IMAGE_PYTHON": "python-base:test",
            "BASE_IMAGE_NODE": "node-base:test",
            "BASE_IMAGE_NGINX": "nginx-base:test",
        }
    )
    result = subprocess.run(
        [str(STACK_SCRIPT), "up"],
        cwd=ROOT_DIR,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    return result, log_path.read_text(encoding="utf-8").splitlines()


def test_up_retries_once_when_docker_socket_connection_resets(tmp_path):
    result, docker_calls = _run_stack_up(tmp_path, "reset")

    assert result.returncode == 0, result.stderr
    compose_up_calls = [
        call for call in docker_calls if call.endswith("up -d --build --wait")
    ]
    assert len(compose_up_calls) == 2
    assert "Docker daemon connection interrupted" in result.stderr


def test_up_does_not_retry_non_daemon_compose_failure(tmp_path):
    result, docker_calls = _run_stack_up(tmp_path, "unhealthy")

    assert result.returncode == 1
    compose_up_calls = [
        call for call in docker_calls if call.endswith("up -d --build --wait")
    ]
    assert len(compose_up_calls) == 1
