from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional
from pymongo.database import Database
from bson import ObjectId
from datetime import datetime
from app.models.order import OrderCreate, OrderUpdate, OrderDB
from app.database import get_database

router = APIRouter(
    prefix="/orders",
    tags=["orders"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=OrderDB, status_code=status.HTTP_201_CREATED)
async def create_order(order: OrderCreate, db: Database = Depends(get_database)):
    order_dict = order.dict()
    
    for prod_id in order_dict["product_ids"]:
        if not db.products.find_one({"_id": prod_id}):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product with ID {prod_id} does not exist"
            )
    
    result = db.orders.insert_one(order_dict)
    created_order = db.orders.find_one({"_id": result.inserted_id})
    return created_order

@router.get("/", response_model=List[OrderDB])
async def read_orders(
    skip: int = 0, 
    limit: int = 100, 
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Database = Depends(get_database)
):
    query = {}
    if start_date and end_date:
        query["date"] = {"$gte": start_date, "$lte": end_date}
    elif start_date:
        query["date"] = {"$gte": start_date}
    elif end_date:
        query["date"] = {"$lte": end_date}
    
    orders = list(db.orders.find(query).skip(skip).limit(limit))
    return orders

@router.get("/{order_id}", response_model=OrderDB)
async def read_order(order_id: str, db: Database = Depends(get_database)):
    if (order := db.orders.find_one({"_id": ObjectId(order_id)})) is not None:
        return order
    raise HTTPException(status_code=404, detail=f"Order with ID {order_id} not found")

@router.put("/{order_id}", response_model=OrderDB)
async def update_order(
    order_id: str, 
    order_update: OrderUpdate, 
    db: Database = Depends(get_database)
):
    existing_order = db.orders.find_one({"_id": ObjectId(order_id)})
    if not existing_order:
        raise HTTPException(status_code=404, detail=f"Order with ID {order_id} not found")
    
    update_data = {k: v for k, v in order_update.dict().items() if v is not None}
    
    if "product_ids" in update_data and update_data["product_ids"]:
        for prod_id in update_data["product_ids"]:
            if not db.products.find_one({"_id": prod_id}):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Product with ID {prod_id} does not exist"
                )
    
    if update_data:
        db.orders.update_one(
            {"_id": ObjectId(order_id)},
            {"$set": update_data}
        )
    
    return db.orders.find_one({"_id": ObjectId(order_id)})

@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_order(order_id: str, db: Database = Depends(get_database)):
    if not db.orders.find_one({"_id": ObjectId(order_id)}):
        raise HTTPException(status_code=404, detail=f"Order with ID {order_id} not found")
    
    db.orders.delete_one({"_id": ObjectId(order_id)})
    return
