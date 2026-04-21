from enum import Enum


class AssetType(str, Enum):
    BANK = "银行理财"
    STOCK = "股票"
    FUND = "基金"
    GOLD = "黄金"
