from fastapi import FastAPI
import uvicorn
from schemas.Alice_Request import AliceRequest, Nlu, Entity
from dotenv import load_dotenv
import os
import httpx
from schedule_processing import process_data_to_text_for_cabinets, process_data_to_text_for_teachers
from typing import Optional, Dict, Any
from parse_date import parse_date

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
            full_name_parts = [i for i in [last_name, first_name, patronymic] if i]
            fio_data["full_name"] = " ".join(full_name_parts)
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
        return candidates
        



def get_schedule(id, target_date):
    env_var = os.getenv("GET_SCHEDULE_FOR_TEACHER")
    request_url = env_var + str(id)
    data = request(request_url)   
    return process_data_to_text_for_teachers(data, target_date)



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
            response['response']['text'] = 'Привет, это голосовой помощник, назовите фамилию преподавателя и дату или номер аудитории'
        else:
            fio_dict = find_teacher(nlu)
            if not fio_dict:
                response['response']['text'] = 'Не нашла ФИО в запросе'
            else:
                result = get_teacher_id(fio_dict)
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
                    session_state['teacher_candidates'] = result
                    session_state['awaiting_teacher_choice'] = True
                    response['session_state'] = session_state
                else:
                    teacher_id = result
                    target_date = parse_date(nlu)
                    if not target_date:
                        response['response']['text'] = 'Некорректная дата в запросе'
                    else:
                        schedule_text = get_schedule(teacher_id, target_date)
                        if not schedule_text:
                            response['response']['text'] = 'Расписание не найдено.'
                        else:
                            response['response']['text'] = schedule_text
        return response
    
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
    