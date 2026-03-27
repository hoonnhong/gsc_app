import re
import os
import base64

folder = 'e:/dev/gsc_app/modules/accounting_group/expense/지출품의서.files'
sheet1_path = os.path.join(folder, 'sheet001.htm')
css_path = os.path.join(folder, 'stylesheet.css')
img1_path = os.path.join(folder, 'image001.png')
img2_path = os.path.join(folder, 'image002.png')

with open(sheet1_path, 'r', encoding='cp949', errors='ignore') as f:
    html = f.read()

with open(css_path, 'r', encoding='cp949', errors='ignore') as f:
    css = f.read()

# CSS 인라인화
html = html.replace('<link rel=stylesheet href=stylesheet.css>', f'<style>{css}</style>')

# 이미지 Base64 인코딩
if os.path.exists(img1_path):
    with open(img1_path, 'rb') as f:
        img1_b64 = base64.b64encode(f.read()).decode('utf-8')
    html = html.replace('image001.png', f'data:image/png;base64,{img1_b64}')

if os.path.exists(img2_path):
    with open(img2_path, 'rb') as f:
        img2_b64 = base64.b64encode(f.read()).decode('utf-8')
    html = html.replace('image002.png', f'data:image/png;base64,{img2_b64}')

# 템플릿용 문자열 치환
# 타이틀
html = html.replace('2026년 3월급여', '{title}')
# 기안자
html = html.replace('황재홍', '{author}')
# 직급
html = html.replace('센터장', '{position}')
# 금액
html = html.replace('일금&nbsp;삼백삼십만구천오백팔십', '{amount_kr}')
html = html.replace('3,309,580', '{amount_num}')

# 날짜 (2026, 3, 25)
html = html.replace('>2026<', '>{year}<')
html = html.replace('>3<', '> {month} <')
html = html.replace('>25<', '> {day} <')
# Wait, let's be more specific with date

# 상세 내역
html = html.replace('>01<', '>{seq_1}<')
html = html.replace('>급여<', '>{summary_1}<')
html = html.replace('>26.03.25<', '>{date_1}<')
html = html.replace('>계좌이체<', '>{method_1}<')

with open('e:/dev/gsc_app/modules/accounting_group/expense/processed_template.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Saved to processed_template.html")
