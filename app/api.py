import os
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from app.models.record import AssetRecord
from app.models.types import AssetType
from app.storage import AssetStore

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
store = AssetStore()


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html", {})


@router.get("/api/types")
async def get_types():
    return [t.value for t in AssetType]


@router.get("/api/dates")
async def get_dates():
    return store.get_dates()


@router.get("/api/records")
async def get_records(asset_type: Optional[str] = None, date: Optional[str] = None):
    records = store.get_records(asset_type=asset_type, date_str=date)
    return [r.to_dict() for r in records]


@router.post("/api/records")
async def add_record(
    asset_type: str = Form(...),
    name: str = Form(...),
    amount: float = Form(...),
    cost: float = Form(...),
    value: float = Form(...),
    date: str = Form(...),
    category: str = Form(""),
    note: str = Form(""),
):
    record = AssetRecord(
        id="",
        asset_type=asset_type,
        name=name,
        amount=amount,
        cost=cost,
        value=value,
        date=date,
        category=category,
        note=note,
    )
    record_id = store.add_record(record)
    return {"id": record_id, "message": "added"}


@router.post("/api/records/{record_id}")
async def update_record(
    record_id: str,
    asset_type: str = Form(...),
    name: str = Form(...),
    amount: float = Form(...),
    cost: float = Form(...),
    value: float = Form(...),
    date: str = Form(...),
    category: str = Form(""),
    note: str = Form(""),
):
    record = AssetRecord(
        id=record_id,
        asset_type=asset_type,
        name=name,
        amount=amount,
        cost=cost,
        value=value,
        date=date,
        category=category,
        note=note,
    )
    store.update_record(record)
    return {"id": record_id, "message": "updated"}


@router.delete("/api/records/{record_id}")
async def delete_record(record_id: str):
    df = store._load()
    row = df[df["id"] == record_id]
    if row.empty:
        return JSONResponse(status_code=404, content={"message": "not found"})
    old_name = str(row.iloc[0]["name"])
    today = datetime.now().strftime("%Y%m%d")
    new_name = f"{old_name}_{today}_删除"
    store.delete_record(record_id, new_name)
    return {"id": record_id, "new_name": new_name, "message": "deleted"}


@router.post("/api/operations")
async def add_operation(
    product_id: str = Form(...),
    product_name: str = Form(...),
    asset_type: str = Form(...),
    operation_type: str = Form(...),
    change_amount: float = Form(0.0),
    price: float = Form(0.0),
    new_amount: float = Form(...),
    new_cost: float = Form(...),
    new_value: float = Form(...),
    date: str = Form(...),
    note: str = Form(""),
):
    op = {
        "id": "",
        "product_id": product_id,
        "product_name": product_name,
        "asset_type": asset_type,
        "operation_type": operation_type,
        "change_amount": change_amount,
        "price": price,
        "new_amount": new_amount,
        "new_cost": new_cost,
        "new_value": new_value,
        "date": date,
        "note": note,
    }
    store.add_operation(op)
    return {"message": "operation added"}


@router.get("/api/summary")
async def get_summary():
    summary = store.get_summary()
    return {
        "date": summary.date,
        "total": summary.total,
        "by_type": summary.by_type,
    }


@router.get("/api/latest_summary")
async def get_latest_summary():
    summary = store.get_summary()
    records = store.get_records()
    details = {}
    for r in records:
        if r.name.endswith("_删除"):
            continue
        atype = r.asset_type
        if atype not in details:
            details[atype] = {"total": 0.0, "records": []}
        details[atype]["total"] += r.total_value
        details[atype]["records"].append(r.to_dict())
    return {
        "date": summary.date,
        "total": summary.total,
        "by_type": summary.by_type,
        "details": details,
    }


@router.get("/api/products")
async def get_products(asset_type: Optional[str] = None):
    records = store.get_records(asset_type=asset_type)
    # 返回所有产品，前端自行过滤 _删除
    return [r.to_dict() for r in records]


@router.get("/api/product/{name}")
async def get_product(name: str):
    product = store.get_product_by_name(name)
    if product is None:
        return JSONResponse(status_code=404, content={"message": "not found"})
    operations = store.get_operations(name)
    return {
        "current": product.to_dict(),
        "operations": operations,
    }
