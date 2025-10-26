from pydantic import BaseModel
from typing import List, Optional

class FacultyShort(BaseModel):
    id: int
    short_name: str

class DirectionShort(BaseModel):
    id: int
    cipher: str
    short_name: str
    degree_study: str

class Profile(BaseModel):
    id: int
    name: str
    short_name: str

class Department(BaseModel):
    id: int
    name: str
    short_name: str

class Group(BaseModel):
    id: int
    name: str
    course: int
    faculty: FacultyShort
    direction: DirectionShort
    profile: Profile
    department: Department
    size: int

class GroupList(BaseModel):
    groups: List[Group]