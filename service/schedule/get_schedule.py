import os
from service.request.request_data import request
from dotenv import load_dotenv
from service.schedule.schedule_processing import process_data_to_text_for_teachers

load_dotenv()

async def get_schedule(id, target_date):
    try:
        env_var = os.getenv("GET_SCHEDULE_FOR_TEACHER")
        request_url = env_var + str(id)
        data = await request(request_url)   
        return process_data_to_text_for_teachers(data, target_date)
    except Exception as e:
        print(f"Ошибка получения расписания: {str(e)}")