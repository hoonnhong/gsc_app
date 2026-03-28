import hashlib

def hash_sha256(text: str) -> str:
    """텍스트를 SHA256으로 해싱하여 16진수 문자열로 반환합니다."""
    if not text:
        return ""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def to_korean_amount(num: int) -> str:
    """숫자 금액을 한글 표기법으로 변환합니다. (예: 1500000 -> 일금 일백오십만 원정)"""
    try:
        num_str = str(int(num))
    except (ValueError, TypeError):
        return ""
    
    if num_str == '0':
        return "영"
        
    num_chars = ["", "일", "이", "삼", "사", "오", "육", "칠", "팔", "구"]
    units = ["", "십", "백", "천"]
    big_units = ["", "만", "억", "조", "경"]
    
    result = []
    length = len(num_str)
    
    for i, digit_char in enumerate(num_str):
        digit = int(digit_char)
        if digit == 0:
            continue
            
        pos = length - i - 1
        unit_pos = pos % 4
        big_unit_pos = pos // 4
        
        result.append(num_chars[digit] + units[unit_pos])
        
        # 만, 억, 조 등의 큰 단위 처리
        if unit_pos == 0 and big_unit_pos > 0:
            # 해단 구간(4자리) 내에 숫자가 있는지 확인
            chunk_start = max(0, i - 3)
            chunk = num_str[chunk_start:i+1]
            if int(chunk) > 0:
                result.append(big_units[big_unit_pos])
                
    return "일금 " + "".join(result) + " 원정"

def format_date_str(date_str: str) -> str:
    """MM-DD 형식의 문자열을 M월 D일 형식으로 변환합니다."""
    d_val = str(date_str).strip()
    if '-' in d_val and '월' not in d_val:
        parts = d_val.split('-')
        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
            return f"{int(parts[0])}월 {int(parts[1])}일"
    return d_val

def get_print_javascript(iframe_id: str) -> str:
    """지정된 iframe ID의 콘텐츠를 새 창에 띄워 인쇄하는 JavaScript 템플릿을 반환합니다."""
    return f"""
    var iframe = document.getElementById('{iframe_id}');
    if (iframe && iframe.src.startsWith('data:')) {{
        var printWindow = window.open('', '', 'width=1000,height=1200');
        var b64 = iframe.src.split(',')[1];
        var bin = atob(b64);
        var u8 = new Uint8Array(bin.length);
        for (var i=0; i<bin.length; i++) u8[i] = bin.charCodeAt(i);
        var html = new TextDecoder('utf-8').decode(u8);
        printWindow.document.write(html);
        printWindow.document.close();
        printWindow.onload = function() {{ 
            setTimeout(function() {{ 
                printWindow.print(); 
                // Firefox 등 일부 브라우저는 print() 후 창이 닫히지 않을 수 있으므로 선택적 추가
                // printWindow.close(); 
            }}, 500);
        }};
    }}
    """
