"""
expense_repo.py - 지출품의서 데이터베이스 처리 계층 (Repository)
UI 계층과 데이터 계층을 분리하고, 행 단위 최적화 쿼리를 사용합니다.
"""

from core.db_manager import db
import pandas as pd

def load_all_reports():
    """모든 지출결의서 데이터와 상세 내역을 로드합니다."""
    # 향후 완전한 SQL JOIN으로 변경 가능하나 현재는 get_df(Pandas) 활용 유지
    masters_df = db.get_df('expense_masters')
    details_df = db.get_df('expense_details')
    
    if masters_df.empty:
        return []
    
    reports = []
    for _, master_row in masters_df.iterrows():
        master_dict = master_row.to_dict()
        if not details_df.empty and 'master_id' in details_df.columns:
            m_id = master_dict.get('master_id')
            master_details = details_df[details_df['master_id'] == m_id].to_dict('records')
            master_dict['details'] = master_details
        else:
            master_dict['details'] = []
        reports.append(master_dict)
    
    # 내림차순 정렬 (최신 번호 상단)
    reports.sort(key=lambda x: str(x.get('master_id', '')), reverse=True)
    return reports

def get_new_master_id():
    """새로운 결의서 ID를 채번합니다."""
    # SQLite 직접 쿼리로 최대값 조회로 최적화 가능
    query = "SELECT master_id FROM expense_masters ORDER BY master_id DESC LIMIT 1"
    rows = db.fetch_all(query)
    
    if not rows:
        return "EXP-001"
        
    last_id = rows[0]['master_id']
    try:
        num = int(str(last_id).split('-')[1])
        return f"EXP-{num + 1:03d}"
    except:
        return "EXP-001"

def save_expense_report(master_data, details_data):
    """지출 결의서를 저장합니다. (Memory/Speed 최적화를 위해 행 단위 SQL 사용)"""
    try:
        # 1. 마스터 데이터 저장 (만약 테이블이 없으면 자동 생성이 안 되므로 기존 방식과 호환성 체크 필요)
        # SQLite 테이블 자동 생성 기능이 db_manager.py의 SQLite에는 없으므로,
        # 기존처럼 Pandas를 사용하되 전체 덮어쓰기가 아닌 1회 생성용으로 확인.
        # 현행 유지 관점을 반영해 여기서는 최초 1회 빈 테이블 처리를 우회함.
        
        # 임시 방편: 테이블이 있는지 확인 (fetch_all 시도로 에러나면 없는 것)
        if db.execute("SELECT 1 FROM expense_masters LIMIT 1") == -1:
             # 테이블이 없으면 pandas를 이용해 더미 구조 생성
             db.save_df(pd.DataFrame([master_data]), 'expense_masters')
             # 초기 생성 완료
             new_id = "EXP-001"
             master_data['master_id'] = new_id
             valid_details = []
             for d in details_data:
                 summary = d.get('summary', '').strip()
                 amount = int(d.get('amount', 0) or 0)
                 if summary or amount > 0:
                     d_copy = d.copy()
                     d_copy['master_id'] = new_id
                     valid_details.append(d_copy)
             if valid_details:
                 db.save_df(pd.DataFrame(valid_details), 'expense_details')
             return new_id
             
        # 이미 테이블이 있는 경우 (최적화 모드)
        new_id = get_new_master_id()
        master_data['master_id'] = new_id
        
        # Master INSERT
        if not db.insert_row('expense_masters', master_data):
            return "오류: 마스터 저장 실패"
            
        # Details INSERT
        for d in details_data:
            summary = d.get('summary', '').strip()
            amount = int(d.get('amount', 0) or 0)
            if summary or amount > 0:
                d_copy = d.copy()
                d_copy['master_id'] = new_id
                
                # 테이블이 없는 경우 대비
                if db.execute("SELECT 1 FROM expense_details LIMIT 1") == -1:
                    db.save_df(pd.DataFrame([d_copy]), 'expense_details')
                else:
                    db.insert_row('expense_details', d_copy)
                    
        return new_id
    except Exception as e:
        return f"오류: {e}"

def delete_expense_report(master_id):
    """문서 번호를 기준으로 결의서와 상세 내용을 삭제합니다."""
    db.delete_row('expense_masters', 'master_id = ?', (master_id,))
    db.delete_row('expense_details', 'master_id = ?', (master_id,))
    return True

def update_scan_path(master_id, path):
    """특정 문서의 스캔 파일 저장 경로를 업데이트합니다."""
    # 컬럼이 있는지 한 번 더 확인 (방어적 프로그래밍)
    cols = [r['name'] for r in db.fetch_all('PRAGMA table_info(expense_masters)')]
    if 'scan_file_path' not in cols:
        db.execute('ALTER TABLE expense_masters ADD COLUMN scan_file_path TEXT')
    
    return db.update_row('expense_masters', {'scan_file_path': path}, 'master_id = ?', (master_id,))
