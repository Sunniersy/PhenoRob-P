from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool


class DatabaseManager:
    def __init__(self, database_url: str, pool_size: int = 20, max_overflow: int = 10, pool_recycle: int = 3600):
        connect_args = {}
        engine_kwargs = {"future": True}

        if database_url == "sqlite://":
            connect_args["check_same_thread"] = False
            engine_kwargs["poolclass"] = StaticPool
        elif database_url.startswith("sqlite"):
            connect_args["check_same_thread"] = False
        else:
            # PostgreSQL connection pool configuration
            engine_kwargs.update({
                "pool_size": pool_size,
                "max_overflow": max_overflow,
                "pool_recycle": pool_recycle,
                "pool_pre_ping": True,  # Verify connections before use
                "pool_timeout": 30,  # Wait timeout for connection from pool
            })

        self.engine = create_engine(database_url, connect_args=connect_args, **engine_kwargs)
        self._sessionmaker = sessionmaker(bind=self.engine, expire_on_commit=False, class_=Session)

    def create_all(self, metadata) -> None:
        metadata.create_all(self.engine)

    def session(self) -> Session:
        return self._sessionmaker()

    @contextmanager
    def session_scope(self):
        """Context manager that provides a session and ensures cleanup.

        Usage::

            with self.db.session_scope() as session:
                # use session
                session.commit()

        The session is always closed on exit.  Callers are responsible for
        calling ``session.commit()`` explicitly when they have writes.
        """
        session = self._sessionmaker()
        try:
            yield session
        finally:
            session.close()

    def close_session(self, session: Session) -> None:
        session.close()

    def ping(self) -> None:
        with self.engine.connect() as connection:
            connection.execute(text("SELECT 1"))
