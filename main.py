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
        session = request_data.session
        nlu = request_data.request.nlu
        current_state = request_data.state.session or {}

        response = {
            "version": request_data.version,
            "session": session,
            "response": {
                "end_session": False,
                "text": ""
            },
            "session_state": current_state
        }

        if not user_input or session["new"] == "true" or not current_state.get('current_step'):
            response['response']['text'] = 'Привет, это голосовой помощник, назовите тип нужного для вас расписания: преподаватель, аудитория или группа'
            response['session_state'] = {'current_step': 'start'}
        
        elif current_state.get('current_step') == 'start':
            if "преподаватель" in user_input:
                response['response']['text'] = 'Назовите имя преподавателя'
                response['session_state'] = {'current_step': 'waiting_teacher_name'}
            elif "аудитория" in user_input:
                response['response']['text'] = 'Назовите номер аудитории'
                response['session_state'] = {'current_step': 'waiting_room_number'}
            elif "группа" in user_input:
                response['response']['text'] = 'Назовите номер группы'
                response['session_state'] = {'current_step': 'waiting_group_number'}
            else:
                response['response']['text'] = 'Пожалуйста, выберите тип расписания: преподаватель, аудитория или группа'
        
        elif current_state.get('current_step') == 'waiting_teacher_name':
            print(f"Пользователь ввел: {user_input}")
            fio_dict = find_teacher(nlu)
            print(f"Извлеченные данные преподавателя: {fio_dict}")
            
            if not fio_dict or not any([fio_dict.get('last_name'), fio_dict.get('first_name'), fio_dict.get('full_name')]):
                response['response']['text'] = 'Не нашла ФИО в запросе. Пожалуйста, назовите имя преподавателя еще раз.'
            else:
                result = await get_teacher_id(fio_dict)
                print(f"Результат поиска преподавателя: {result} (тип: {type(result)})")
                
                if not result:
                    response['response']['text'] = 'Не нашла такого преподавателя. Пожалуйста, уточните фамилию.'
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
                        
                        response['session_state'] = {
                            **current_state,
                            'teacher_candidates': result,
                            'current_step': 'waiting_teacher_choice'
                        }
                else:
                    response['session_state'] = {
                        **current_state,
                        'current_step': 'waiting_date',
                        'teacher_id': result,
                        'teacher_info': fio_dict
                    }
                    response['response']['text'] = f'На какой день нужно расписание?'
        
        elif current_state.get('current_step') == 'waiting_teacher_choice':
            if user_input.isdigit():
                index = int(user_input) - 1
                teacher_candidates = current_state.get('teacher_candidates', [])
                
                if 0 <= index < len(teacher_candidates):
                    selected_teacher = teacher_candidates[index]
                    teacher_id = selected_teacher.get('id')
                    
                    print(f"Выбран преподаватель: {selected_teacher.get('full_name')} с ID: {teacher_id}")
                    
                    response['session_state'] = {
                        **current_state,
                        'current_step': 'waiting_date',
                        'teacher_id': teacher_id,
                        'teacher_info': selected_teacher
                    }
                    response['response']['text'] = f'Выбран преподаватель: {selected_teacher.get("full_name", "")}. На какой день нужно расписание?'
                else:
                    response['response']['text'] = 'Неверный номер. Пожалуйста, выберите номер из списка.'
            else:
                response['response']['text'] = 'Пожалуйста, укажите номер преподавателя из списка.'
        
        elif current_state.get('current_step') == 'waiting_date':
            try:
                teacher_id = current_state.get('teacher_id')
                teacher_info = current_state.get('teacher_info', {})
                
                print(f"Текущий teacher_id: {teacher_id}")
                print(f"Информация о преподавателе: {teacher_info}")
                
                if not teacher_id:
                    response['response']['text'] = 'Ошибка: не найден ID преподавателя. Давайте начнем сначала.'
                    response['session_state'] = {'current_step': 'start'}
                else:
                    target_date = parse_date(nlu)
            
                    if not target_date:
                        response['response']['text'] = 'Не поняла дату. Пожалуйста, укажите дату, например: "на завтра", "на понедельник" или конкретную дату.'
                    else:
                        print(f"Запрашиваем расписание для teacher_id: {teacher_id} на дату: {target_date}")
                        schedule_text = await get_schedule(teacher_id, target_date)
                        if not schedule_text:
                            response['response']['text'] = 'Расписание не найдено.'
                        else:
                            response['response']['text'] = schedule_text
                            response['session_state'] = {'current_step': 'start'}
            except Exception as e:
                print(f"Ошибка при обработке даты: {str(e)}")
                response['response']['text'] = 'Произошла ошибка при обработке даты. Попробуйте еще раз.'

        return response
        
    except Exception as e:
        print(f"Произошла ошибка: {str(e)}")
        return {
            "response": {
                "text": "Произошла ошибка. Попробуйте еще раз.",
                "end_session": False
            },
            "session_state": {},
            "version": "1.0"
        }
        

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)