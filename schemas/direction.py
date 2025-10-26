from pydantic import BaseModel
from typing import List, Optional

class FacultyShort(BaseModel):
    id: int
    short_name: str

class Direction(BaseModel):
    id: int
    name: str
    cipher: str
    degree_study: str
    faculty: FacultyShort

class DirectionList(BaseModel):
    directions: List[Direction]