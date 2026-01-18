# Common utility functions
import datetime

def get_current_time_str() -> str:
    """현재 시간을 문자열로 반환"""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
