from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Import models so Alembic autogenerate and test metadata see the full schema.
from app.models.market_data import (  # noqa: E402,F401
    DataIngestionRun,
    DailyBar,
    IndexBar,
    Instrument,
    IntradayBar,
    TdxDailySnapshot,
    Theme,
    ThemeConstituent,
    ThemeSnapshot,
    TradingCalendar,
)
from app.models import review as review_models  # noqa: E402,F401
