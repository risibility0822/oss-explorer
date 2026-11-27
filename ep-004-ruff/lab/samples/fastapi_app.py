from fastapi import FastAPI, HTTPException
import os, sys, json
from typing import List, Optional, Dict

app = FastAPI()
ORDERS: Dict[str, dict] = {}


@app.get("/orders")
def list_orders(status: Optional[str] = None, tags: List[str] = []):
    result = []
    for id, order in ORDERS.items():
        if status == None or order["status"] == status:
            result.append(order)
    print(f"回傳訂單")
    return result


@app.get("/orders/{order_id}")
def get_order(order_id: str):
    try:
        return ORDERS[order_id]
    except:
        raise HTTPException(status_code=404, detail="找不到訂單")
