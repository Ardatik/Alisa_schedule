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
logger = logging.getLogger(__name__)
app = FastAPI()

@app.post('/webhook')
async def handler(request_data: AliceRequest):
    try:
        user_input = request_data.request.original_utterance.lower().strip()
        session = request_data.session
        nlu = request_data.request.nlu

        response = {
            "version": request_data.version,
            "session": session,
            "response": {
                "end_session": False,
                "text": ""
            }
        }
            
        if not user_input:
            response['response']['text'] = 'Привет, это голосовой помощник, назовите тип нужного для вас расписания: преподаватель, аудитория или группа'
        else:
            print(user_input)
            response['response']['text'] = 'Назовите имя преподавателя'
            fio_dict = find_teacher(nlu)
            print(fio_dict)
            if not fio_dict:
                response['response']['text'] = 'Не нашла ФИО в запросе'
            else:
                result = await get_teacher_id(fio_dict)
                print(result)
                if not result:
                    response['response']['text'] = 'Не нашла такого преподавателя'
                elif isinstance(result, list):
                    if not result:
                        response['response']['text'] = 'Не нашла такого преподавателя'
                    else:
                        choices = "Нашлось несколько преподавателей:\n"
                        for i, teacher in enumerate(result, 1):
                            name = teacher.get('full_name', f'Преподаватель {i}')
                            choices += f"{i}. {name}\n"
                        choices += "\nУкажите номер нужного преподавателя."
                        response['response']['text'] = choices
                    session_state = request.get('state', {}).get('session', {})
                    if isinstance(result, list):
                        session_state['teacher_candidates'] = result
                        session_state['awaiting_teacher_choice'] = True
                        response['session_state'] = session_state
                    else:
                        response['session_state'] = {}
                    response['session_state'] = result
                else:
                    teacher_id = result
                    target_date = parse_date(nlu)
                    if not target_date:
                        response['response']['text'] = 'Некорректная дата в запросе'
                    else:
                        schedule_text = await get_schedule(teacher_id, target_date)
                        if not schedule_text:
                            response['response']['text'] = 'Расписание не найдено.'
                        else:
                            response['response']['text'] = schedule_text
        return response
    
    except Exception as e:
        logger.exception(f"Произошла ошибка: {str(e)}")
        return {
            "version": request_data.version,
            "session": request_data.session,
            "response": {
                "end_session": True,
                "text": "Произошла ошибка"
            }
        }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
    