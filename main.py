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
from service.groups.get_faculty import display_faculties, find_faculty_by_choice
from service.groups.get_direction import display_directions, find_direction_by_choice
from service.groups.get_group import display_groups, find_group_by_choice
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()


@app.post("/webhook")
async def handler(request_data: AliceRequest):
    try:
        user_input = request_data.request.original_utterance.lower().strip()
        session = request_data.session
        nlu = request_data.request.nlu
        current_state = request_data.state.session or {}

        response = {
            "version": request_data.version,
            "session": session,
            "response": {"end_session": False, "text": ""},
            "session_state": current_state,
        }

        logger.info(
            f"Текущее состояние: {current_state.get('current_step')}, Ввод: {user_input}"
        )

        if (
            not user_input
            or session.get("new")
            or not current_state.get("current_step")
        ):
            response["response"][
                "text"
            ] = "Привет! Я помогу узнать расписание. Выберите тип расписания: преподаватель, аудитория или группа"
            response["session_state"] = {"current_step": "start"}
            return response

        if current_state.get("current_step") == "start":
            if "преподаватель" in user_input:
                response["response"]["text"] = "Назовите фамилию преподавателя"
                response["session_state"] = {"current_step": "waiting_teacher_name"}
                return response
            elif "аудитория" in user_input or "кабинет" in user_input:
                response["response"]["text"] = "Назовите номер аудитории"
                response["session_state"] = {"current_step": "waiting_room_number"}
                return response
            elif "группа" in user_input:
                try:
                    faculties_text = await display_faculties()
                    response["response"]["text"] = faculties_text
                    response["session_state"] = {
                        "current_step": "waiting_faculty_choice"
                    }
                    return response
                except Exception as e:
                    logger.error(f"Ошибка при получении факультетов: {e}")
                    response["response"][
                        "text"
                    ] = "Не удалось загрузить список факультетов. Попробуйте еще раз."
                    response["session_state"] = {"current_step": "start"}
                    return response
            else:
                response["response"][
                    "text"
                ] = "Пожалуйста, выберите тип расписания: преподаватель, аудитория или группа"
                return response

        if current_state.get("current_step") == "waiting_faculty_choice":
            if user_input.isdigit():
                try:
                    faculty_data = await find_faculty_by_choice(user_input)
                    if (
                        faculty_data
                        and isinstance(faculty_data, dict)
                        and faculty_data.get("id")
                    ):
                        faculty_id = faculty_data["id"]
                        directions_text = await display_directions(faculty_id)
                        response["response"]["text"] = directions_text
                        response["session_state"] = {
                            "current_step": "waiting_direction_choice",
                            "faculty_id": faculty_id,
                            "faculty_name": faculty_data.get("short_name", ""),
                        }
                        return response
                    else:
                        response["response"][
                            "text"
                        ] = "Не удалось выбрать факультет. Пожалуйста, выберите номер из списка."
                        return response
                except Exception as e:
                    logger.error(f"Ошибка при выборе факультета: {e}")
                    response["response"][
                        "text"
                    ] = "Произошла ошибка при выборе факультета. Попробуйте еще раз."
                    response["session_state"] = {"current_step": "start"}
                    return response
            else:
                response["response"][
                    "text"
                ] = "Пожалуйста, введите номер факультета цифрой."
                return response

        if current_state.get("current_step") == "waiting_direction_choice":
            if user_input.isdigit():
                faculty_id = current_state.get("faculty_id")
                if not faculty_id:
                    response["response"][
                        "text"
                    ] = "Ошибка: не найден факультет. Давайте начнем сначала."
                    response["session_state"] = {"current_step": "start"}
                    return response

                try:
                    direction_id = await find_direction_by_choice(
                        faculty_id, user_input
                    )

                    if direction_id and isinstance(direction_id, int):
                        groups_text = await display_groups(faculty_id, direction_id)
                        response["response"]["text"] = groups_text
                        response["session_state"] = {
                            "current_step": "waiting_group_choice",
                            "faculty_id": faculty_id,
                            "direction_id": direction_id,
                        }
                        return response
                    else:
                        response["response"][
                            "text"
                        ] = "Не удалось выбрать направление. Пожалуйста, выберите номер из списка."
                        return response
                except Exception as e:
                    logger.error(f"Ошибка при выборе направления: {e}")
                    response["response"][
                        "text"
                    ] = "Произошла ошибка при выборе направления. Попробуйте еще раз."
                    response["session_state"] = {"current_step": "start"}
                    return response
            else:
                response["response"][
                    "text"
                ] = "Пожалуйста, введите номер направления цифрой."
                return response

        if current_state.get("current_step") == "waiting_group_choice":
            if user_input.isdigit():
                faculty_id = current_state.get("faculty_id")
                direction_id = current_state.get("direction_id")

                if not faculty_id or not direction_id:
                    response["response"][
                        "text"
                    ] = "Ошибка: не найден факультет или направление. Давайте начнем сначала."
                    response["session_state"] = {"current_step": "start"}
                    return response

                try:
                    group_id = await find_group_by_choice(
                        faculty_id, direction_id, user_input
                    )

                    if group_id and isinstance(group_id, int):
                        response["session_state"] = {
                            "current_step": "waiting_date_for_group",
                            "entity_type": "group",
                            "entity_id": group_id,
                            "faculty_id": faculty_id,
                            "direction_id": direction_id,
                        }
                        response["response"][
                            "text"
                        ] = "Группа выбрана! На какой день нужно расписание?"
                        return response
                    else:
                        response["response"][
                            "text"
                        ] = "Не удалось выбрать группу. Пожалуйста, выберите номер из списка."
                        return response
                except Exception as e:
                    logger.error(f"Ошибка при выборе группы: {e}")
                    response["response"][
                        "text"
                    ] = "Произошла ошибка при выборе группы. Попробуйте еще раз."
                    response["session_state"] = {"current_step": "start"}
                    return response
            else:
                response["response"][
                    "text"
                ] = "Пожалуйста, введите номер группы цифрой."
                return response

        if current_state.get("current_step") == "waiting_date_for_group":
            try:
                entity_id = current_state.get("entity_id")

                if not entity_id:
                    response["response"][
                        "text"
                    ] = "Ошибка: не найден ID группы. Давайте начнем сначала."
                    response["session_state"] = {"current_step": "start"}
                    return response

                target_date = parse_date(nlu)
                if not target_date:
                    response["response"][
                        "text"
                    ] = 'Не поняла дату. Пожалуйста, укажите дату, например: "на завтра", "на понедельник" или конкретную дату.'
                    return response

                logger.info(f"Запрос расписания группы {entity_id} на {target_date}")
                schedule_text = await get_schedule(entity_id, target_date, "group")

                if (
                    not schedule_text
                    or schedule_text.startswith("Ошибка")
                    or schedule_text.startswith("На эту дату занятий не найдено")
                ):
                    response["response"][
                        "text"
                    ] = f"На {target_date} занятий для выбранной группы не найдено."
                else:
                    response["response"][
                        "text"
                    ] = f"Расписание группы на {target_date}:\n{schedule_text}"

                response["response"][
                    "text"
                ] += "\n\nМогу помочь с другим расписанием. Выберите: преподаватель, аудитория или группа"
                response["session_state"] = {"current_step": "start"}
                return response

            except Exception as e:
                logger.error(f"Ошибка при получении расписания группы: {e}")
                response["response"][
                    "text"
                ] = "Произошла ошибка при получении расписания. Попробуйте еще раз."
                response["session_state"] = {"current_step": "start"}
                return response

        if current_state.get("current_step") == "waiting_teacher_name":
            try:
                fio_dict = find_teacher(nlu)
                if not fio_dict or not any(
                    [
                        fio_dict.get("last_name"),
                        fio_dict.get("first_name"),
                        fio_dict.get("full_name"),
                    ]
                ):
                    response["response"][
                        "text"
                    ] = "Не нашла ФИО в запросе. Пожалуйста, назовите фамилию преподавателя еще раз."
                    return response
                else:
                    result = await get_teacher_id(fio_dict)
                    if not result:
                        response["response"][
                            "text"
                        ] = "Не нашла такого преподавателя. Пожалуйста, уточните фамилию."
                        return response
                    elif isinstance(result, list):
                        if not result:
                            response["response"][
                                "text"
                            ] = "Не нашла такого преподавателя"
                            return response
                        else:
                            choices = "Нашлось несколько преподавателей:\n"
                            for i, teacher in enumerate(result, 1):
                                name = teacher.get("full_name", f"Преподаватель {i}")
                                choices += f"{i}. {name}\n"
                            choices += "\nУкажите номер нужного преподавателя."
                            response["response"]["text"] = choices
                            response["session_state"] = {
                                "current_step": "waiting_teacher_choice",
                                "teacher_candidates": result,
                            }
                            return response
                    else:
                        response["session_state"] = {
                            "current_step": "waiting_date",
                            "entity_type": "teacher",
                            "entity_id": result,
                            "entity_info": fio_dict,
                        }
                        teacher_name = fio_dict.get("full_name", "преподавателя")
                        response["response"][
                            "text"
                        ] = f"На какой день нужно расписание для {teacher_name}?"
                        return response
            except Exception as e:
                logger.error(f"Ошибка при поиске преподавателя: {e}")
                response["response"][
                    "text"
                ] = "Произошла ошибка при поиске преподавателя. Попробуйте еще раз."
                response["session_state"] = {"current_step": "start"}
                return response

        if current_state.get("current_step") == "waiting_room_number":
            try:
                auditory_dict = find_auditory(nlu)
                if not auditory_dict or not auditory_dict.get("number"):
                    response["response"][
                        "text"
                    ] = "Не нашла номер аудитории в запросе. Пожалуйста, назовите номер аудитории еще раз."
                    return response
                else:
                    result = await get_cabinet_id(auditory_dict)
                    if not result:
                        response["response"][
                            "text"
                        ] = f'Не нашла аудиторию {auditory_dict["number"]}. Пожалуйста, уточните номер.'
                        return response
                    elif isinstance(result, list):
                        if not result:
                            response["response"][
                                "text"
                            ] = f'Не нашла аудиторию {auditory_dict["number"]}'
                            return response
                        else:
                            choices = "Нашлось несколько аудиторий:\n"
                            for i, cabinet in enumerate(result, 1):
                                name = cabinet.get("name", f"Аудитория {i}")
                                choices += f"{i}. {name}\n"
                            choices += "\nУкажите номер нужной аудитории."
                            response["response"]["text"] = choices
                            response["session_state"] = {
                                "current_step": "waiting_cabinet_choice",
                                "cabinet_candidates": result,
                            }
                            return response
                    else:
                        response["session_state"] = {
                            "current_step": "waiting_date",
                            "entity_type": "cabinet",
                            "entity_id": result,
                            "entity_info": auditory_dict,
                        }
                        response["response"][
                            "text"
                        ] = f'На какой день нужно расписание для аудитории {auditory_dict["number"]}?'
                        return response
            except Exception as e:
                logger.error(f"Ошибка при поиске аудитории: {e}")
                response["response"][
                    "text"
                ] = "Произошла ошибка при поиске аудитории. Попробуйте еще раз."
                response["session_state"] = {"current_step": "start"}
                return response

        if current_state.get("current_step") == "waiting_teacher_choice":
            if user_input.isdigit():
                index = int(user_input) - 1
                teacher_candidates = current_state.get("teacher_candidates", [])

                if 0 <= index < len(teacher_candidates):
                    selected_teacher = teacher_candidates[index]
                    teacher_id = selected_teacher.get("id")
                    response["session_state"] = {
                        "current_step": "waiting_date",
                        "entity_type": "teacher",
                        "entity_id": teacher_id,
                        "entity_info": selected_teacher,
                    }
                    response["response"][
                        "text"
                    ] = f'Выбран преподаватель: {selected_teacher.get("full_name", "")}. На какой день нужно расписание?'
                    return response
                else:
                    response["response"][
                        "text"
                    ] = "Неверный номер. Пожалуйста, выберите номер из списка."
                    return response
            else:
                response["response"][
                    "text"
                ] = "Пожалуйста, укажите номер преподавателя из списка."
                return response

        if current_state.get("current_step") == "waiting_cabinet_choice":
            if user_input.isdigit():
                index = int(user_input) - 1
                cabinet_candidates = current_state.get("cabinet_candidates", [])

                if 0 <= index < len(cabinet_candidates):
                    selected_cabinet = cabinet_candidates[index]
                    cabinet_id = selected_cabinet.get("id")
                    response["session_state"] = {
                        "current_step": "waiting_date",
                        "entity_type": "cabinet",
                        "entity_id": cabinet_id,
                        "entity_info": selected_cabinet,
                    }
                    response["response"][
                        "text"
                    ] = f'Выбрана аудитория: {selected_cabinet.get("name", "")}. На какой день нужно расписание?'
                    return response
                else:
                    response["response"][
                        "text"
                    ] = "Неверный номер. Пожалуйста, выберите номер из списка."
                    return response
            else:
                response["response"][
                    "text"
                ] = "Пожалуйста, укажите номер аудитории из списка."
                return response

        if current_state.get("current_step") == "waiting_date":
            try:
                entity_type = current_state.get("entity_type")
                entity_id = current_state.get("entity_id")
                entity_info = current_state.get("entity_info", {})

                if not entity_id:
                    response["response"][
                        "text"
                    ] = f"Ошибка: не найден ID {entity_type}. Давайте начнем сначала."
                    response["session_state"] = {"current_step": "start"}
                    return response

                target_date = parse_date(nlu)
                if not target_date:
                    response["response"][
                        "text"
                    ] = 'Не поняла дату. Пожалуйста, укажите дату, например: "на завтра", "на понедельник" или конкретную дату.'
                    return response

                if entity_type == "teacher":
                    schedule_type = "teachers"
                    entity_name = entity_info.get("full_name", "преподавателя")
                else:
                    schedule_type = "cabinet"
                    entity_name = f'аудитории {entity_info.get("name", "")}'

                logger.info(
                    f"Запрос расписания {entity_type} {entity_id} на {target_date}"
                )
                schedule_text = await get_schedule(
                    entity_id, target_date, schedule_type
                )

                if (
                    not schedule_text
                    or schedule_text.startswith("Ошибка")
                    or schedule_text.startswith("На эту дату занятий не найдено")
                ):
                    response["response"][
                        "text"
                    ] = f"На {target_date} занятий не найдено."
                else:
                    response["response"][
                        "text"
                    ] = f"Расписание {entity_name} на {target_date}:\n{schedule_text}"

                response["response"][
                    "text"
                ] += "\n\nМогу помочь с другим расписанием. Выберите: преподаватель, аудитория или группа"
                response["session_state"] = {"current_step": "start"}
                return response

            except Exception as e:
                logger.error(f"Ошибка при получении расписания: {e}")
                response["response"][
                    "text"
                ] = "Произошла ошибка при получении расписания. Попробуйте еще раз."
                response["session_state"] = {"current_step": "start"}
                return response

        response["response"][
            "text"
        ] = "Что-то пошло не так. Давайте начнем заново. Выберите тип расписания: преподаватель, аудитория или группа"
        response["session_state"] = {"current_step": "start"}
        return response

    except Exception as e:
        logger.error(f"Критическая ошибка: {str(e)}")
        return {
            "response": {
                "text": "Произошла критическая ошибка. Попробуйте еще раз.",
                "end_session": False,
            },
            "session_state": {},
            "version": "1.0",
        }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
