from fastapi import FastAPI
import uvicorn
from schemas.Alice_Request import AliceRequest, Nlu, Entity
from dotenv import load_dotenv
import os
import httpx
from schedule_processing import process_data_to_text_for_cabinets, process_data_to_text_for_teachers
from typing import Optional, Dict, Any

app = FastAPI()
load_dotenv()

def find_teacher(nlu: Nlu) -> Dict[str, str]:
    fio_data = {}
    entities = nlu.entities
    for entity in entities:
        entity_value = entity.value
        if entity.type == 'YANDEX.FIO':
            first_name = entity_value.get('first_name', '')
            last_name = entity_value.get('last_name', '')
            patronymic = entity_value.get('patronymic_name', '')
            if last_name:
                fio_data["last_name"] = last_name
            if first_name:
                fio_data["first_name"] = first_name
            if patronymic:
                fio_data["patronymic"] = patronymic
            full_name_parts = [last_name, first_name, patronymic]
            fio_data["full_name"] = " ".join(filter(None, full_name_parts))
            break
    return fio_data

def request(api_url):
    with httpx.Client() as client:
        try:
            request = client.get(api_url)
            request.raise_for_status()
            data = request.json()
            return data
        except httpx.HTTPStatusError as exc:
            return f"Ошибка при получении расписания: {exc.response.status_code}"
        except Exception as e:
            return f"Произошла ошибка: {str(e)}"

def get_teacher_id(fio_data):
    if not fio_data or not fio_data.get("last_name"):
        return None
    env_var = os.getenv("GET_TEACHERS")
    request_url = env_var + fio_data["last_name"]
    data = request(request_url)
    for teacher in data.get("teachers"):
        if teacher.get("full_name") == fio_data["full_name"]:
            return teacher.get("id")
    return None

def get_schedule(id, schedule_type):
    env_var = os.getenv("GET_SCHEDULE_FOR_TEACHER")
    request_url = env_var + id
    data = request(request_url)   
    if schedule_type == "cabinet":
        return process_data_to_text_for_cabinets(data)
    elif schedule_type == "teacher":
        return process_data_to_text_for_teachers(data)
    elif schedule_type == "group":
        return "Расписание для групп пока не реализовано"
    else:
        return "Неподдерживаемый тип расписания"    


@app.get('/ind')
async def ttest():
    return {'a': 'b'}
    
    
@app.post('/webhook')
async def handler(request_data: AliceRequest):
    try:
        user_input = request_data.request.original_utterance.strip()
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
            print(user_input)
            response['response']['text'] = 'Привет, это голосовой помощник, назовите фамилию преподавателя и дату или номер аудитории'
        else:
            #fio_dict = find_teacher(nlu)
            response['response']['text'] = 'fffffffffff' #fio_dict["first_name"]
            
            return response

            
            
            
            """curr_stage = "choose_type"
            if curr_stage == "choose_type":
                if 'преподаватель' in user_input:
                    schedule_type = 'teacher'
                elif 'аудитория' in user_input:
                    schedule_type = 'place'
                elif 'группа' in user_input:
                    schedule_type = 'group'
                else:
                    response['response']['text'] = 'не смогла распознать тип расписания'
                    curr_stage = "choose_entity"
            if curr_stage == "choose_entity":
                fio_data = find_teacher(nlu)
                print(fio_data)
                if fio_data:
                    print('yes')
                    teacher_id = get_teacher_id(nlu)
                    print(teacher_id)
                    if teacher_id:
                        response['response']['text'] = get_schedule(teacher_id, schedule_type)
                    else:
                        response['response']['text'] = 'Преподаватель не найден. Пожалуйста, уточните ФИО.'
                else:
                    response['response']['text'] = 'Назовите фамилию, имя и отчество преподавателя '
                    curr_stage = "get_schedule"
            if curr_stage == "get_schedule":
                response['response']['text'] = 'ok '"""
            
            
            
    except Exception as e:
        print(f"Произошла ошибка: {str(e)}")
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
    
    
"""def get_teacher_id(fio_data):
    if not fio_data:
        return None
    last_name = fio_data.get("last_name", "")
    first_name = fio_data.get("first_name", "")
    patronymic = fio_data.get("patronymic", "")
    full_name = fio_data.get("full_name", "").lower()
    search_param = last_name or first_name
    print(f"last_name='{last_name}', first_name='{first_name}', patronymic='{patronymic}', full_name='{full_name}'")
    print("search_param: ", search_param)
    if not search_param:
        return None
    try:
        env_var = os.getenv("GET_TEACHERS")
        request_url = env_var + search_param
        print(f"запрос: {request_url}")
        data = request(request_url)
        print(f"данные от API: {data}")
    except Exception as e:
        print(f"Ошибка при запросе данных: {e}")
        return None
    candidates = []
    for teacher in data.get("teachers", []):
        if not teacher.get("full_name"):
            print(f"Пропускаем преподавателя без full_name: {teacher}")
            continue
        teacher_parts = teacher["full_name"].lower().split()
        teacher_last = teacher_parts[0] if len(teacher_parts) > 0 else ""
        teacher_first = teacher_parts[1] if len(teacher_parts) > 1 else ""
        teacher_patr = teacher_parts[2] if len(teacher_parts) > 2 else ""
        print(f"Анализируем преподавателя: {teacher['full_name']} (ID: {teacher['id']})")
        if full_name and " ".join(teacher_parts) == full_name:
            print("Найдено полное совпадение по ФИО")
            candidates.append({
                "id": teacher["id"],
                "full_name": teacher["full_name"],
                "short_name": teacher.get("short_name", "")
            })
            continue
        if last_name and first_name:
            if teacher_last == last_name.lower() and teacher_first == first_name.lower():
                print("Найдено совпадение по фамилии и имени")
                candidates.append({
                    "id": teacher["id"],
                    "full_name": teacher["full_name"],
                    "short_name": teacher.get("short_name", "")
                })
                continue
        if not last_name and first_name and patronymic:
            if teacher_first == first_name.lower() and teacher_patr == patronymic.lower():
                print("Найдено совпадение по имени и отчеству")
                candidates.append({
                    "id": teacher["id"],
                    "full_name": teacher["full_name"],
                    "short_name": teacher.get("short_name", "")
                })
                continue
        if last_name and not first_name and not patronymic:
            if teacher_last == last_name.lower():
                print("Найдено совпадение только по фамилии")
                candidates.append({
                    "id": teacher["id"],
                    "full_name": teacher["full_name"],
                    "short_name": teacher.get("short_name", "")
                })
    if not candidates:
        print("Не найдено подходящих преподавателей")
        return None
    elif len(candidates) == 1:
        print(f"Возвращаем ID единственного кандидата: {candidates[0]['id']}")
        return candidates[0]["id"]
    else:
        print(f"Возвращаем список из {len(candidates)} кандидатов")
        return candidates"""