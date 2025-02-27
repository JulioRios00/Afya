from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from app.utils.object_id import PyObjectId
from bson import ObjectId

class OrderBase(BaseModel):
    date: datetime = Field(default_factory=datetime.now)
    product_ids: List[PyObjectId]
    total: float

class OrderCreate(BaseModel):
    product_ids: List[str]
    total: float
    date: datetime = Field(default_factory=datetime.now)
    customer_email: Optional[str] = None 

class OrderUpdate(BaseModel):
    date: Optional[datetime] = None
    product_ids: Optional[List[PyObjectId]] = None
    total: Optional[float] = None

class OrderDB(OrderBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
