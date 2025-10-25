from schemas.schedule import Schedule
import logging

logger = logging.getLogger(__name__)


def process_data_to_text_for_teachers(data, target_date):
    schedule_list = []
    try:
        schedule = Schedule.model_validate(data)
        target_date_str = str(target_date)
        for i, lesson in enumerate(schedule.data):
            lesson_date_str = str(lesson.date)
            if lesson_date_str == target_date_str:
                place_name = lesson.place.name if lesson.place else 'не указана'
                start_time = lesson.start_time.replace('-', ':')[:5]
                end_time = lesson.end_time.replace('-', ':')[:5]
                text = (
                    f"{lesson.number}, "
                    f"{lesson.type.short_name}, "
                    f"дисцип: {lesson.discipline.short_name}, "
                    f"группы: {', '.join([group.name for group in lesson.groups])}, "
                    f"ауд. {place_name}, "
                    f"время: {start_time}-{end_time}"
                )
                schedule_list.append(text)
    except Exception as e:
        logging.error(f"Ошибка обработки расписания для преподавателей: {e}")
        return f"Произошла ошибка при обработке расписания: {str(e)}"
    if schedule_list:
        return ' '.join(schedule_list)
    else:
        return "На эту дату занятий не найдено"


def process_data_to_text_for_cabinets(data, target_date):
    schedule_list = []
    try:
        schedule = Schedule.model_validate(data)
        target_date_str = str(target_date)
        for i, lesson in enumerate(schedule.data):
            lesson_date_str = str(lesson.date)
            if lesson_date_str == target_date_str:
                place_name = lesson.place.name if lesson.place else 'не указана'
                teachers_names = []
                for teacher in lesson.teachers:
                    if hasattr(teacher, 'full_name'):
                        teachers_names.append(teacher.full_name)
                    elif isinstance(teacher, dict) and 'full_name' in teacher:
                        teachers_names.append(teacher['full_name'])
                start_time = lesson.start_time.replace('-', ':')[:5]
                end_time = lesson.end_time.replace('-', ':')[:5]
                text = (
                    f"{lesson.number}. "
                    f"{lesson.type.short_name}, "
                    f"{lesson.discipline.short_name}, "
                    f"группы: {', '.join([group.name for group in lesson.groups])}, "
                    f"преп: {', '.join([teacher.short_name for teacher in lesson.teachers])}, "
                    f"ауд. {place_name}, "
                    f"время: {start_time}:{end_time}"
                )
                schedule_list.append(text)
    except Exception as e:
        logging.error(f"Ошибка обработки расписания для кабинетов: {e}")
        return f"Произошла ошибка при обработке расписания: {str(e)}"
    if schedule_list:
        return '\n'.join(schedule_list)
    else:
        return "На эту дату занятий не найдено"


async def out_readable_text(data, target_date, schedule_type):
    if schedule_type == "cabinet":
        return process_data_to_text_for_cabinets(data, target_date)
    elif schedule_type == "teacher":
        return process_data_to_text_for_teachers(data, target_date)
    else:
        pass
