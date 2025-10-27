from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date


class Type(BaseModel):
    id: int
    name: str
    short_name: str
    color: str
    all_day: bool


class Discipline(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    short_name: Optional[str] = None


class Place(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    size: Optional[int] = None


class Group(BaseModel):
    id: int
    name: str
    size: Optional[int] = None


class Teacher(BaseModel):
    id: int
    short_name: str
    full_name: str


class Lesson(BaseModel):
    id: int
    number: int
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    is_remotely: bool
    is_elective: bool
    type: Type
    discipline: Optional[Discipline] = None
    place: Optional[Place] = None
    date: date
    theme: Optional[str] = None
    status: int
    groups: List[Group]
    teachers: List[Teacher]


class Schedule(BaseModel):
    data: List[Lesson]
