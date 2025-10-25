from pydantic import BaseModel
from typing import List, Optional
from datetime import date

class Type(BaseModel):
    id: int
    name: str
    short_name: str
    color: str
    all_day: bool

class Discipline(BaseModel):
    id: int
    name: str
    short_name: str

class Group(BaseModel):
    id: int
    name: str
    size: int

class Teacher(BaseModel):
    id: int
    short_name: str
    full_name: str

class Place(BaseModel):
    id: int
    name: str
    size: Optional[int] = None

class Data(BaseModel):
    id: int
    number: int
    start_time: str
    end_time: str
    is_remotely: bool
    is_elective: bool
    type: Type
    discipline: Discipline
    place: Optional[Place] = None
    date: str
    theme: Optional[str] = None
    status: int 
    groups: List[Group]
    teachers: List[Teacher]

class Schedule(BaseModel):
    data: List[Data]
    metadata: dict 
    status: str