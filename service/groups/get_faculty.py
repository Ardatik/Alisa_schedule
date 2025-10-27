import os
from service.request.request_data import request
from dotenv import load_dotenv
from schemas.faculty import FacultyList


async def get_faculties_from_api():
    try:
        load_dotenv()
        request_url = os.getenv("GET_FACULTIES")
        print(f"[DEBUG] Запрос факультетов: {request_url}")
        data = await request(request_url)
        faculties_data = FacultyList.model_validate({"faculties": data}).faculties
        faculties_dict = {}
        for faculty in faculties_data:
            if faculty.id and faculty.short_name and not faculty.inactive:
                faculties_dict[faculty.short_name] = faculty.id
                print(f"[DEBUG] Факультет: {faculty.short_name} (ID: {faculty.id})")
        return faculties_dict
    except Exception as e:
        print(f"Ошибка при запросе данных факультетов: {e}")
        return {}


async def find_faculty_by_choice(choice_number):
    faculties_dict = await get_faculties_from_api()
    
    if not faculties_dict:
        return None
    faculties_list = list(faculties_dict.items())
    try:
        choice_index = int(choice_number) - 1
        if 0 <= choice_index < len(faculties_list):
            short_name, faculty_id = faculties_list[choice_index]
            print(f"[DEBUG] Выбран факультет: {short_name} (ID: {faculty_id})")
            return {
                "id": faculty_id,
                "short_name": short_name
            }
        else:
            return f"Некорректный номер выбора: {choice_number}"
    except (ValueError, TypeError):
        print(f"Некорректный формат номера: {choice_number}")
        return None


async def display_faculties():
    faculties_dict = await get_faculties_from_api()
    if not faculties_dict:
        return "Не удалось загрузить список факультетов"
    faculties = faculties_dict.items()
    result = "Доступные факультеты:\n"
    for i, (short_name, faculty_id) in enumerate(faculties, 1):
        result += f"{i}. {short_name}\n"
    result += "\nВыберите номер факультета:"
    return result