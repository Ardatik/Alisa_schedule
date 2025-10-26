from service.request.request_data import request
import os
import re


def find_auditory(nlu):
    auditory_data = {}
    tokens = nlu.tokens
    for i, token in enumerate(tokens):
        if token.isdigit():
            number_parts = [token]
            j = i + 1
            while j < len(tokens):
                next_token = tokens[j]
                if (next_token.isalpha() and len(next_token) == 1) or next_token == "/":
                    number_parts.append(next_token)
                    j += 1
                else:
                    break
            auditory_data["number"] = "".join(number_parts).lower()
            auditory_data["original"] = " ".join(number_parts)
            break
        elif any(char.isdigit() for char in token):
            auditory_data["number"] = token.lower()
            auditory_data["original"] = token
            break
    return auditory_data


def match_cabinet(cabinet, auditory_data):
    if not cabinet.get("name") or not cabinet.get("id"):
        return None
    search_number = auditory_data.get("number", "").lower()
    cabinet_name = cabinet["name"].lower()
    cabinet_parts = cabinet_name.split()
    normalized_search = search_number.replace(" ", "")
    normalized_cabinet = cabinet_name.replace(" ", "")
    if normalized_search == normalized_cabinet:
        return {
            "id": cabinet["id"],
            "name": cabinet["name"],
            "size": cabinet.get("size"),
        }
    if normalized_search in normalized_cabinet:
        return {
            "id": cabinet["id"],
            "name": cabinet["name"],
            "size": cabinet.get("size"),
        }
    for part in cabinet_parts:
        if search_number == part.lower():
            return {
                "id": cabinet["id"],
                "name": cabinet["name"],
                "size": cabinet.get("size"),
            }
    return None


async def get_cabinets_from_api(search_param):
    try:
        env_var = os.getenv("GET_CABINETS")
        request_url = env_var + search_param
        data = await request(request_url)
        return (
            data.get("places", [])
        )
    except Exception as e:
        print(f"Ошибка при запросе данных аудиторий: {e}")
        return []


async def get_cabinet_id(auditory_data):
    if not auditory_data:
        return None
    search_number = auditory_data.get("number", "").lower()
    original_number = auditory_data.get("original", "").lower()
    print(f"Поиск аудитории: number='{search_number}', original='{original_number}'")
    if not search_number:
        return None
    cabinets = await get_cabinets_from_api(search_number)
    if not cabinets:
        print("Не найдено аудиторий в ответе API")
        return None
    print(f"API вернуло {len(cabinets)} аудиторий")
    candidates = []
    for cabinet in cabinets:
        candidate = match_cabinet(cabinet, auditory_data)
        if candidate:
            candidates.append(candidate)
    print(f"Найдено подходящих кандидатов: {len(candidates)}")
    if not candidates:
        return None
    elif len(candidates) == 1:
        cabinet_id = candidates[0]["id"]
        return cabinet_id
    else:
        return candidates
