import os
import uuid
from datetime import datetime
from typing import List, Optional

import pandas as pd

from app.models.record import AssetRecord
from app.models.summary import AssetSummary


class AssetStore:
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            data_dir = os.path.join(os.path.dirname(__file__), "data")
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        self.products_path = os.path.join(self.data_dir, "products.csv")
        self.operations_path = os.path.join(self.data_dir, "operations.csv")
        self._ensure_files()

    def _ensure_files(self):
        if not os.path.exists(self.products_path):
            pd.DataFrame(
                columns=[
                    "id", "asset_type", "name", "amount", "cost",
                    "value", "date", "category", "note",
                ]
            ).to_csv(self.products_path, index=False, encoding="utf-8-sig")
        if not os.path.exists(self.operations_path):
            pd.DataFrame(
                columns=[
                    "id", "product_id", "product_name", "asset_type",
                    "operation_type", "change_amount", "price", "new_amount",
                    "new_cost", "new_value", "date", "note",
                ]
            ).to_csv(self.operations_path, index=False, encoding="utf-8-sig")

    def _load(self) -> pd.DataFrame:
        df = pd.read_csv(
            self.products_path,
            dtype={
                "id": str,
                "asset_type": str,
                "name": str,
                "date": str,
                "category": str,
                "note": str,
            },
            encoding="utf-8-sig",
        )
        for col in ["amount", "cost", "value"]:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
        return df

    def _load_ops(self) -> pd.DataFrame:
        df = pd.read_csv(
            self.operations_path,
            dtype={
                "id": str,
                "product_id": str,
                "product_name": str,
                "asset_type": str,
                "operation_type": str,
                "date": str,
                "note": str,
            },
            encoding="utf-8-sig",
        )
        for col in ["change_amount", "price", "new_amount", "new_cost", "new_value"]:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
        return df

    def _save(self, df: pd.DataFrame):
        df.to_csv(self.products_path, index=False, encoding="utf-8-sig")

    def _save_ops(self, df: pd.DataFrame):
        df.to_csv(self.operations_path, index=False, encoding="utf-8-sig")

    def add_record(self, record: AssetRecord) -> str:
        df = self._load()
        record.id = record.id or uuid.uuid4().hex[:8]
        row = pd.DataFrame([{
            "id": record.id,
            "asset_type": record.asset_type,
            "name": record.name,
            "amount": record.amount,
            "cost": record.cost,
            "value": record.value,
            "date": record.date,
            "category": record.category,
            "note": record.note,
        }])
        df = pd.concat([df, row], ignore_index=True)
        self._save(df)
        return record.id

    def update_record(self, record: AssetRecord) -> str:
        df = self._load()
        if record.id in df["id"].values:
            idx = df.index[df["id"] == record.id].tolist()[0]
            df.at[idx, "asset_type"] = record.asset_type
            df.at[idx, "name"] = record.name
            df.at[idx, "amount"] = record.amount
            df.at[idx, "cost"] = record.cost
            df.at[idx, "value"] = record.value
            df.at[idx, "date"] = record.date
            df.at[idx, "category"] = record.category
            df.at[idx, "note"] = record.note
        else:
            row = pd.DataFrame([{
                "id": record.id or uuid.uuid4().hex[:8],
                "asset_type": record.asset_type,
                "name": record.name,
                "amount": record.amount,
                "cost": record.cost,
                "value": record.value,
                "date": record.date,
                "category": record.category,
                "note": record.note,
            }])
            df = pd.concat([df, row], ignore_index=True)
        self._save(df)
        return record.id

    def delete_record(self, record_id: str, new_name: str):
        df = self._load()
        if record_id in df["id"].values:
            idx = df.index[df["id"] == record_id].tolist()[0]
            old_name = df.at[idx, "name"]
            df.at[idx, "name"] = new_name
            self._save(df)
            # 同步更新 operations.csv 中的 product_name
            ops_df = self._load_ops()
            ops_df.loc[ops_df["product_id"] == record_id, "product_name"] = new_name
            self._save_ops(ops_df)

    def get_records(self, asset_type: Optional[str] = None, date_str: Optional[str] = None) -> List[AssetRecord]:
        df = self._load()
        if asset_type:
            df = df[df["asset_type"] == asset_type]
        if date_str:
            df = df[df["date"] == date_str]
        records = []
        for _, row in df.iterrows():
            records.append(AssetRecord(
                id=str(row["id"]),
                asset_type=str(row["asset_type"]),
                name=str(row["name"]),
                amount=float(row["amount"]),
                cost=float(row["cost"]),
                value=float(row["value"]),
                date=str(row["date"]),
                category=str(row.get("category", "")),
                note=str(row.get("note", "")),
            ))
        return records

    def add_operation(self, op: dict):
        df = self._load_ops()
        op["id"] = op.get("id") or uuid.uuid4().hex[:8]
        row = pd.DataFrame([op])
        df = pd.concat([df, row], ignore_index=True)
        self._save_ops(df)

    def get_operations(self, product_name: str) -> List[dict]:
        df = self._load_ops()
        df = df[df["product_name"] == product_name]
        df = df.sort_values(by="date", ascending=True)
        return df.to_dict(orient="records")

    def get_summary(self) -> AssetSummary:
        df = self._load()
        # 过滤已删除产品
        df = df[~df["name"].astype(str).str.endswith("_删除")]
        total = (df["amount"] * df["value"]).sum()
        by_type = {}
        for atype, group in df.groupby("asset_type"):
            by_type[str(atype)] = float((group["amount"] * group["value"]).sum())
        latest_date = self.get_latest_date()
        return AssetSummary(date=latest_date or datetime.now().strftime("%Y-%m-%d"), total=float(total), by_type=by_type)

    def get_latest_date(self) -> Optional[str]:
        df = self._load()
        if df.empty:
            return None
        return str(df["date"].max())

    def get_dates(self) -> List[str]:
        df = self._load()
        if df.empty:
            return []
        dates = sorted(df["date"].dropna().unique(), reverse=True)
        return [str(d) for d in dates]

    def get_product_by_name(self, name: str) -> Optional[AssetRecord]:
        df = self._load()
        row = df[df["name"] == name]
        if row.empty:
            return None
        r = row.iloc[0]
        return AssetRecord(
            id=str(r["id"]),
            asset_type=str(r["asset_type"]),
            name=str(r["name"]),
            amount=float(r["amount"]),
            cost=float(r["cost"]),
            value=float(r["value"]),
            date=str(r["date"]),
            category=str(r.get("category", "")),
            note=str(r.get("note", "")),
        )
