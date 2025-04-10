# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import pytz
import base64
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from io import BytesIO
import os
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import re
import math # ceil 사용을 위해 추가

# --- 페이지 설정 ---
st.set_page_config(page_title="이삿날 스마트견적", layout="wide")

# --- 타이틀 ---
st.title("🚚 이삿날 스마트견적")

# --- 데이터 정의 ---
# < 통합: 차량 제원 >
vehicle_specs = {
    "1톤": {"capacity": 5, "weight_capacity": 1000},
    "2.5톤": {"capacity": 12, "weight_capacity": 2500},
    "3.5톤": {"capacity": 18, "weight_capacity": 3500},
    "5톤": {"capacity": 25, "weight_capacity": 5000},
    "6톤": {"capacity": 30, "weight_capacity": 6000},
    "7.5톤": {"capacity": 40, "weight_capacity": 7500},
    "10톤": {"capacity": 50, "weight_capacity": 10000},
    "15톤": {"capacity": 70, "weight_capacity": 15000},
    "20톤": {"capacity": 90, "weight_capacity": 20000},
}

# < 통합: 이사 유형별 차량 가격 및 기본 인원 >
vehicle_prices = {
    "가정 이사 🏠": {
        "1톤": {"price": 400000, "men": 2, "housewife": 0}, "2.5톤": {"price": 900000, "men": 2, "housewife": 1},
        "3.5톤": {"price": 950000, "men": 2, "housewife": 1}, "5톤": {"price": 1200000, "men": 3, "housewife": 1},
        "6톤": {"price": 1350000, "men": 3, "housewife": 1}, "7.5톤": {"price": 1750000, "men": 4, "housewife": 1},
        "10톤": {"price": 2300000, "men": 5, "housewife": 1}, "15톤": {"price": 2800000, "men": 6, "housewife": 1},
        "20톤": {"price": 3500000, "men": 8, "housewife": 1},
    },
    "사무실 이사 🏢": {
        "1톤": {"price": 400000, "men": 2}, "2.5톤": {"price": 650000, "men": 2},
        "3.5톤": {"price": 700000, "men": 2}, "5톤": {"price": 950000, "men": 3},
        "6톤": {"price": 1050000, "men": 3}, "7.5톤": {"price": 1300000, "men": 4},
        "10톤": {"price": 1700000, "men": 5}, "15톤": {"price": 2000000, "men": 6},
        "20톤": {"price": 2500000, "men": 8},
    }
}

# < 통합: 이사 유형별 품목 정의 >
item_definitions = {
    "가정 이사 🏠": {
        "가정품목": ["장롱", "더블침대", "서랍장(5단)", "화장대", "TV(75인치)", "책상&의자", "책장", "옷행거", "소파(3인용)", "장식장", "에어컨", "4도어 냉장고", "김치냉장고(스탠드형)", "식탁(4인)", "주방용 선반(수납장)", "세탁기 및 건조기"],
        "기타품목": ["피아노(일반)", "피아노(디지털)", "안마기", "스타일러스", "신발장", "화분", "여행가방 및 캐리어"]
    },
    "사무실 이사 🏢": {
        "사무실품목": ["중역책상", "책상&의자", "서랍장(5단)", "4도어 냉장고", "TV(75인치)", "장식장", "에어컨", "오디오 및 스피커"],
        "기타품목": ["안마기", "공기청정기", "화분", "스타일러스", "신발장"]
    }
}

# < 품목 정보 (부피, 무게) >
items = {
    "장롱": (1.05, 120.0), "싱글침대": (1.20, 60.0), "더블침대": (1.70, 70.0), "돌침대": (2.50, 150.0),
    "옷장": (1.05, 160.0), "서랍장(3단)": (0.40, 30.0), "서랍장(5단)": (0.75, 40.0), "화장대": (0.32, 80.0),
    "중역책상": (1.20, 80.0), "책장": (0.96, 56.0), "책상&의자": (0.25, 40.0), "옷행거": (0.35, 40.0),
    "소파(1인용)": (0.40, 30.0), "소파(3인용)": (0.60, 50.0), "소파 테이블": (0.65, 35.0),
    "TV(45인치)": (0.15, 15.0), "TV(75인치)": (0.30, 30.0), "장식장": (0.75, 40.0),
    "오디오 및 스피커": (0.10, 20.0), "에어컨": (0.15, 30.0), "피아노(일반)": (1.50, 200.0),
    "피아노(디지털)": (0.50, 50.0), "안마기": (0.90, 50.0), "공기청정기": (0.10, 8.0),
    "양문형 냉장고": (1.00, 120.0), "4도어 냉장고": (1.20, 130.0), "김치냉장고(스탠드형)": (0.80, 90.0),
    "김치냉장고(일반형)": (0.60, 60.0), "식탁(4인)": (0.40, 50.0), "식탁(6인)": (0.60, 70.0),
    "가스레인지 및 인덕션": (0.10, 10.0), "주방용 선반(수납장)": (1.10, 80.0),
    "세탁기 및 건조기": (0.50, 80.0), "신발장": (1.10, 60.0), "여행가방 및 캐리어": (0.15, 5.0),
    "화분": (0.20, 10.0), "스타일러스": (0.50, 20.0),
}

