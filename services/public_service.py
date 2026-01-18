# Public business logic
from modules.db_firestore import get_stats

def get_public_dashboard_stats():
    """공개용 통계 데이터 조회"""
    return get_stats()

def submit_application(data: dict):
    """신청서 제출"""
    # TODO: Implement submission to Firestore
    pass
