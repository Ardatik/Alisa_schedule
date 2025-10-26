import os
from service.request.request_data import request
from dotenv import load_dotenv
from schemas.direction import DirectionList


async def get_directions_from_api(faculty_id):
    try:
        load_dotenv()
        env_var = os.getenv("GET_DIRECTION")
        request_url = env_var + str(faculty_id)
        print(request_url)
        data = await request(request_url)
        directions_data = DirectionList.model_validate({"directions": data}).directions
        directions_dict = {}
        for direction in directions_data:
            if direction.id and direction.name and direction.degree_study:
                directions_dict[direction.id] = {
                    "name": direction.name,
                    "degree_study": direction.degree_study,
                    "cipher": direction.cipher
                }
        print(f"Загружено {len(directions_dict)} направлений")
        return directions_dict
    except Exception as e:
        print(f"Ошибка при запросе данных направлений: {e}")
        return {}


async def find_direction_by_choice(faculty_id, choice_number):
    directions_dict = await get_directions_from_api(faculty_id)
    if not directions_dict:
        return None
    directions_list = list(directions_dict.items())
    try:
        choice_index = int(choice_number) - 1
        if 0 <= choice_index < len(directions_list):
            direction_id, direction_info = directions_list[choice_index]
            return direction_id
        else:
            print(f"Некорректный номер выбора: {choice_number}")
            return None
    except (ValueError, TypeError):
        print(f"Некорректный формат номера: {choice_number}")
        return None


async def display_directions(faculty_id):
    directions_dict = await get_directions_from_api(faculty_id)
    if not directions_dict:
        return "Не удалось загрузить список направлений"
    result = "Доступные направления:\n"
    for i, (direction_id, direction_info) in enumerate(directions_dict.items(), 1):
        name = direction_info["name"]
        degree = direction_info["degree_study"]
        cipher = direction_info["cipher"]
        result += f"{i}. {name} ({degree}) [{cipher}]\n"
    result += "\nВыберите номер направления:"
    return result