# < 기타 비용 정보 >
ladder_prices = { # 사다리차 비용
    "2~5층": {"5톤": 150000, "6톤": 180000, "7.5톤": 210000, "10톤": 240000},
    "6~7층": {"5톤": 160000, "6톤": 190000, "7.5톤": 220000, "10톤": 250000},
    "8~9층": {"5톤": 170000, "6톤": 200000, "7.5톤": 230000, "10톤": 260000},
    "10~11층": {"5톤": 180000, "6톤": 210000, "7.5톤": 240000, "10톤": 270000},
    "12~13층": {"5톤": 190000, "6톤": 220000, "7.5톤": 250000, "10톤": 280000},
    "14층": {"5톤": 200000, "6톤": 230000, "7.5톤": 260000, "10톤": 290000},
    "15층": {"5톤": 210000, "6톤": 240000, "7.5톤": 270000, "10톤": 300000},
    "16층": {"5톤": 220000, "6톤": 250000, "7.5톤": 280000, "10톤": 310000},
    "17층": {"5톤": 230000, "6톤": 260000, "7.5톤": 290000, "10톤": 320000},
    "18층": {"5톤": 250000, "6톤": 280000, "7.5톤": 310000, "10톤": 340000},
    "19층": {"5톤": 260000, "6톤": 290000, "7.5톤": 320000, "10톤": 350000},
    "20층": {"5톤": 280000, "6톤": 310000, "7.5톤": 340000, "10톤": 370000},
    "21층": {"5톤": 310000, "6톤": 340000, "7.5톤": 370000, "10톤": 400000},
    "22층": {"5톤": 340000, "6톤": 370000, "7.5톤": 400000, "10톤": 430000},
    "23층": {"5톤": 370000, "6톤": 400000, "7.5톤": 430000, "10톤": 460000},
    "24층": {"5톤": 400000, "6톤": 430000, "7.5톤": 460000, "10톤": 490000},
}
special_day_prices = { # 이사 집중일 운영비
    "평일(일반)": 0, "이사많은날 🏠": 200000, "손없는날 ✋": 100000,
    "월말 📅": 100000, "공휴일 🎉": 100000,
}
long_distance_prices = { # 장거리 비용
    "선택 안 함": 0, "100km 이내": 200000, "200km 이내": 500000,
    "200km 초과": 700000, "제주": 1000000,
}
long_distance_options = list(long_distance_prices.keys()) # 장거리 옵션 목록

# < 상수 정의 >
ADDITIONAL_PERSON_COST = 200000 # 1인당 추가/할인 비용 기준 금액
WASTE_DISPOSAL_COST_PER_TON = 300000 # 톤당 폐기물 처리 비용
SKY_BASE_PRICE = 300000 # 스카이 기본 비용
SKY_EXTRA_HOUR_PRICE = 50000 # 스카이 시간당 추가 비용
STORAGE_DAILY_FEE_PER_TON = 7000 # 톤당 일일 보관료
LOADING_EFFICIENCY = 0.90 # 차량 적재 효율
METHOD_OPTIONS = ["사다리차 🪜", "승강기 🛗", "계단 🚶", "스카이 🏗️"] # 작업 방법 옵션

# --- 함수 정의 ---
def get_current_kst_time_str():
    """현재 한국 시간 문자열 반환"""
    try:
        kst = pytz.timezone("Asia/Seoul")
        return datetime.now(kst).strftime("%Y-%m-%d %H:%M")
    except pytz.UnknownTimeZoneError:
        st.warning("Asia/Seoul 타임존을 찾을 수 없음. 현재 시스템 시간 사용.", icon="⚠️")
        return datetime.now().strftime("%Y-%m-%d %H:%M")

def calculate_total_volume_weight(move_type):
    """선택된 품목의 총 부피와 무게 계산"""
    total_volume = 0
    total_weight = 0
    current_items_def = item_definitions.get(move_type, {})
    for section, item_list in current_items_def.items():
        for item_name in item_list:
            widget_key = f"qty_{move_type}_{section}_{item_name}"
            qty = st.session_state.get(widget_key, 0)
            if qty > 0 and item_name in items:
                volume, weight = items[item_name]
                total_volume += qty * volume
                total_weight += qty * weight
    return total_volume, total_weight

def recommend_vehicle(total_volume, total_weight):
    """총 부피와 무게를 바탕으로 차량 추천"""
    # < 개선: 통합된 vehicle_specs 사용 >
    sorted_vehicles = sorted(vehicle_specs.keys(), key=lambda x: vehicle_specs.get(x, {}).get("capacity", 0))
    for name in sorted_vehicles:
        spec = vehicle_specs.get(name)
        if spec:
            effective_capacity = spec["capacity"] * LOADING_EFFICIENCY
            if total_volume <= effective_capacity and total_weight <= spec["weight_capacity"]:
                remaining = ((effective_capacity - total_volume) / effective_capacity * 100) if effective_capacity > 0 else 0
                return name, remaining
    largest = sorted_vehicles[-1] if sorted_vehicles else None
    return f"{largest} 초과" if largest else "차량 정보 없음", 0

def get_ladder_range(floor):
    """층수에 따른 사다리차 가격 범위 반환"""
    try:
        f = int(floor)
        if f < 2: return None
        # < 개선: 범위 조건을 더 간결하게 표현 >
        ranges = {
            (2, 5): "2~5층", (6, 7): "6~7층", (8, 9): "8~9층", (10, 11): "10~11층",
            (12, 13): "12~13층", (14, 14): "14층", (15, 15): "15층", (16, 16): "16층",
            (17, 17): "17층", (18, 18): "18층", (19, 19): "19층", (20, 20): "20층",
            (21, 21): "21층", (22, 22): "22층", (23, 23): "23층", (24, float('inf')): "24층",
        }
        for (min_f, max_f), range_str in ranges.items():
            if min_f <= f <= max_f:
                return range_str
    except (ValueError, TypeError):
        return None
    return None

def get_vehicle_tonnage(vehicle_name):
    """차량 이름에서 톤수 추출 (숫자)"""
    if not vehicle_name or "초과" in vehicle_name:
        return 0
    try:
        # 정규 표현식으로 숫자(소수점 포함) 찾기
        match = re.findall(r'\d+\.?\d*', vehicle_name)
        return float(match[0]) if match else 0
    except Exception:
        return 0

def get_ladder_vehicle_size(vehicle_name):
    """차량 톤수에 따른 사다리차 적용 기준 반환"""
    tonnage = get_vehicle_tonnage(vehicle_name)
    if tonnage >= 10: return "10톤"
    if tonnage >= 7.5: return "7.5톤"
    if tonnage >= 6: return "6톤"
    if tonnage >= 5: return "5톤" # 기본값 또는 5톤 미만 차량 시
    # 5톤 미만 차량은 사다리차 비용 테이블에 없으므로, 정책에 따라 5톤 기준으로 하거나 별도 처리 필요
    # 여기서는 5톤 기준으로 처리
    return "5톤"

