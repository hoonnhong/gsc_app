"""
router.py - 메뉴 ID를 기반으로 동적으로 페이지 모듈을 불러오는 라우터 클래스
main.py에서 하드코딩된 import를 제거하고, 확장성을 높입니다.
"""
import importlib
from nicegui import ui

class PageRouter:
    # 메뉴 ID : (모듈 경로, 렌더링 함수명)
    ROUTE_MAP = {
        'dashboard': ('modules.dashboard.dashboard_page', 'render_page'),
        'accounting': ('modules.accounting_group.accounting.accounting_page', 'render_accounting_page'),
        'expense': ('modules.accounting_group.expense.expense_page', 'render_expense_page'),
        'instructor': ('modules.instructor_group.instructor.instructor_page', 'render_instructor_page'),
        'payment': ('modules.instructor_group.payment.payment_page', 'render_payment_page'),
        'settings': ('modules.settings.settings_page', 'render_settings_page'),
        'dev': ('modules.dev.dev_page', 'render_dev_page'),
        'work': ('modules.favorite_sites.work.work_page', 'render_work_page'),
        'others': ('modules.favorite_sites.others.others_page', 'render_others_page'),
        'notice': ('modules.notice.notice_page', 'render_notice_page')
    }

    @classmethod
    def load_page(cls, menu_id: str):
        """메뉴 ID에 해당하는 모듈을 동적으로 가져와 렌더링 함수를 실행합니다."""
        if menu_id not in cls.ROUTE_MAP:
            cls.render_not_found(menu_id)
            return

        module_path, func_name = cls.ROUTE_MAP[menu_id]
        
        try:
            # 동적 모듈 임포트
            module = importlib.import_module(module_path)
            render_func = getattr(module, func_name, None)
            
            if render_func:
                render_func()
            else:
                cls.render_error(menu_id, f"{func_name} 함수를 찾을 수 없습니다.")
        except ModuleNotFoundError:
            # 아직 모듈 파일이 생성되지 않은 경우 (개발 중)
            cls.render_construction(menu_id)
        except Exception as e:
            cls.render_error(menu_id, str(e))

    @staticmethod
    def render_not_found(menu_id):
        with ui.column().classes('w-full mt-20 items-center text-gray-500'):
            ui.icon('search_off', size='80px')
            ui.label('경로를 찾을 수 없습니다.').classes('text-2xl font-bold mt-4')
            ui.label(f"알 수 없는 메뉴 ID: '{menu_id}'").classes('text-gray-400 mt-2')

    @staticmethod
    def render_construction(menu_id):
        with ui.column().classes('w-full mt-20 items-center text-gray-400'):
            ui.icon('construction', size='80px')
            ui.label(f'[{menu_id}] 라우터에 등록되었으나 모듈 파일이 없습니다.').classes('text-xl font-bold mt-4')
            ui.label('개발 중인 기능입니다.').classes('text-lg mt-2')

    @staticmethod
    def render_error(menu_id, error_msg):
        with ui.column().classes('w-full mt-20 items-center text-red-500'):
            ui.icon('error_outline', size='80px')
            ui.label('페이지 렌더링 오류').classes('text-2xl font-bold mt-4')
            ui.label(error_msg).classes('text-lg mt-2')
            ui.label(f'메뉴: {menu_id}').classes('text-sm mt-2 text-gray-500')
