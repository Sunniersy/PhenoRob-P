from pathlib import Path


def test_default_compose_stack_includes_simulator_service_and_demo_env():
    content = Path("deploy/docker-compose.yml").read_text()

    assert "\n  simulator:\n" in content
    assert "./demo.env" in content


def test_simulator_image_exports_repo_root_on_pythonpath():
    content = Path("deploy/simulator.Dockerfile").read_text()

    assert "ENV PYTHONPATH=/app" in content


def test_compose_host_ports_are_env_overridable():
    content = Path("deploy/docker-compose.yml").read_text()

    assert '${POSTGRES_HOST_PORT:-5432}:5432' in content
    assert '${REDIS_HOST_PORT:-6379}:6379' in content
    assert '${MQTT_HOST_PORT:-1883}:1883' in content
    assert '${MINIO_API_HOST_PORT:-9000}:9000' in content
    assert '${MINIO_CONSOLE_HOST_PORT:-9001}:9001' in content
    assert '${APP_HTTP_PORT:-80}:80' in content


def test_portable_docker_entrypoint_script_exists():
    content = Path("scripts/docker_stack.sh").read_text()

    assert content.startswith("#!/usr/bin/env bash")
    assert "docker compose" in content
    assert 'case "${command}" in' in content
    assert "demo-reset-admin" in content
    assert "python -m flask --app backend.run demo-reset-admin" in content
    assert "pull_base_images" in content
    assert "docker pull" in content
    assert "docker tag" in content
    assert "BASE_IMAGE_PYTHON" in content
    assert "BASE_IMAGE_PYTHON_SOURCE" in content
    assert "pull-base-images" in content


def test_backend_and_simulator_images_pin_and_share_python_base():
    backend = Path("deploy/backend.Dockerfile").read_text()
    simulator = Path("deploy/simulator.Dockerfile").read_text()

    assert "ARG BASE_IMAGE_PYTHON=" in backend
    assert "FROM ${BASE_IMAGE_PYTHON}" in backend
    assert "ARG BASE_IMAGE_PYTHON=" in simulator
    assert "FROM ${BASE_IMAGE_PYTHON}" in simulator


def test_frontend_image_pin_variables_are_declared():
    frontend = Path("deploy/frontend.Dockerfile").read_text()

    assert "ARG BASE_IMAGE_NODE=" in frontend
    assert "FROM ${BASE_IMAGE_NODE} AS build" in frontend
    assert "ARG BASE_IMAGE_NGINX=" in frontend
    assert "FROM ${BASE_IMAGE_NGINX}" in frontend


def test_production_nginx_enforces_security_headers_and_auth_rate_limits():
    content = Path("deploy/nginx.conf").read_text()

    assert 'limit_req_zone $binary_remote_addr zone=auth_limit:10m rate=10r/m;' in content
    assert "client_max_body_size 32m;" in content
    assert 'add_header X-Frame-Options "DENY" always;' in content
    assert 'add_header X-Content-Type-Options "nosniff" always;' in content
    assert 'add_header Referrer-Policy "strict-origin-when-cross-origin" always;' in content
    assert "Content-Security-Policy" in content
    assert "proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;" in content
    assert "proxy_set_header X-Forwarded-Proto $scheme;" in content
    assert "limit_req zone=auth_limit burst=5 nodelay;" in content


def test_demo_and_example_envs_define_bootstrap_token_for_initial_admin_hardening():
    demo_env = Path("deploy/demo.env").read_text()
    example_env = Path(".env.example").read_text()

    assert "BOOTSTRAP_TOKEN=" in demo_env
    assert "BOOTSTRAP_TOKEN=" in example_env


def test_stack_env_override_is_opt_in_for_demo_commands():
    compose_content = Path("deploy/docker-compose.yml").read_text()
    script_content = Path("scripts/docker_stack.sh").read_text()

    assert "${STACK_ENV_FILE:-/dev/null}" in compose_content
    assert 'STACK_ENV_FILE="${STACK_ENV_FILE:-/dev/null}"' in script_content
    assert "STACK_ENV_FILE          Optional env file path for overriding deploy/demo.env" in script_content


def test_backend_unit_test_command_does_not_start_port_bound_dependencies():
    script_content = Path("scripts/docker_stack.sh").read_text()

    assert "run_compose run --rm --no-deps --build backend python -m pytest -q tests" in script_content


def test_stack_clean_command_removes_generated_artifacts_without_touching_local_envs():
    script_content = Path("scripts/docker_stack.sh").read_text()
    makefile_content = Path("Makefile").read_text()

    assert "clean_generated()" in script_content
    assert "frontend/dist" in script_content
    assert ".pytest_cache" in script_content
    assert "-name __pycache__" in script_content
    assert "-path \"$ROOT_DIR/.venv\" -prune" in script_content
    assert "-path \"$ROOT_DIR/.venv_test\" -prune" in script_content
    assert "clean)" in script_content
    assert "docker-clean" in makefile_content


def test_asset_service_is_split_into_upload_and_query_collaborators():
    asset_service = Path("backend/app/services/asset_service.py").read_text()

    assert Path("backend/app/services/asset_upload_service.py").exists()
    assert Path("backend/app/services/asset_query_service.py").exists()
    assert "AssetUploadService" in asset_service
    assert "AssetQueryService" in asset_service


def test_ci_workflow_runs_backend_frontend_and_compose_quality_gates():
    workflow = Path(".github/workflows/ci.yml")

    assert workflow.exists()
    content = workflow.read_text()
    assert "python -m pytest -q tests" in content
    assert "npm run lint" in content
    assert "npm test" in content
    assert "npm run build" in content
    assert "docker compose -f deploy/docker-compose.yml config -q" in content
