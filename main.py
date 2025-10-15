from fastapi import FastAPI
import uvicorn
from schemas.Alice_Request import AliceRequest, Nlu, Entity
from typing import Optional, Dict, Any
from service.date.parse_date import parse_date
from service.teachers.find_teacher_by_name import find_teacher
from service.teachers.find_teacher_by_id import get_teacher_id
from service.request.request_data import request
from service.schedule.get_schedule import get_schedule 
import logging

logging.basicConfig(level=logging.INFO)
app = FastAPI()

@app.post('/webhook')
async def handler(request_data: AliceRequest):
    try:
        user_input = request_data.request.original_utterance.lower().strip()
        #session = request_data.session
        nlu = request_data.request.nlu
        current_state = request_data.state.session or {}

        response = {
            "response": {
                "text": "Привет, это голосовой помощник, назовите тип нужного для вас расписания: преподаватель, аудитория или группа",
                "tts": "Привет, это голосовой помощник, назовите тип нужного для вас расписания: преподаватель, аудитория или группа",
                "end_session": False
            },
            "session_state": {},
            "user_state_update": {},
            "application_state": {},
            "version": request_data.version
        }
        
        if "преподаватель" in user_input:
            response["session_state"] = {"current_mode": "teacher"}
            response["response"]["text"] = "Хорошо, назовите фамилию преподавателя"
            response["response"]["tts"] = "Хорошо, назовите фамилию преподавателя"
            
        return response
        
    except Exception as e:
        print(f"Произошла ошибка: {str(e)}")
        return {
            "response": {
                "text": "Произошла ошибка. Попробуйте еще раз.",
                "tts": "Произошла ошибка. Попробуйте еще раз.",
                "end_session": False
            },
            "session_state": {},
            "user_state_update": {},
            "application_state": {},
            "version": "1.0"  # Обязательно строка "1.0"
        }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)