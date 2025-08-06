from pydantic import BaseModel
from typing import List, Optional
from datetime import date

class Type(BaseModel):
    id: int
    name: str
    short_name: str
    
class Discipline(BaseModel):
    id: int
    name: str
    short_name: str
    
class Place(BaseModel):
    id: int
    name: str
    size: int

class Group(BaseModel):
    id: int
    name: str
    
class Teacher(BaseModel):
    id: int
    short_name: str
    full_name: str

class Data(BaseModel):
    id: int
    number: int
    start_time: str
    end_time: str
    type: Type
    discipline: Discipline
    place: Place | None
    date: date
    status: int
    groups: List[Group]
    teachers: List[Teacher]

class Metadata(BaseModel):
    semester_id: int
    week: str | None
    start_date: date
    end_date: date

class Schedule(BaseModel):
    data: List[Data]
    metadata: Metadata
    status: str