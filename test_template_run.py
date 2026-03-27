
import os
import sys

# 현재 작업 디렉토리를 파이썬 경로에 추가
sys.path.append('E:/dev/gsc_app')

from modules.accounting_group.expense.template import generate_print_html

master = {
    'title': '테스트 품의서 제목',
    'author': '홍길동',
    'position': '과장',
    'approval_date': '2026-03-27',
    'total_amount': 500000,
    'total_amount_kr': '오십만',
    'note_text': '테스트 비고 내용입니다.\n두 번째 줄입니다.'
}

details = [
    {'summary': '사무용품 구입', 'date': '03-27', 'amount': 100000, 'method': '카드', 'note': '-'},
    {'summary': '식비', 'date': '03-27', 'amount': 50000, 'method': '현금', 'note': '점심'},
]

html = generate_print_html(master, details)
output_path = 'E:/dev/gsc_app/modules/accounting_group/expense/test_output.html'
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"Test HTML generated at {output_path}")
