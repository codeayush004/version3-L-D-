from pydantic import BaseModel, EmailStr
from typing import Optional

class AuthModel(BaseModel):
    username: str
    password: str

class BatchModel(BaseModel):
    name: str
    manager_id: str
    department: str = "Data Ops"
class ScoreUpdateModel(BaseModel):
    EmpID: str
    subject: str
    score: float
    total_marks: Optional[int] = None
    manager_id: str
    batch_id: str

class SubjectDeleteModel(BaseModel):
    subject: str
    manager_id: str
    batch_id: str

class SubjectUpdateModel(BaseModel):
    old_name: str
    new_name: Optional[str] = None
    total_marks: Optional[int] = None
    manager_id: str
    batch_id: str



class ChatQueryModel(BaseModel):
    query: str
    manager_id: str
    batch_id: str
    history: Optional[list] = []




