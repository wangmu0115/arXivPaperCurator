import logging
from typing import ContextManager, Optional

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from src.config import PostgresSettings

from .base import BaseDatabase

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


class PostgresDatabase(BaseDatabase):
    def __init__(self, config: PostgresSettings):
        self.config = config
        self.engine: Optional[Engine] = None
        self.session_factory: Optional[sessionmaker] = None

    def startup(self) -> None:
        logger.info("Attempting to connect to PostgresSQL: %s", self.config.db_url)
        self.engine = create_engine(
            self.config.db_url,
            echo=self.config.echo_sql,
            pool_size=self.config.pool_size,
            max_overflow=self.config.max_overflow,
            pool_pre_ping=True,  # Verify connections
        )
        self.session_factory = sessionmaker(self.engine, expire_on_commit=False)

        # Test connections
        assert self.engine is not None
        with self.engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            logger.info("PostgresSQL connection test successful")

    def teardown(self) -> None:
        if self.engine:
            self.engine.dispose()
            logger.info("PostgresSQL connections closed")

    def get_session(self) -> ContextManager[Session]:
        return super().get_session()
