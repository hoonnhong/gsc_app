"""
ai_helper.py - 제미나이 AI 연동 핵심 모듈
Gemini Pro API를 사용하여 메뉴 추천, 데이터 분석 등의 지능형 기능을 제공합니다.
"""

import google.generativeai as genai
import os
import json
from config import Config

class AIHelper:
    def _check_config(self):
        """API 키 설정을 다시 확인하고 모델을 초기화합니다."""
        from dotenv import load_dotenv
        load_dotenv(override=True)
        
        env_key = os.getenv("GEMINI_API_KEY")
        
        # 모델이 없거나 키가 변경된 경우 재설정
        if not hasattr(self, 'model') or self.model is None or self.api_key != env_key:
            self.api_key = env_key
            if self.api_key:
                try:
                    genai.configure(api_key=self.api_key)
                    # 사용자가 권장한 최신 프리뷰 모델 사용
                    self.model = genai.GenerativeModel('gemini-3.1-flash-lite-preview')
                    print(f"AI 모델 초기화 성공 (gemini-3.1-flash-lite-preview)")
                except Exception as e:
                    print(f"AI 모델 초기화 실패: {e}")
                    self.model = None
            else:
                self.model = None

    def get_menu_recommendation(self, label):
        """메뉴 라벨을 바탕으로 적절한 ID와 Material Icon을 추천합니다."""
        self._check_config()
        if not self.model:
            return None 

        prompt = f"""
        당신은 파이썬 NiceGUI 웹 앱 개발 전문가입니다.
        사용자가 입력한 메뉴 이름(라벨)에 가장 잘 어울리는 영문 ID(소문자 snake_case)와 
        Google Material Icons 이름을 추천해 주세요.
        
        입력 라벨: "{label}"
        
        반드시 다음 JSON 형식으로만 답변하세요:
        {{
            "id": "추천ID",
            "icon": "추천아이콘명"
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            return json.loads(text)
        except Exception as e:
            from nicegui import ui
            ui.notify(f"AI 추천 중 오류 발생: {str(e)}", type='negative')
            print(f"AI 추천 상세 오류: {str(e)}")
            return None

    def ask_gemini(self, prompt):
        """일반적인 질문에 대해 제미나이 응답을 반환합니다."""
        self._check_config()
        if not self.model:
            return "GEMINI_API_KEY가 설정되지 않았습니다."
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"오류 발생: {str(e)}"

# 싱글톤 인스턴스 생성
ai = AIHelper()
