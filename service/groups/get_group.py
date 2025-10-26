import os
from service.request.request_data import request
from dotenv import load_dotenv
from schemas.group import GroupList


async def get_groups_from_api(faculty_id, direction_id):
    try:
        load_dotenv()
        env_var = os.getenv("GET_GROUPS")
        request_url = f"{env_var}direction={direction_id}&faculty={faculty_id}"
        print(f"Запрос групп: {request_url}")
        data = await request(request_url)
        groups_data = GroupList.model_validate({"groups": data}).groups
        groups_dict = {}
        for group in groups_data:
            if group.id and group.name and group.course:
                groups_dict[group.id] = {
                    "name": group.name,
                    "course": group.course
                }
        return groups_dict
    except Exception as e:
        print(f"Ошибка при запросе данных групп: {e}")
        return {}


async def find_group_by_choice(faculty_id, direction_id, choice_number):
    groups_dict = await get_groups_from_api(faculty_id, direction_id)
    if not groups_dict:
        return None
    groups_list = list(groups_dict.items())
    try:
        choice_index = int(choice_number) - 1
        if 0 <= choice_index < len(groups_list):
            group_id, group_info = groups_list[choice_index]
            return group_id
        else:
            return f"Некорректный номер выбора: {choice_number}"
    except (ValueError, TypeError):
        print(f"Некорректный формат номера: {choice_number}")
        return None


async def display_groups(faculty_id, direction_id):
    groups_dict = await get_groups_from_api(faculty_id, direction_id)
    
    if not groups_dict:
        return "Не удалось получить список групп"
    result = "Доступные группы:\n"
    for i, (group_id, group_info) in enumerate(groups_dict.items(), 1):
        name = group_info["name"]
        course = group_info["course"]
        result += f"{i}. {name} ({course} курс)\n"
    result += "\nВыберите номер группы:"
    return result