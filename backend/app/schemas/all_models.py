from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any

class AuthModel(BaseModel):
    username: str
    password: str

class BatchModel(BaseModel):
    name: str
    manager_id: str
    department: str = "Data Ops"

class InternModel(BaseModel):
    Name: str
    Email: EmailStr
    EmpID: str
    manager_id: str
    batch_id: str

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

class FeedbackColumnModel(BaseModel):
    name: str
    manager_id: str
    batch_id: str

class FeedbackCellUpdateModel(BaseModel):
    EmpID: str
    column: str
    text: str
    manager_id: str
    batch_id: str

class ChatQueryModel(BaseModel):
    query: str
    manager_id: str
    batch_id: str

class AttemptUpdateModel(BaseModel):
    EmpID: str
    subject: str
    attempt_note: str
    manager_id: str
    batch_id: str

class ManagerSheetLinkModel(BaseModel):
    manager_id: str
    batch_id: str
    sheet_url: Optional[str] = None
    file_path: Optional[str] = None
    type: str # 'link' or 'upload'

class SyncFeedbackModel(BaseModel):
    manager_id: str
    batch_id: str
