from fastapi import FastAPI
import uvicorn
from schemas.Alice_Request import AliceRequest
from service.date.parse_date import parse_date
from service.teachers.find_teacher_by_name import find_teacher
from service.teachers.find_teacher_by_id import get_teacher_id
from service.schedule.get_schedule import get_schedule
import logging
from typing import Any, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = FastAPI()

def _extract_incoming_session_state(request_data: AliceRequest) -> Dict[str, Any]:
    state = {}
    raw = getattr(request_data, "__dict__", {})
    if "state" in raw and isinstance(raw["state"], dict):
        state = raw["state"].get("session", {}) if isinstance(raw["state"].get("session", {}), dict) else {}
        if state:
            return dict(state)

    session = getattr(request_data, "session", {}) or {}
    if isinstance(session, dict):
        if isinstance(session.get("session_state"), dict):
            return dict(session.get("session_state"))
        if isinstance(session.get("state"), dict):
            return dict(session.get("state"))
    return {}

@app.post('/webhook')
async def handler(request_data: AliceRequest):
    try:
        user_input = (request_data.request.original_utterance or "").lower().strip()
        nlu = request_data.request.nlu

        session_state = _extract_incoming_session_state(request_data)

        response = {
            "version": request_data.version,
            "session": request_data.session,
            "response": {
                "end_session": False,
                "text": ""
            },
            "session_state": session_state.copy()
        }

        if not user_input:
            response['response']['text'] = (
                'Привет, это голосовой помощник. '
                'Назовите тип расписания: преподаватель, аудитория или группа.'
            )
            return response

        if session_state.get('awaiting_teacher_choice'):
            try:
                idx = int(user_input.split()[0])
                candidates = session_state.get('teacher_candidates', [])
                if 1 <= idx <= len(candidates):
                    chosen = candidates[idx - 1]
                    teacher_id = chosen.get('id') or chosen.get('teacher_id') or chosen.get('pk')
                    session_state.pop('awaiting_teacher_choice', None)
                    session_state.pop('teacher_candidates', None)
                    response['session_state'] = session_state.copy()

                    target_date = parse_date(nlu)
                    if not target_date:
                        session_state['selected_teacher_id'] = teacher_id
                        session_state['awaiting_date'] = True
                        response['session_state'] = session_state.copy()
                        response['response']['text'] = 'Укажите дату (например: завтра или 25 сентября).'
                        return response
                    schedule_text = await get_schedule(teacher_id, target_date)
                    response['response']['text'] = schedule_text or 'Расписание не найдено.'
                    return response
                else:
                    response['response']['text'] = 'Неверный номер. Пожалуйста, укажите номер из списка.'
                    return response
            except ValueError:
                response['response']['text'] = 'Ожидался номер. Повторите, пожалуйста, цифрой.'
                return response

        if session_state.get('awaiting_date'):
            teacher_id = session_state.get('selected_teacher_id')
            target_date = parse_date(nlu)
            if not target_date:
                response['response']['text'] = 'Не распознал дату. Укажите дату снова (например: завтра).'
                return response
            session_state.pop('awaiting_date', None)
            session_state.pop('selected_teacher_id', None)
            response['session_state'] = session_state.copy()
            schedule_text = await get_schedule(teacher_id, target_date)
            response['response']['text'] = schedule_text or 'Расписание не найдено.'
            return response

        fio_dict = find_teacher(nlu)
        if not fio_dict:
            session_state['awaiting_teacher_name'] = True
            response['session_state'] = session_state.copy()
            response['response']['text'] = 'Не нашла ФИО в запросе. Назовите имя преподавателя, пожалуйста.'
            return response

        result = await get_teacher_id(fio_dict)
        if not result:
            response['response']['text'] = 'Не нашла такого преподавателя.'
            return response

        if isinstance(result, list):
            if not result:
                response['response']['text'] = 'Не нашла такого преподавателя.'
                return response
            choices = "Нашлось несколько преподавателей:\n"
            for i, teacher in enumerate(result, 1):
                name = teacher.get('full_name') or teacher.get('name') or f'Преподаватель {i}'
                choices += f"{i}. {name}\n"
            choices += "\nУкажите номер нужного преподавателя."
            session_state['teacher_candidates'] = result
            session_state['awaiting_teacher_choice'] = True
            response['session_state'] = session_state.copy()
            response['response']['text'] = choices
            return response

        teacher_id = result
        target_date = parse_date(nlu)
        if not target_date:
            session_state['selected_teacher_id'] = teacher_id
            session_state['awaiting_date'] = True
            response['session_state'] = session_state.copy()
            response['response']['text'] = 'Укажите дату, пожалуйста (например: завтра).'
            return response

        schedule_text = await get_schedule(teacher_id, target_date)
        response['response']['text'] = schedule_text or 'Расписание не найдено.'
        return response

    except Exception as e:
        logger.exception(f"Произошла ошибка: {str(e)}")
        return {
            "version": getattr(request_data, "version", "1.0"),
            "session": getattr(request_data, "session", {}),
            "response": {
                "end_session": True,
                "text": "Произошла ошибка"
            }
        }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
