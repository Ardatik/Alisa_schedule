from fastapi import FastAPI
import uvicorn
from schemas.Alice_Request import AliceRequest, Nlu, Entity
from typing import Optional, Dict, Any
from service.date.parse_date import parse_date
from service.teachers.find_teacher_by_name import find_teacher
from service.teachers.find_teacher_by_id import get_teacher_id
from service.request.request_data import request
from service.schedule.get_schedule import get_schedule 
from service.cabinets.find_cabinet import find_auditory, get_cabinet_id
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

        if not user_input or session.get("new") or not current_state.get('current_step'):
            response['response']['text'] = 'Привет, это голосовой помощник, назовите тип нужного для вас расписания: преподаватель, аудитория или группа'
            response['session_state'] = {'current_step': 'start'}
            return response

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
            return response

        elif current_state.get('current_step') == 'waiting_teacher_name':
            fio_dict = find_teacher(nlu)            
            if not fio_dict or not any([fio_dict.get('last_name'), fio_dict.get('first_name'), fio_dict.get('full_name')]):
                response['response']['text'] = 'Не нашла ФИО в запросе. Пожалуйста, назовите имя преподавателя еще раз.'
            else:
                result = await get_teacher_id(fio_dict)                
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
                            'current_step': 'waiting_teacher_choice',
                            'teacher_candidates': result
                        }
                else:
                    response['session_state'] = {
                        'current_step': 'waiting_date',
                        'entity_type': 'teacher',
                        'entity_id': result,
                        'entity_info': fio_dict
                    }
                    teacher_name = fio_dict.get('full_name', 'преподавателя')
                    response['response']['text'] = f'На какой день нужно расписание для {teacher_name}?'
            return response

        elif current_state.get('current_step') == 'waiting_room_number':
            auditory_dict = find_auditory(nlu)            
            if not auditory_dict or not auditory_dict.get('number'):
                response['response']['text'] = 'Не нашла номер аудитории в запросе. Пожалуйста, назовите номер аудитории еще раз.'
            else:
                result = await get_cabinet_id(auditory_dict)                
                if not result:
                    response['response']['text'] = f'Не нашла аудиторию {auditory_dict["number"]}. Пожалуйста, уточните номер.'
                elif isinstance(result, list):
                    if not result:
                        response['response']['text'] = f'Не нашла аудиторию {auditory_dict["number"]}'
                    else:
                        choices = "Нашлось несколько аудиторий:\n"
                        for i, cabinet in enumerate(result, 1):
                            name = cabinet.get('name', f'Аудитория {i}')
                            choices += f"{i}. {name}\n"
                        choices += "\nУкажите номер нужной аудитории."
                        response['response']['text'] = choices
                        response['session_state'] = {
                            'current_step': 'waiting_cabinet_choice',
                            'cabinet_candidates': result
                        }
                else:
                    response['session_state'] = {
                        'current_step': 'waiting_date',
                        'entity_type': 'cabinet',
                        'entity_id': result,
                        'entity_info': auditory_dict
                    }
                    response['response']['text'] = f'На какой день нужно расписание для аудитории {auditory_dict["number"]}?'
            return response

        elif current_state.get('current_step') == 'waiting_teacher_choice':
            if user_input.isdigit():
                index = int(user_input) - 1
                teacher_candidates = current_state.get('teacher_candidates', [])
                
                if 0 <= index < len(teacher_candidates):
                    selected_teacher = teacher_candidates[index]
                    teacher_id = selected_teacher.get('id')
                    response['session_state'] = {
                        'current_step': 'waiting_date',
                        'entity_type': 'teacher',
                        'entity_id': teacher_id,
                        'entity_info': selected_teacher
                    }
                    response['response']['text'] = f'Выбран преподаватель: {selected_teacher.get("full_name", "")}. На какой день нужно расписание?'
                else:
                    response['response']['text'] = 'Неверный номер. Пожалуйста, выберите номер из списка.'
            else:
                response['response']['text'] = 'Пожалуйста, укажите номер преподавателя из списка.'
            return response

        elif current_state.get('current_step') == 'waiting_cabinet_choice':
            if user_input.isdigit():
                index = int(user_input) - 1
                cabinet_candidates = current_state.get('cabinet_candidates', [])
                
                if 0 <= index < len(cabinet_candidates):
                    selected_cabinet = cabinet_candidates[index]
                    cabinet_id = selected_cabinet.get('id')
                    print(f"Выбрана аудитория: {selected_cabinet.get('name')} с ID: {cabinet_id}")
                    response['session_state'] = {
                        'current_step': 'waiting_date',
                        'entity_type': 'cabinet',
                        'entity_id': cabinet_id,
                        'entity_info': selected_cabinet
                    }
                    response['response']['text'] = f'Выбрана аудитория: {selected_cabinet.get("name", "")}. На какой день нужно расписание?'
                else:
                    response['response']['text'] = 'Неверный номер. Пожалуйста, выберите номер из списка.'
            else:
                response['response']['text'] = 'Пожалуйста, укажите номер аудитории из списка.'
            return response

        elif current_state.get('current_step') == 'waiting_date':
            try:
                entity_type = current_state.get('entity_type')
                entity_id = current_state.get('entity_id')
                entity_info = current_state.get('entity_info', {})                
                if not entity_id:
                    response['response']['text'] = f'Ошибка: не найден ID {entity_type}. Давайте начнем сначала.'
                    response['session_state'] = {'current_step': 'start'}
                    return response
                
                target_date = parse_date(nlu)
                if not target_date:
                    response['response']['text'] = 'Не поняла дату. Пожалуйста, укажите дату, например: "на завтра", "на понедельник" или конкретную дату.'
                    return response                
                if entity_type == 'teacher':
                    schedule_type = 'teachers'
                else:
                    schedule_type = 'cabinet'
                schedule_text = await get_schedule(entity_id, target_date, schedule_type)
                
                if not schedule_text or schedule_text.startswith('Ошибка'):
                    response['response']['text'] = 'Расписание не найдено или произошла ошибка.'
                else:
                    response['response']['text'] = schedule_text
                
                response['session_state'] = {'current_step': 'start'}
                
            except Exception as e:
                response['response']['text'] = 'Произошла ошибка при обработке запроса. Попробуйте еще раз.'
            return response

        elif current_state.get('current_step') == 'waiting_group_number':
            response['response']['text'] = 'Функционал для групп пока не реализован. Выберите преподавателя или аудиторию.'
            response['session_state'] = {'current_step': 'start'}
            return response

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