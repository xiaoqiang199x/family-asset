from dataclasses import dataclass, field

from app.models.types import AssetType


@dataclass
class AssetRecord:
    id: str
    asset_type: str
    name: str
    amount: float
    cost: float
    value: float
    date: str
    category: str = ""
    note: str = ""

    @property
    def total_value(self) -> float:
        return self.amount * self.value

    @property
    def profit(self) -> float:
        return (self.value - self.cost) * self.amount

    @property
    def profit_pct(self) -> float:
        if self.cost == 0:
            return 0.0
        return (self.value - self.cost) / self.cost * 100

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "asset_type": self.asset_type,
            "name": self.name,
            "amount": self.amount,
            "cost": self.cost,
            "value": self.value,
            "date": self.date,
            "category": self.category,
            "note": self.note,
            "total_value": self.total_value,
            "profit": self.profit,
            "profit_pct": self.profit_pct,
        }
