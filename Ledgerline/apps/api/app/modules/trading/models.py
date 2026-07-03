from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import TradingBase


class Workspace(TradingBase):
    __tablename__ = "workspaces"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, index=True)

    portfolios: Mapped[list["Portfolio"]] = relationship(back_populates="workspace")


class Portfolio(TradingBase):
    __tablename__ = "portfolios"

    id: Mapped[int] = mapped_column(primary_key=True)
    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id"), index=True)
    name: Mapped[str] = mapped_column(String(80), index=True)

    workspace: Mapped[Workspace] = relationship(back_populates="portfolios")

