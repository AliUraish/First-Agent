from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class FlagBase(BaseModel):
    flag_name: str
    flag_criteria: str

class FlagCreate(FlagBase):
    pass

class FlagUpdate(BaseModel):
    flag_name: Optional[str] = None
    flag_criteria: Optional[str] = None
    is_active: Optional[bool] = None

class FlagResponse(FlagBase):
    id: str
    user_id: str
    label_id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 