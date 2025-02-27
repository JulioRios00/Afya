from pydantic import BaseModel, Field
from typing import Optional
from app.utils.object_id import PyObjectId
from bson import ObjectId

class CategoryBase(BaseModel):
    name: str
    
class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(CategoryBase):
    name: Optional[str] = None


class CategoryDB(CategoryBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

