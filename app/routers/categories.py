from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
from pymongo.database import Database
from bson import ObjectId
from app.models.category import CategoryCreate, CategoryUpdate, CategoryDB
from app.database import get_database

router = APIRouter(
    prefix="/categories",
    tags=["categories"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=CategoryDB, status_code=status.HTTP_201_CREATED)
async def create_category(category: CategoryCreate, db: Database = Depends(get_database)):
    category_dict = category.dict()
    result = db.categories.insert_one(category_dict)
    created_category = db.categories.find_one({"_id": result.inserted_id})
    return created_category

@router.get("/", response_model=List[CategoryDB])
async def read_categories(
    skip: int = 0, 
    limit: int = 100, 
    db: Database = Depends(get_database)
):
    categories = list(db.categories.find().skip(skip).limit(limit))
    return categories

@router.get("/{category_id}", response_model=CategoryDB)
async def read_category(category_id: str, db: Database = Depends(get_database)):
    if (category := db.categories.find_one({"_id": ObjectId(category_id)})) is not None:
        return category
    raise HTTPException(status_code=404, detail=f"Category with ID {category_id} not found")

@router.put("/{category_id}", response_model=CategoryDB)
async def update_category(
    category_id: str, 
    category_update: CategoryUpdate, 
    db: Database = Depends(get_database)
):
    if not db.categories.find_one({"_id": ObjectId(category_id)}):
        raise HTTPException(status_code=404, detail=f"Category with ID {category_id} not found")
    
    update_data = {k: v for k, v in category_update.dict().items() if v is not None}
    
    if update_data:
        db.categories.update_one(
            {"_id": ObjectId(category_id)},
            {"$set": update_data}
        )
    
    return db.categories.find_one({"_id": ObjectId(category_id)})

@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(category_id: str, db: Database = Depends(get_database)):
    if not db.categories.find_one({"_id": ObjectId(category_id)}):
        raise HTTPException(status_code=404, detail=f"Category with ID {category_id} not found")
    
    db.categories.delete_one({"_id": ObjectId(category_id)})
    
    db.products.update_many(
        {"category_ids": ObjectId(category_id)},
        {"$pull": {"category_ids": ObjectId(category_id)}}
    )
    
    return