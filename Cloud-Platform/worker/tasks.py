from backend.app import create_app


def create_worker_task_queue():
    app = create_app()
    return app.extensions["task_queue"]

