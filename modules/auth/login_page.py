"""
login_page.py - 직원 로그인 화면
보안이 적용된 세션 기반 로그인을 처리하며, 깔끔한 카드 UI를 사용합니다.
"""
from nicegui import ui, app
from core.auth import login, is_authenticated
from core.ui_components import primary_button

def render_login_page():
    # 이미 로그인된 경우 메인으로 이동
    if is_authenticated():
        ui.open('/')
        return

    # 배경 그라데이션 및 레이아웃 설정
    with ui.column().classes('w-full min-h-screen items-center justify-center bg-blue-50/50'):
        # 로그인 카드 (그림자 및 라운드 강조)
        with ui.card().classes('w-full max-w-[400px] p-10 shadow-2xl rounded-3xl bg-white border border-gray-100'):
            with ui.column().classes('w-full items-center gap-2'):
                ui.icon('admin_panel_settings', size='72px').classes('text-primary mb-4')
                ui.label('GSC Integrated System').classes('text-3xl font-black text-gray-900 tracking-tight')
                ui.label('직원 통합 로그인').classes('text-lg font-medium text-gray-500 mb-6')
                
                # 입력 필드 (dense & outlined)
                user_id = ui.input('아이디').classes('w-full mb-2').props('outlined dense autofocus placeholder="아이디를 입력하세요"')
                password = ui.input('비밀번호').classes('w-full mb-6').props('outlined dense type="password" placeholder="비밀번호를 입력하세요"')
                
                # 로그인 실행 함수
                def handle_login():
                    if not user_id.value or not password.value:
                        ui.notify('아이디와 비밀번호를 모두 입력해 주세요.', type='warning')
                        return
                        
                    if login(user_id.value, password.value):
                        ui.notify(f'성공! {app.storage.user.get("user_name")}님 환영합니다.', type='positive')
                        ui.open('/') # 메인 페이지로 이동
                    else:
                        ui.notify('아이디 또는 비밀번호가 정확하지 않습니다.', type='negative')
                
                # 로그인 버튼 (전체 너비 강조)
                primary_button('로그인하기', on_click=handle_login).classes('w-full h-14 text-xl font-bold rounded-xl shadow-lg')
                
                with ui.row().classes('w-full justify-center mt-8 text-sm text-gray-400'):
                    ui.label('© 2026 GSC Business Group. All rights reserved.')
