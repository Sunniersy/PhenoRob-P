from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select

from backend.app.models import RealtimeEvent, SystemAlert


class RealtimeBroker:
    def __init__(self, db, enabled: bool = True):
        self.db = db
        self.enabled = enabled

    def publish(self, event_type: str, payload: dict) -> None:
        session = self.db.session()
        try:
            session.add(RealtimeEvent(event=event_type, payload=payload))
            if event_type == "system.alert":
                session.add(
                    SystemAlert(
                        source=payload.get("source", "system"),
                        level=payload.get("level", "ERROR"),
                        message=payload.get("message", payload.get("error", "system alert")),
                        payload=payload,
                    )
                )
            session.commit()
        finally:
            session.close()

    def fetch_after(self, last_event_id: int, limit: int = 100) -> list[dict]:
        session = self.db.session()
        try:
            items = session.scalars(
                select(RealtimeEvent)
                .where(RealtimeEvent.id > last_event_id)
                .order_by(RealtimeEvent.id.asc())
                .limit(limit)
            ).all()
            return [
                {
                    "id": item.id,
                    "event": item.event,
                    "payload": item.payload,
                    "timestamp": item.timestamp.isoformat(),
                }
                for item in items
            ]
        finally:
            session.close()

    def purge_old_events(self, ttl_hours: int = 24) -> int:
        """Delete realtime_events older than ttl_hours. Returns number of deleted rows."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=ttl_hours)
        session = self.db.session()
        try:
            result = session.execute(
                delete(RealtimeEvent).where(RealtimeEvent.timestamp < cutoff)
            )
            session.commit()
            return result.rowcount
        finally:
            session.close()

    def purge_acknowledged_alerts(self, ttl_days: int = 7) -> int:
        """Delete acknowledged system_alerts older than ttl_days. Returns number of deleted rows."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=ttl_days)
        session = self.db.session()
        try:
            result = session.execute(
                delete(SystemAlert).where(
                    SystemAlert.is_acknowledged == True,  # noqa: E712
                    SystemAlert.created_at < cutoff,
                )
            )
            session.commit()
            return result.rowcount
        finally:
            session.close()

    def healthcheck(self) -> dict:
        session = self.db.session()
        try:
            session.execute(select(RealtimeEvent.id).limit(1))
            return {"ok": True}
        finally:
            session.close()
