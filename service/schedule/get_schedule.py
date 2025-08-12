import os
from service.request.request_data import request
from dotenv import load_dotenv
from service.schedule.schedule_processing import process_data_to_text_for_teachers

load_dotenv()

def get_schedule(id, target_date):
    env_var = os.getenv("GET_SCHEDULE_FOR_TEACHER")
    request_url = env_var + str(id)
    data = request(request_url)   
    return process_data_to_text_for_teachers(data, target_date)