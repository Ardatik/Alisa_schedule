from pydantic import BaseModel
from typing import List, Dict, Any

class Entity(BaseModel):
    type: str
    tokens: Dict[str, int]
    value: Any

class Nlu(BaseModel):
    tokens: List[str]
    entities: List[Entity]
    intents: Dict[str, Any]

class Markup(BaseModel):
    dangerous_context: bool

class Request(BaseModel):
    command: str
    original_utterance: str
    nlu: Nlu
    markup: Markup
    type: str

class AliceRequest(BaseModel):
    session: Dict
    request: Request
    version: str