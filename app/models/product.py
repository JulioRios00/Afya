from pydantic import BaseModel, Field
from typing import List, Optional
from app.utils.object_id import PyObjectId
from bson import ObjectId

class ProductBase(BaseModel):
    name: str
    description: str
    price: str
    category_ids: List[PyObjectId] = None
    image_url: Optional[str] = None
    
class ProductCreate(ProductBase):
    pass

class ProductUpdate(ProductBase):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[str] = None
    category_ids: Optional[List[PyObjectId]] = None
    image_url: Optional[str] = None

class ProductDB(ProductBase):
    id:	PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

