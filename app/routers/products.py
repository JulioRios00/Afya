from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional
from pymongo.database import Database
from bson import ObjectId
from app.models.product import ProductCreate, ProductUpdate, ProductDB
from app.database import get_database

router = APIRouter(
    prefix="/products",
    tags=["products"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=ProductDB, status_code=status.HTTP_201_CREATED)
async def create_product(product: ProductCreate, db: Database = Depends(get_database)):
    product_dict = product.model_dump()
    
    if product_dict["category_ids"]:
        for cat_id in product_dict["category_ids"]:
            if not db.categories.find_one({"_id": cat_id}):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Category with ID {cat_id} does not exist"
                )
    
    result = db.products.insert_one(product_dict)
    created_product = db.products.find_one({"_id": result.inserted_id})
    return created_product

@router.get("/", response_model=List[ProductDB])
async def read_products(
    skip: int = 0, 
    limit: int = 100, 
    category_id: Optional[str] = None,
    db: Database = Depends(get_database)
):
    query = {}
    if category_id:
        query["category_ids"] = ObjectId(category_id)
    
    products = list(db.products.find(query).skip(skip).limit(limit))
    return products

@router.get("/{product_id}", response_model=ProductDB)
async def read_product(product_id: str, db: Database = Depends(get_database)):
    if (product := db.products.find_one({"_id": ObjectId(product_id)})) is not None:
        return product
    raise HTTPException(status_code=404, detail=f"Product with ID {product_id} not found")

@router.put("/{product_id}", response_model=ProductDB)
async def update_product(
    product_id: str, 
    product_update: ProductUpdate, 
    db: Database = Depends(get_database)
):
    existing_product = db.products.find_one({"_id": ObjectId(product_id)})
    if not existing_product:
        raise HTTPException(status_code=404, detail=f"Product with ID {product_id} not found")
    
    update_data = {k: v for k, v in product_update.dict().items() if v is not None}
    
    if "category_ids" in update_data and update_data["category_ids"]:
        for cat_id in update_data["category_ids"]:
            if not db.categories.find_one({"_id": cat_id}):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Category with ID {cat_id} does not exist"
                )
    
    if update_data:
        db.products.update_one(
            {"_id": ObjectId(product_id)},
            {"$set": update_data}
        )
    
    return db.products.find_one({"_id": ObjectId(product_id)})

@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(product_id: str, db: Database = Depends(get_database)):
    if not db.products.find_one({"_id": ObjectId(product_id)}):
        raise HTTPException(status_code=404, detail=f"Product with ID {product_id} not found")
    
    db.products.delete_one({"_id": ObjectId(product_id)})
    
    db.orders.update_many(
        {"product_ids": ObjectId(product_id)},
        {"$pull": {"product_ids": ObjectId(product_id)}}
    )

    affected_orders = db.orders.find({"product_ids": {"$size": 0}})
    for order in affected_orders:
        db.orders.update_one(
            {"_id": order["_id"]},
            {"$set": {"total": 0}}
        )
    
    return
