"""
auth.py - 사용자 인증 및 권한 확인 로직
세션 관리 및 DB 연동을 통한 로그인/로그아웃 처리를 담당합니다.
"""
from nicegui import app, ui
from core.db_manager import db
from core.utils import hash_sha256

def login(user_id, password):
    """사용자 아이디와 비밀번호를 확인하여 로그인을 처리합니다."""
    pwd_hash = hash_sha256(password)
    user = db.fetch_all("SELECT * FROM users WHERE user_id = ? AND user_pwd = ? AND is_active = 1", (user_id, pwd_hash))
    
    if user:
        u = user[0]
        app.storage.user.update({
            'user_id': u['user_id'],
            'user_name': u['user_name'],
            'role': u['role'],
            'authenticated': True
        })
        
        # 권한 정보 로드 (관리자는 모든 권한, 직원은 할당된 것만)
        if u['role'] == 'admin':
            app.storage.user['permissions'] = ['all']
        else:
            perms = db.fetch_all("SELECT menu_id FROM user_permissions WHERE user_id = ?", (u['user_id'],))
            app.storage.user['permissions'] = [p['menu_id'] for p in perms]
            
        return True
    return False

def logout():
    """로그아웃 처리 후 로그인 페이지로 이동합니다."""
    app.storage.user.clear()
    ui.open('/login')

def is_authenticated():
    """현재 사용자가 인증되었는지 확인합니다."""
    try:
        return app.storage.user.get('authenticated', False)
    except RuntimeError:
        return False

def has_permission(menu_id):
    """특정 메뉴에 대한 접근 권한이 있는지 확인합니다."""
    if app.storage.user.get('role') == 'admin':
        return True
    perms = app.storage.user.get('permissions', [])
    return menu_id in perms or 'all' in perms
