from datetime import timedelta
import os
from service.request.request_data import request
from dotenv import load_dotenv
from service.schedule.schedule_processing import process_data_to_text_for_teachers
import logging

logger = logging.getLogger(__name__)

load_dotenv()


async def get_schedule(id, target_date):
    try:
        current_date = target_date
        start_of_current_week = current_date - timedelta(days=current_date.weekday())
        end_of_next_week = start_of_current_week + timedelta(days=13)
        start_date_str = start_of_current_week.strftime("%Y-%m-%d")
        end_date_str = end_of_next_week.strftime("%Y-%m-%d")
        env_var = os.getenv("GET_SCHEDULE_FOR_TEACHER")
        if not id:
            raise ValueError("Teacher ID is required")
        request_url = f"{env_var}?start_date={start_date_str}&end_date={end_date_str}&teacher={id}"
        print(f"Запрос расписания на 2 недели: {request_url}")
        data = await request(request_url)
        if isinstance(data, dict) and data.get("error"):
            raise Exception(f"API error: {data['error']}")
        return process_data_to_text_for_teachers(data, target_date)
    except Exception as e:
        logger.exception(f"Ошибка получения расписания: {str(e)}")
        return f"Ошибка при получении расписания: {str(e)}"