def calculate_boxes_baskets(vehicle_name):
    """차량 톤수에 따라 예상 박스/바구니 수량 계산"""
    tonnage = get_vehicle_tonnage(vehicle_name)
    if tonnage >= 10: return 55, 60
    if tonnage >= 7.5: return 45, 45
    if tonnage >= 5: return 35, 35
    if tonnage >= 2.5: return 25, 25
    # 2.5톤 미만 (예: 1톤)의 경우 기본값 또는 별도 정의 필요
    # 여기서는 1톤 기준을 임의로 추가 (필요시 수정)
    if tonnage >= 1: return 15, 15
    return 0, 0

def extract_phone_number_part(phone_str):
    """전화번호 문자열에서 마지막 4자리 숫자 추출"""
    if not phone_str: return "번호없음"
    cleaned = re.sub(r'\D', '', phone_str) # 숫자가 아닌 문자 제거
    return cleaned[-4:] if len(cleaned) >= 4 else "번호없음"

def generate_pdf(state_data, calculated_cost_items, total_cost):
    """PDF 견적서 생성 로직"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    font_path = "NanumGothic.ttf" # 시스템에 맞는 경로 또는 웹폰트 사용 고려
    font_registered = False
    try:
        if os.path.exists(font_path):
            pdfmetrics.registerFont(TTFont("NanumGothic", font_path))
            font_registered = True
        else: st.error(f"폰트 파일({font_path}) 없음. PDF에 한글이 깨질 수 있습니다.")
    except Exception as e: st.error(f"폰트 등록 오류: {e}")

    styles = getSampleStyleSheet()
    if font_registered:
        default_font = "NanumGothic"
        for style_name in styles.byName:
            try: styles[style_name].fontName = default_font
            except: pass
        styles['Title'].fontName = default_font
        styles['Heading1'].fontName = default_font
        styles['Heading2'].fontName = default_font
        styles['Normal'].fontName = default_font
        styles['Code'].fontName = default_font # 코드 스타일도 변경 (필요시)
    else:
        default_font = 'Helvetica' # Fallback font
        st.warning("한글 폰트가 등록되지 않아 PDF에서 한글이 깨질 수 있습니다.")

    normal_style = styles["Normal"]
    heading2_style = styles["Heading2"]
    title_style = styles["Title"]
    table_font_name = default_font
    table_bold_font_name = f"{default_font}-Bold" if font_registered else 'Helvetica-Bold'

    elements = []
    is_storage = state_data.get("is_storage_move", False)
    selected_vehicle_pdf = state_data.get("final_selected_vehicle") # 최종 선택된 차량 사용

    title = "보관이사 견적서" if is_storage else "이사 견적서"
    elements.append(Paragraph(title, title_style))
    elements.append(Spacer(1, 20))

    # --- PDF 내용 생성 ---
    # 1. 기본 정보
    elements.append(Paragraph("■ 기본 정보", heading2_style))
    elements.append(Spacer(1, 5))
    customer_name = state_data.get("customer_name", "")
    customer_phone = state_data.get("customer_phone", "")
    customer_display_name = customer_name or customer_phone or "미입력"
    to_location_label_pdf = "보관지" if is_storage else "도착지"
    basic_data = [
        ["고객명", customer_display_name], ["전화번호", customer_phone or "미입력"],
        ["이사일(출발)", str(state_data.get("moving_date", "미입력"))],
        ["출발지", state_data.get("from_location", "미입력")],
        [to_location_label_pdf, state_data.get("to_location", "미입력")],
    ]
    if is_storage:
        basic_data.append(["보관기간", f"{state_data.get('storage_duration', 1)}일"])
        basic_data.append(["최종 도착지", state_data.get("final_to_location", "미입력")])
    basic_data.append(["견적일", get_current_kst_time_str()])
    if state_data.get("apply_long_distance"):
        basic_data.append(["장거리", state_data.get("long_distance_selector", "미입력")])

    basic_table = Table(basic_data, colWidths=[100, 350])
    basic_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (0, 0), (-1, -1), "LEFT"),
        ('VALIGN', (0, 0), (-1, -1), "MIDDLE"),
        ('FONTNAME', (0, 0), (-1, -1), table_font_name),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6)
    ]))
    elements.append(basic_table); elements.append(Spacer(1, 12))

    # 2. 작업 정보
    elements.append(Paragraph("■ 작업 정보", heading2_style))
    elements.append(Spacer(1, 5))
    # <수정됨> 보관이사 시 '보관지 작업' 항목 제거 (층수/방법 입력이 없어졌으므로)
    to_work_label_pdf = "도착지 작업" # 일반 이사 기준 레이블
    work_data = [
        ["선택 차량", selected_vehicle_pdf or "미선택"],
        ["출발지 작업", f"{state_data.get('from_floor', '?')}층 ({state_data.get('from_method', '?')})"],
    ]
    # 보관이사가 아닐 경우에만 도착지 작업 정보 추가
    if not is_storage:
         work_data.append([to_work_label_pdf, f"{state_data.get('to_floor', '?')}층 ({state_data.get('to_method', '?')})"])
    # 보관이사일 경우 최종 도착지 정보 추가
    if is_storage:
        work_data.append(["최종 도착지 작업", f"{state_data.get('final_to_floor', '?')}층 ({state_data.get('final_to_method', '?')})"])

    # 기본 인원 정보 가져오기
    base_info_pdf = {}
    if selected_vehicle_pdf:
        base_move_cost_type_pdf = vehicle_prices.get(state_data.get('base_move_type'), {})
        base_info_pdf = base_move_cost_type_pdf.get(selected_vehicle_pdf, {"price": 0, "men": 0, "housewife": 0})

    base_men_pdf = base_info_pdf.get('men', 0)
    base_women_pdf = base_info_pdf.get('housewife', 0)
    base_personnel_str_pdf = f"남 {base_men_pdf}명" + (f", 여 {base_women_pdf}명" if base_women_pdf > 0 else "")
    work_data.append(["기본 인원", base_personnel_str_pdf])

    pdf_add_men = state_data.get('add_men', 0)
    pdf_add_women = state_data.get('add_women', 0)
    add_personnel_str_pdf = f"남 {pdf_add_men}명, 여 {pdf_add_women}명" if (pdf_add_men > 0 or pdf_add_women > 0) else "없음"
    work_data.append(["추가 인원", add_personnel_str_pdf])

    work_data.append(["예상 박스 수량", f"{state_data.get('final_box_count', 0)} 개"])
    work_data.append(["예상 바구니 수량", f"{state_data.get('final_basket_count', 0)} 개"])

    work_table = Table(work_data, colWidths=[100, 350])
    work_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (0, 0), (-1, -1), "LEFT"),
        ('VALIGN', (0, 0), (-1, -1), "MIDDLE"),
        ('FONTNAME', (0, 0), (-1, -1), table_font_name),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6)
    ]))
    elements.append(work_table); elements.append(Spacer(1, 12))

    # 3. 비용 상세 내역
    elements.append(Paragraph("■ 비용 상세 내역", heading2_style))
    elements.append(Spacer(1, 5))
    cost_data_pdf = [["항목", "금액", "비고"]]
    for item_row in calculated_cost_items:
        cost_data_pdf.append([str(col) for col in item_row]) # 모든 셀을 문자열로 변환
    cost_data_pdf.append(["총 견적 비용", f"{total_cost:,.0f}원", ""])

    cost_table = Table(cost_data_pdf, colWidths=[150, 100, 200])
    cost_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey), # Header row background
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey), # Footer row background
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (0, 0), (-1, -1), "LEFT"), # Default alignment
        ('ALIGN', (1, 1), (1, -1), "RIGHT"), # Align cost column right (except header)
        ('VALIGN', (0, 0), (-1, -1), "MIDDLE"),
        ('FONTNAME', (0, 0), (-1, -1), table_font_name),
        ('FONTNAME', (0, -1), (-1, -1), table_bold_font_name), # Bold font for total row
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(cost_table); elements.append(Spacer(1, 12))

    # 4. 특이 사항
    special_notes_text = state_data.get("special_notes", "")
    if special_notes_text:
        elements.append(Paragraph("■ 특이 사항", heading2_style))
        elements.append(Spacer(1, 5))
        # 줄바꿈 문자를 <br/> 태그로 변환하여 Paragraph에서 인식하도록 함
        elements.append(Paragraph(special_notes_text.replace('\n', '<br/>'), normal_style))
        elements.append(Spacer(1, 12))

    # --- PDF 빌드 ---
    try:
        doc.build(elements)
        pdf_data = buffer.getvalue()
        return pdf_data
    except Exception as e:
        st.error(f"PDF 빌드 오류: {e}")
        st.error("PDF 생성 중 문제가 발생했습니다. 입력 값이나 폰트 설정을 확인해주세요.")
        return None

# --- 세션 상태 초기화 ---
def initialize_session_state():
    """세션 상태 변수들 초기화"""
    defaults = {
        "base_move_type": "가정 이사 🏠",
        "is_storage_move": False,
        "apply_long_distance": False,
        "final_box_count": 0,
        "final_basket_count": 0,
        "remove_base_housewife": False,
        "customer_name": "", "customer_phone": "", "from_location": "", "to_location": "",
        "moving_date": datetime.now().date(), "from_floor": "", "from_method": METHOD_OPTIONS[0],
        "to_floor": "", "to_method": METHOD_OPTIONS[0], "special_notes": "",
        "storage_duration": 1, "final_to_location": "", "final_to_floor": "", "final_to_method": METHOD_OPTIONS[0],
        "long_distance_selector": long_distance_options[0],
        "vehicle_select_radio": "자동 추천 차량 사용",
        "manual_vehicle_select_value": None,
        "final_selected_vehicle": None, # < 추가: 최종 선택된 차량 저장용 >
        "sky_hours_from": 2, "sky_hours_final": 2, # <수정됨> 'to'를 'final'로 통일
        "add_men": 0, "add_women": 0,
        "has_waste_check": False, "waste_tons_input": 0.5,
        "date_opt_0_widget": False, "date_opt_1_widget": False, "date_opt_2_widget": False, "date_opt_3_widget": False,
        "total_volume": 0.0, # < 추가: 계산된 총 부피 저장용 >
        "total_weight": 0.0, # < 추가: 계산된 총 무게 저장용 >
        "recommended_vehicle_auto": None, # < 추가: 자동 추천 차량 저장용 >
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    # 이사 유형별 품목 수량 초기화
    current_move_type_init = st.session_state.base_move_type # Use a different name to avoid conflict
    current_items_def_init = item_definitions.get(current_move_type_init, {})
    for section, item_list in current_items_def_init.items():
        for item in item_list:
            widget_key = f"qty_{current_move_type_init}_{section}_{item}"
            if widget_key not in st.session_state:
                st.session_state[widget_key] = 0

# --- 메인 애플리케이션 로직 ---
initialize_session_state()

# < 현재 이사 유형 가져오기 >
current_move_type = st.session_state.base_move_type

# --- 탭 생성 ---
tab1, tab2, tab3 = st.tabs(["고객 정보", "물품 선택", "견적 및 비용"])

# --- 탭 1: 고객 정보 ---
with tab1:
    st.header("📝 고객 기본 정보")
    base_move_type_options = list(item_definitions.keys()) # ["가정 이사 🏠", "사무실 이사 🏢"]
    st.radio(
        "🏢 기본 이사 유형:", base_move_type_options,
        index=base_move_type_options.index(current_move_type),
        horizontal=True, key="base_move_type" # 직접 키 변경
    )
    col_check1, col_check2 = st.columns(2)
    with col_check1:
        st.checkbox("📦 보관이사 여부", key="is_storage_move")
    with col_check2:
        st.checkbox("🛣️ 장거리 이사 적용", key="apply_long_distance")

    col1, col2 = st.columns(2)
    with col1:
        st.text_input("👤 고객명", key="customer_name")
        st.text_input("📍 출발지", key="from_location")
        st.date_input("🚚 이사일 (출발일)", key="moving_date")
        if st.session_state.apply_long_distance:
            current_long_distance_value = st.session_state.get("long_distance_selector", long_distance_options[0])
            current_index = long_distance_options.index(current_long_distance_value) if current_long_distance_value in long_distance_options else 0
            st.selectbox("🛣️ 장거리 구간 선택", long_distance_options, index=current_index, key="long_distance_selector")
    with col2:
        st.text_input("📞 전화번호", key="customer_phone", placeholder="01012345678")
        to_location_label = "보관지" if st.session_state.is_storage_move else "도착지"
        st.text_input(f"📍 {to_location_label}", key="to_location")
        st.caption(f"⏱️ 견적일: {get_current_kst_time_str()}")

    st.divider()
    st.header("🏢 작업 조건")
    col3, col4 = st.columns(2)
    with col3:
        st.text_input("🔼 출발지 층수", key="from_floor", placeholder="예: 3")
        from_method_index = METHOD_OPTIONS.index(st.session_state.from_method) if st.session_state.from_method in METHOD_OPTIONS else 0
        st.selectbox("🛗 출발지 작업 방법", METHOD_OPTIONS, index=from_method_index, key="from_method")
    with col4:
        # <수정됨> 보관이사 시에는 '도착지(보관지)' 층수/방법 입력을 표시하지 않음
        if not st.session_state.is_storage_move:
            to_floor_label = "도착지 층수"
            to_method_label = "도착지 작업 방법"
            st.text_input(f"🔽 {to_floor_label}", key="to_floor", placeholder="예: 5")
            to_method_index = METHOD_OPTIONS.index(st.session_state.to_method) if st.session_state.to_method in METHOD_OPTIONS else 0
            st.selectbox(f"🛠️ {to_method_label}", METHOD_OPTIONS, index=to_method_index, key="to_method")
        else:
            st.info("보관이사 선택됨. 보관지 정보는 '보관이사 추가 정보'에서 입력하세요.", icon="ℹ️")


    if st.session_state.is_storage_move:
        st.divider()
        st.subheader("📦 보관이사 추가 정보")
        col5, col6 = st.columns(2)
        with col5:
            st.number_input("🗓️ 보관 기간 (일)", min_value=1, step=1, key="storage_duration")
            st.text_input("📍 최종 도착지 (입고지)", key="final_to_location")
        with col6:
            st.text_input("🔽 최종 도착지 층수 (입고지)", key="final_to_floor", placeholder="예: 10")
            final_to_method_index = METHOD_OPTIONS.index(st.session_state.final_to_method) if st.session_state.final_to_method in METHOD_OPTIONS else 0
            st.selectbox("🚚 최종 도착지 작업 방법 (입고지)", METHOD_OPTIONS, index=final_to_method_index, key="final_to_method")
        st.info("보관이사는 기본 이사 비용(차량+인원)이 2배로 적용되며, 일일 보관료 및 최종 도착지 작업 비용이 추가됩니다.", icon="ℹ️")

    st.divider()
    st.header("🗒️ 특이 사항 입력")
    st.text_area("특이 사항이 있으면 입력해주세요.", height=100, key="special_notes")

# --- 탭 2: 물품 선택 ---
with tab2:
    st.header("📋 품목 선택")
    st.caption(f"현재 선택된 기본 이사 유형: **{current_move_type}**")

    # < 개선: 함수를 사용하여 부피/무게 계산 및 세션 상태 업데이트 >
    st.session_state.total_volume, st.session_state.total_weight = calculate_total_volume_weight(current_move_type)
    st.session_state.recommended_vehicle_auto, remaining_space = recommend_vehicle(st.session_state.total_volume, st.session_state.total_weight)

    item_category_to_display = item_definitions.get(current_move_type, {})
    for section, item_list in item_category_to_display.items():
        with st.expander(f"{section} 선택"):
            cols = st.columns(2)
            num_items = len(item_list)
            items_per_col = math.ceil(num_items / 2) if num_items > 0 else 1
            for idx, item in enumerate(item_list):
                col_index = idx // items_per_col
                if col_index < len(cols):
                    with cols[col_index]:
                        if item in items:
                            unit = "칸" if item == "장롱" else "개"
                            widget_key = f"qty_{current_move_type}_{section}_{item}"
                            st.number_input(label=f"{item} ({unit})", min_value=0, step=1, key=widget_key)
                        else:
                            st.warning(f"'{item}' 품목 정보 없음") # Should not happen if data is consistent

    st.divider()
    st.subheader("📦 선택한 품목 정보 및 예상 물량")
    current_selection_display = {}
    for section, item_list_calc in item_category_to_display.items():
        for item_calc in item_list_calc:
            widget_key_calc = f"qty_{current_move_type}_{section}_{item_calc}"
            qty = st.session_state.get(widget_key_calc, 0)
            if qty > 0 and item_calc in items:
                unit_calc = "칸" if item_calc == "장롱" else "개"
                current_selection_display[item_calc] = (qty, unit_calc)

    if current_selection_display:
        cols_disp = st.columns(2)
        item_list_disp = list(current_selection_display.items())
        items_per_col_disp = math.ceil(len(item_list_disp) / 2) if len(item_list_disp) > 0 else 1
        for i, (item_disp, (qty_disp, unit_disp)) in enumerate(item_list_disp):
            col_idx_disp = i // items_per_col_disp
            if col_idx_disp < 2:
                with cols_disp[col_idx_disp]: st.write(f"**{item_disp}**: {qty_disp} {unit_disp}")

        st.subheader("🚚 추천 차량 정보")
        st.info(f"📊 총 부피: {st.session_state.total_volume:.2f} m³ | 총 무게: {st.session_state.total_weight:.2f} kg")
        recommended_vehicle_display = st.session_state.recommended_vehicle_auto
        if recommended_vehicle_display and "초과" not in recommended_vehicle_display:
            st.success(f"🚛 추천 차량: **{recommended_vehicle_display}** ({remaining_space:.1f}% 여유)")
            spec = vehicle_specs.get(recommended_vehicle_display)
            if spec:
                st.caption(f"({recommended_vehicle_display} 최대: {spec['capacity']}m³, {spec['weight_capacity']:,}kg)")
        elif recommended_vehicle_display and "초과" in recommended_vehicle_display:
                st.error(f"🚛 추천 차량: **{recommended_vehicle_display}**. 더 큰 차량 필요 또는 물량 조절 필요.")
        else:
            st.warning("🚛 추천 차량: 자동 추천 불가 (물량이 없거나 차량 정보 부족).")
    else:
        st.info("선택된 품목이 없습니다.")
        st.subheader("🚚 추천 차량 정보")
        st.info("📊 총 부피: 0.00 m³ | 총 무게: 0.00 kg")
        st.warning("🚛 추천 차량: 품목을 선택해주세요.")


# --- 탭 3: 견적 및 비용 ---
with tab3:
    st.header("💰 이사 비용 계산")
    is_storage = st.session_state.is_storage_move

    # --- 차량 선택 ---
    col_v1, col_v2 = st.columns([1, 2])
    with col_v1:
        st.radio(
            "차량 선택 방식:", ["자동 추천 차량 사용", "수동으로 차량 선택"],
            index=["자동 추천 차량 사용", "수동으로 차량 선택"].index(st.session_state.vehicle_select_radio),
            key="vehicle_select_radio"
        )

    # <변경됨> 차량 선택 로직: selected_vehicle_determined 지역 변수 사용 후 세션 상태 업데이트
    selected_vehicle_determined = None # 이 블록에서 결정될 차량 (지역 변수)
    recommended_vehicle_auto = st.session_state.recommended_vehicle_auto # 탭 2에서 계산된 추천 차량
    vehicle_prices_options = vehicle_prices.get(current_move_type, {})
    available_trucks = sorted(vehicle_prices_options.keys(), key=lambda x: vehicle_specs.get(x, {}).get("capacity", 0))

    with col_v2:
        use_auto = st.session_state.vehicle_select_radio == "자동 추천 차량 사용"
        valid_auto_recommendation = recommended_vehicle_auto and "초과" not in recommended_vehicle_auto and recommended_vehicle_auto in available_trucks

        if use_auto:
            if valid_auto_recommendation:
                selected_vehicle_determined = recommended_vehicle_auto
                st.success(f"자동 선택된 차량: **{selected_vehicle_determined}**")
                spec = vehicle_specs.get(selected_vehicle_determined)
                if spec:
                    st.caption(f"({selected_vehicle_determined} 최대: {spec['capacity']}m³, {spec['weight_capacity']:,}kg)")
                    st.caption(f"현재 물량: {st.session_state.total_volume:.2f} m³ ({st.session_state.total_weight:.2f} kg)")
            else:
                st.error(f"자동 추천 차량({recommended_vehicle_auto}) 사용 불가. 수동 선택 필요.")
                selected_vehicle_determined = None # 자동 추천 실패 시 선택 없음으로 설정

        # 수동 선택 모드이거나, 자동 추천이 유효하지 않은 경우
        if not use_auto or (use_auto and not valid_auto_recommendation):
            if not available_trucks:
                st.error("선택 가능한 차량 정보가 없습니다.")
                selected_vehicle_determined = None
            else:
                # 수동 선택 시 기본값 설정 (기존 선택값 > 자동추천값 > 첫번째 차량)
                default_manual_vehicle = st.session_state.manual_vehicle_select_value
                if default_manual_vehicle not in available_trucks:
                    if valid_auto_recommendation:
                        default_manual_vehicle = recommended_vehicle_auto
                    else:
                        default_manual_vehicle = available_trucks[0]

                current_manual_index = available_trucks.index(default_manual_vehicle) if default_manual_vehicle in available_trucks else 0

                # <수정됨> 수동 선택 selectbox가 변경될 때마다 selected_vehicle_determined가 업데이트됨
                selected_vehicle_determined = st.selectbox(
                    "🚚 차량 선택 (수동):", available_trucks,
                    index=current_manual_index,
                    key="manual_vehicle_select_value" # 이 key의 값이 변경되면 rerun됨
                 )
                st.info(f"수동 선택 차량: **{selected_vehicle_determined}**")
                spec = vehicle_specs.get(selected_vehicle_determined)
                if spec:
                    st.caption(f"({selected_vehicle_determined} 최대: {spec['capacity']}m³, {spec['weight_capacity']:,}kg)")
                    st.caption(f"현재 물량: {st.session_state.total_volume:.2f} m³ ({st.session_state.total_weight:.2f} kg)")

    # <변경됨> 결정된 차량을 세션 상태에 최종 저장 (이 시점의 값으로 이후 계산 수행)
    st.session_state.final_selected_vehicle = selected_vehicle_determined

    # <변경됨> 박스/바구니 수량 업데이트 시 final_selected_vehicle 사용
    final_vehicle_for_counts = st.session_state.final_selected_vehicle
    if final_vehicle_for_counts:
        st.session_state.final_box_count, st.session_state.final_basket_count = calculate_boxes_baskets(final_vehicle_for_counts)
    else:
        st.session_state.final_box_count, st.session_state.final_basket_count = 0, 0

    # --- 기타 옵션 ---
    st.divider()
    st.subheader("🛠️ 작업 및 추가 옵션")

    # 스카이 옵션
    uses_sky_from = st.session_state.get('from_method') == "스카이 🏗️"
    final_dest_method_key = 'final_to_method' if is_storage else 'to_method'
    uses_sky_final_to = st.session_state.get(final_dest_method_key) == "스카이 🏗️"
    if uses_sky_from or uses_sky_final_to:
        st.warning("스카이 작업 포함됨. 필요시 시간 조절.", icon="🏗️")
        col_sky1, col_sky2 = st.columns(2)
        if uses_sky_from:
            with col_sky1: st.number_input("출발지 스카이 시간 (기본 2시간)", min_value=2, step=1, key="sky_hours_from")
        # <수정됨> 보관 이사 시 최종 도착지에만 스카이 옵션 표시 (보관지 자체는 제외)
        if uses_sky_final_to and not (is_storage and final_dest_method_key == 'to_method'): # 'to_method'가 스카이면서 보관이사일 때는 최종 도착지가 아니므로 제외
            to_label_sky = "최종 도착지" if is_storage else "도착지"
            with col_sky2: st.number_input(f"{to_label_sky} 스카이 시간 (기본 2시간)", min_value=2, step=1, key="sky_hours_final")


    # 추가 인원 및 기본 여성 제외 옵션
    col_add1, col_add2 = st.columns(2)
    with col_add1:
        st.number_input("추가 남성 인원 👨", min_value=0, step=1, key="add_men")
    with col_add2:
        st.number_input("추가 여성 인원 👩", min_value=0, step=1, key="add_women")

    # 기본 여성 인원 제외 체크박스 (조건부 표시)
    # <변경됨> 체크박스 표시 여부 결정 시 final_selected_vehicle 사용
    base_women_count = 0
    show_remove_option = False
    final_vehicle_for_options = st.session_state.final_selected_vehicle
    if current_move_type == "가정 이사 🏠" and final_vehicle_for_options:
        base_info_for_check = vehicle_prices.get(current_move_type, {}).get(final_vehicle_for_options, {})
        base_women_count = base_info_for_check.get('housewife', 0)
        if base_women_count > 0:
            show_remove_option = True

    if show_remove_option:
        st.checkbox(f"기본 여성 인원({base_women_count}명) 제외하고 할인 적용 👩‍🔧 (-{ADDITIONAL_PERSON_COST:,}원)", key="remove_base_housewife")
    else:
        # 관련 없는 상태 초기화 (체크박스가 안보일 때)
        if st.session_state.remove_base_housewife:
            st.session_state.remove_base_housewife = False

    # 폐기물 처리 옵션
    col_waste1, col_waste2 = st.columns(2)
    with col_waste1:
        st.checkbox("폐기물 처리 필요 🗑️", key="has_waste_check")
    with col_waste2:
        if st.session_state.has_waste_check:
            st.number_input("폐기물 양 (톤)", min_value=0.5, max_value=10.0, step=0.5, key="waste_tons_input")
            st.caption(f"💡 1톤당 {WASTE_DISPOSAL_COST_PER_TON:,}원 추가")

    # 날짜 유형 선택
    st.subheader("📅 날짜 유형 선택 (중복 가능, 해당 시 할증)")
    date_options = ["이사많은날 🏠", "손없는날 ✋", "월말 📅", "공휴일 🎉"]
    selected_dates = []
    cols_date = st.columns(4)
    date_keys = ["date_opt_0_widget", "date_opt_1_widget", "date_opt_2_widget", "date_opt_3_widget"]
    for i, option in enumerate(date_options):
        if cols_date[i].checkbox(option, key=date_keys[i]):
            selected_dates.append(option)

    # --- 비용 계산 ---
    st.divider()
    st.subheader("💵 이사 비용 계산")

    total_cost = 0
    calculated_cost_items = []
    base_info_cost = {} # 비용 계산용 기본 정보 저장

    if selected_vehicle:
        # < 개선: 필요한 상태 값들을 지역 변수로 가져오기 >
        state = st.session_state
        add_men = state.add_men
        add_women = state.add_women
        remove_base_housewife = state.remove_base_housewife
        has_waste = state.has_waste_check
        waste_tons = state.waste_tons_input if has_waste else 0
        apply_long_dist = state.apply_long_distance
        long_dist_option = state.long_distance_selector
        storage_days = state.storage_duration

        # 1. 기본 비용
        base_move_cost_type = vehicle_prices.get(current_move_type, {})
        base_info_cost = base_move_cost_type.get(selected_vehicle, {"price": 0, "men": 0, "housewife": 0})
        base_cost_one_way = base_info_cost.get("price", 0)
        base_men_cost = base_info_cost.get('men', 0)
        base_women_cost = base_info_cost.get('housewife', 0)
        base_personnel_str = f"기본 남{base_men_cost}, 여{base_women_cost}"

        if is_storage:
            base_cost_calculated = base_cost_one_way * 2
            total_cost += base_cost_calculated
            calculated_cost_items.append(["기본 이사 비용 (보관x2)", f"{base_cost_calculated:,}원", f"{selected_vehicle} ({base_personnel_str})"])
        else:
            base_cost_calculated = base_cost_one_way
            total_cost += base_cost_calculated
            calculated_cost_items.append(["기본 이사 비용", f"{base_cost_calculated:,}원", f"{selected_vehicle} ({base_personnel_str})"])

        # 2. 장거리 추가 비용
        if apply_long_dist and long_dist_option != "선택 안 함":
            long_distance_cost = long_distance_prices.get(long_dist_option, 0)
            if long_distance_cost > 0:
                total_cost += long_distance_cost
                calculated_cost_items.append(["장거리 추가비용", f"{long_distance_cost:,}원", long_dist_option])

        # 3. 작업 비용 (사다리/스카이)
        # < 개선: 함수 활용 및 명확한 변수명 사용 >
        ladder_size = get_ladder_vehicle_size(selected_vehicle) # 사다리 비용 계산 기준

        # 출발지 작업 비용
        from_method = state.from_method
        from_floor_range = get_ladder_range(state.from_floor)
        if from_method == "사다리차 🪜" and from_floor_range:
            cost = ladder_prices.get(from_floor_range, {}).get(ladder_size, 0)
            if cost > 0: total_cost += cost; calculated_cost_items.append(["출발지 사다리차", f"{cost:,}원", f"{state.from_floor}층"])
        elif from_method == "스카이 🏗️":
            cost = SKY_BASE_PRICE + max(0, state.sky_hours_from - 2) * SKY_EXTRA_HOUR_PRICE
            total_cost += cost; calculated_cost_items.append(["출발지 스카이", f"{cost:,}원", f"{state.sky_hours_from}시간"])

        # 도착지(또는 최종 도착지) 작업 비용
        to_method_key = 'final_to_method' if is_storage else 'to_method'
        to_floor_key = 'final_to_floor' if is_storage else 'to_floor'
        to_hours_key = 'sky_hours_final' # 스카이 시간은 'final' 키 하나로 관리
        to_method = state[to_method_key]
        to_floor = state[to_floor_key]
        to_label = "최종 도착지" if is_storage else "도착지"
        to_floor_range = get_ladder_range(to_floor)

        if to_method == "사다리차 🪜" and to_floor_range:
            cost = ladder_prices.get(to_floor_range, {}).get(ladder_size, 0)
            if cost > 0: total_cost += cost; calculated_cost_items.append([f"{to_label} 사다리차", f"{cost:,}원", f"{to_floor}층"])
        elif to_method == "스카이 🏗️":
            cost = SKY_BASE_PRICE + max(0, state[to_hours_key] - 2) * SKY_EXTRA_HOUR_PRICE
            total_cost += cost; calculated_cost_items.append([f"{to_label} 스카이", f"{cost:,}원", f"{state[to_hours_key]}시간"])

        # 4. 보관료
        if is_storage:
            vehicle_ton_for_storage = get_vehicle_tonnage(selected_vehicle)
            if vehicle_ton_for_storage > 0:
                storage_fee = storage_days * STORAGE_DAILY_FEE_PER_TON * vehicle_ton_for_storage
                total_cost += storage_fee
                calculated_cost_items.append(["보관료", f"{storage_fee:,}원", f"{storage_days}일 ({selected_vehicle})"])
            else:
                calculated_cost_items.append(["보관료", "계산 오류", f"{selected_vehicle} 톤수 인식 불가?"])

        # 5. 추가 인원 비용 및 할인
        additional_men_cost_total = add_men * ADDITIONAL_PERSON_COST
        if additional_men_cost_total > 0:
            total_cost += additional_men_cost_total
            calculated_cost_items.append(["추가 남성 인원", f"{additional_men_cost_total:,}원", f"{add_men}명"])

        additional_women_cost_total = add_women * ADDITIONAL_PERSON_COST
        if additional_women_cost_total > 0:
            total_cost += additional_women_cost_total
            calculated_cost_items.append(["추가 여성 인원", f"{additional_women_cost_total:,}원", f"{add_women}명"])

        # 기본 여성 인원 제외 할인 (체크박스 값 사용)
        if remove_base_housewife and base_women_cost > 0: # base_women_cost는 위에서 계산됨
            discount_amount = ADDITIONAL_PERSON_COST # 할인액 = 1인 비용
            total_cost -= discount_amount
            calculated_cost_items.append(["기본 여성 인원 제외 할인", f"(-){discount_amount:,}원", "체크 시 적용"])
        elif remove_base_housewife and base_women_cost == 0:
             # 로직 오류 방지: 체크되었으나 할인 대상이 아닌 경우 상태 리셋
             st.session_state.remove_base_housewife = False

        # 6. 폐기물 처리 비용
        if has_waste and waste_tons > 0:
            waste_cost = waste_tons * WASTE_DISPOSAL_COST_PER_TON
            total_cost += waste_cost
            calculated_cost_items.append(["폐기물 처리", f"{waste_cost:,}원", f"{waste_tons}톤"])

        # 7. 날짜 할증 (이사 집중일 운영비)
        special_day_cost_total = sum(special_day_prices.get(date, 0) for date in selected_dates)
        if special_day_cost_total > 0:
            total_cost += special_day_cost_total
            cost_label = "이사 집중일 운영비"
            if len(selected_dates) == 1:
                cost_label = f"{selected_dates[0]} 운영비" # 더 명확한 레이블
            calculated_cost_items.append([cost_label, f"{special_day_cost_total:,}원", f"{', '.join(selected_dates)}"])

        # --- 비용 내역 표시 ---
        st.subheader("📊 비용 상세 내역")
        if calculated_cost_items:
            cost_df = pd.DataFrame(calculated_cost_items, columns=["항목", "금액", "비고"])
            # 금액 열을 오른쪽 정렬하고, 쉼표 서식 적용
            st.dataframe(cost_df.style.format({"금액": "{}"}).set_properties(**{'text-align': 'right'}, subset=['금액']), use_container_width=True)
            # st.table(cost_df.style.format({"금액": "{}"})) # 이전 방식
        else:
            st.info("계산된 비용 항목이 없습니다.")

        st.subheader(f"💰 총 견적 비용: {total_cost:,.0f}원")

        if state.special_notes:
            st.subheader("📝 특이 사항")
            st.info(state.special_notes)
    else:
        st.warning("차량을 먼저 선택해주세요.")

    # --- PDF 견적서 생성 기능 ---
    st.divider()
    st.subheader("📄 견적서 다운로드")
    can_generate_pdf = selected_vehicle and (st.session_state.customer_name or st.session_state.customer_phone)

    if st.button("PDF 견적서 생성", disabled=not can_generate_pdf, key="pdf_generate_button"):
        if not selected_vehicle:
            st.error("PDF 생성을 위해 차량을 선택해주세요.")
        elif not (st.session_state.customer_name or st.session_state.customer_phone):
            st.error("PDF 생성을 위해 고객명 또는 전화번호를 입력해주세요.")
        else:
            # < 개선: 함수 호출로 변경 >
            pdf_data = generate_pdf(st.session_state.to_dict(), calculated_cost_items, total_cost) # 세션 상태 전체를 딕셔너리로 전달

            if pdf_data:
                b64_pdf = base64.b64encode(pdf_data).decode("utf-8")
                phone_part = extract_phone_number_part(st.session_state.customer_phone)
                file_prefix = "보관이사견적서" if is_storage else "이사견적서"
                file_name = f"{file_prefix}_{phone_part}_{datetime.now().strftime('%Y%m%d')}.pdf"
                href = f'<a href="data:application/octet-stream;base64,{b64_pdf}" download="{file_name}">📥 {file_prefix} 다운로드 ({file_name})</a>'
                st.markdown(href, unsafe_allow_html=True)

    elif not can_generate_pdf:
        st.caption("PDF를 생성하려면 고객명/전화번호 입력 및 차량 선택이 필요합니다.")
