from celery import Celery

from backend.app import create_app

flask_app = create_app()
celery_app = Celery("phenobot", broker=flask_app.config["REDIS_URL"], backend=flask_app.config["REDIS_URL"])
celery_app.conf.beat_schedule = {
    "mark-offline-robots": {
        "task": "phenobot.robot_offline_sweep",
        "schedule": 15.0,
    },
    "purge-old-realtime-events": {
        "task": "phenobot.purge_old_realtime_events",
        "schedule": 3600.0,
    },
    "purge-acknowledged-alerts": {
        "task": "phenobot.purge_acknowledged_alerts",
        "schedule": 86400.0,
    },
}


@celery_app.task(name="phenobot.analysis")
def run_analysis(task_id: str):
    flask_app.extensions["analysis_service"].run_analysis(task_id)


@celery_app.task(name="phenobot.robot_offline_sweep")
def robot_offline_sweep():
    count = flask_app.extensions["robot_service"].mark_stale_offline(flask_app.config["ROBOT_OFFLINE_TTL_SECONDS"])
    flask_app.extensions["realtime"].publish(
        "system.runtime",
        {"name": "robot_offline_sweep", "offline_count": count},
    )
    return count


@celery_app.task(name="phenobot.purge_old_realtime_events")
def purge_old_realtime_events():
    broker = flask_app.extensions["realtime"]
    event_ttl = flask_app.config["REALTIME_EVENT_TTL_HOURS"]
    deleted_events = broker.purge_old_events(ttl_hours=event_ttl)
    if deleted_events:
        flask_app.extensions["realtime"].publish(
            "system.runtime",
            {
                "name": "purge_old_realtime_events",
                "deleted_events": deleted_events,
            },
        )
    return {"deleted_events": deleted_events}


@celery_app.task(name="phenobot.purge_acknowledged_alerts")
def purge_acknowledged_alerts():
    broker = flask_app.extensions["realtime"]
    alert_ttl = flask_app.config["SYSTEM_ALERT_ACK_TTL_DAYS"]
    deleted_alerts = broker.purge_acknowledged_alerts(ttl_days=alert_ttl)
    if deleted_alerts:
        flask_app.extensions["realtime"].publish(
            "system.runtime",
            {
                "name": "purge_acknowledged_alerts",
                "deleted_alerts": deleted_alerts,
            },
        )
    return {"deleted_alerts": deleted_alerts}
