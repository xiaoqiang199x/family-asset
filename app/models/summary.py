from dataclasses import dataclass


@dataclass
class AssetSummary:
    date: str
    total: float
    by_type: dict
