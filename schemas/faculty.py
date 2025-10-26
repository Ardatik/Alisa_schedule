from pydantic import BaseModel
from typing import List

class Faculty(BaseModel):
    id: int
    name: str
    short_name: str
    inactive: bool
    
class FacultyList(BaseModel):
    faculties: List[Faculty]