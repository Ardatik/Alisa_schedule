from service.request.request_data import request
import os

def match_teacher(teacher, fio_data):
    if not teacher.get("full_name"):
        return None
        
    full_name = fio_data["full_name"]
    last_name = fio_data["last_name"]
    first_name = fio_data["first_name"]
    patronymic = fio_data["patronymic"]
    
    teacher_name = teacher["full_name"].lower()
    teacher_parts = teacher_name.split()
    teacher_last = teacher_parts[0] if len(teacher_parts) > 0 else ""
    teacher_first = teacher_parts[1] if len(teacher_parts) > 1 else ""
    teacher_patr = teacher_parts[2] if len(teacher_parts) > 2 else ""
    
    print(f"Анализируем преподавателя: {teacher['full_name']} (ID: {teacher['id']})")
    
    if full_name and " ".join(teacher_parts) == full_name:
        print("Найдено полное совпадение по ФИО")
        return {
            "id": teacher["id"],
            "full_name": teacher["full_name"],
            "short_name": teacher.get("short_name", "")
        }
    
    if last_name and first_name:
        if teacher_last == last_name and teacher_first == first_name:
            print("Найдено совпадение по фамилии и имени")
            return {
                "id": teacher["id"],
                "full_name": teacher["full_name"],
                "short_name": teacher.get("short_name", "")
            }
    
    if not last_name and first_name and patronymic:
        if teacher_first == first_name and teacher_patr == patronymic:
            print("Найдено совпадение по имени и отчеству")
            return {
                "id": teacher["id"],
                "full_name": teacher["full_name"],
                "short_name": teacher.get("short_name", "")
            }
    
    if last_name and not first_name and not patronymic:
        if teacher_last == last_name:
            print("Найдено совпадение только по фамилии")
            return {
                "id": teacher["id"],
                "full_name": teacher["full_name"],
                "short_name": teacher.get("short_name", "")
            }
    
    return None


def get_teachers_from_api(search_param):
    try:
        env_var = os.getenv("GET_TEACHERS")
        request_url = env_var + search_param
        print(f"Запрос: {request_url}")
        data = request(request_url)
        print(f"Данные от API: {data}")
        return data.get("teachers", [])
    except Exception as e:
        print(f"Ошибка при запросе данных: {e}")
        return []


def get_teacher_id(fio_data):
    if not fio_data:
        return None
        
    last_name = fio_data.get("last_name", "").lower()
    first_name = fio_data.get("first_name", "").lower()
    patronymic = fio_data.get("patronymic", "").lower()
    full_name = fio_data.get("full_name", "").lower()
    
    search_param = last_name or first_name
    print(f"Поиск: last_name='{last_name}', first_name='{first_name}', "f"patronymic='{patronymic}', full_name='{full_name}'")
    print("Параметр поиска:", search_param)
    
    if not search_param:
        return None
    
    teachers = get_teachers_from_api(search_param)
    if not teachers:
        print("Не найдено преподавателей в ответе API")
        return None
    
    candidates = []
    for teacher in teachers:
        candidate = match_teacher(teacher, {
            "last_name": last_name,
            "first_name": first_name,
            "patronymic": patronymic,
            "full_name": full_name
        })
        if candidate:
            candidates.append(candidate)
    
    if not candidates:
        print("Не найдено подходящих преподавателей")
        return None
    elif len(candidates) == 1:
        print(f"Возвращаем ID единственного кандидата: {candidates[0]['id']}")
        return candidates[0]["id"]
    else:
        print(f"Возвращаем список из {len(candidates)} кандидатов")
        return candidates