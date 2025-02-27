from fastapi import APIRouter, Depends, Query
from typing import List, Optional, Dict, Any
from pymongo.database import Database
from bson import ObjectId
from datetime import datetime, timedelta
from app.database import get_database

router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"],
    responses={404: {"description": "Not found"}},
)

@router.get("/sales")
async def get_sales_dashboard(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    category_id: Optional[str] = None,
    product_id: Optional[str] = None,
    db: Database = Depends(get_database)
):
    if not start_date:
        start_date = datetime.now() - timedelta(days=30)
    if not end_date:
        end_date = datetime.now()
    
    match_stage = {"date": {"$gte": start_date, "$lte": end_date}}
    
    if product_id:
        match_stage["product_ids"] = ObjectId(product_id)
    
    pipeline = [{"$match": match_stage}]
    
    if category_id:
        products_in_category = list(db.products.find(
            {"category_ids": ObjectId(category_id)},
            {"_id": 1}
        ))
        product_ids = [p["_id"] for p in products_in_category]
        
        match_stage["product_ids"] = {"$in": product_ids}
        pipeline[0]["$match"] = match_stage
    
    pipeline.extend([
        {
            "$group": {
                "_id": None,
                "total_orders": {"$sum": 1},
                "total_revenue": {"$sum": "$total"},
                "avg_order_value": {"$avg": "$total"}
            }
        }
    ])
    
    results = list(db.orders.aggregate(pipeline))
    
    time_series_pipeline = [
        {"$match": match_stage},
        {
            "$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$date"}},
                "orders": {"$sum": 1},
                "revenue": {"$sum": "$total"}
            }
        },
        {"$sort": {"_id": 1}}
    ]
    time_series = list(db.orders.aggregate(time_series_pipeline))
    
    top_products_pipeline = [
        {"$match": match_stage},
        {"$unwind": "$product_ids"},
        {
            "$group": {
                "_id": "$product_ids",
                "count": {"$sum": 1}
            }
        },
        {"$sort": {"count": -1}},
        {"$limit": 5},
        {
            "$lookup": {
                "from": "products",
                "localField": "_id",
                "foreignField": "_id",
                "as": "product_info"
            }
        },
        {"$unwind": "$product_info"},
        {
            "$project": {
                "product_id": "$_id",
                "product_name": "$product_info.name",
                "count": 1
            }
        }
    ]
    top_products = list(db.orders.aggregate(top_products_pipeline))
    
    if not results:
        stats = {
            "total_orders": 0,
            "total_revenue": 0,
            "avg_order_value": 0
        }
    else:
        stats = {
            "total_orders": results[0]["total_orders"],
            "total_revenue": results[0]["total_revenue"],
            "avg_order_value": results[0]["avg_order_value"]
        }
    
    return {
        "stats": stats,
        "time_series": time_series,
        "top_products": top_products
    }
