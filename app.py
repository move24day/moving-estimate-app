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
# 차량 비용
office_vehicle_prices = {
    "1톤": {"price": 400000, "men": 2}, "2.5톤": {"price": 650000, "men": 2},
    "3.5톤": {"price": 700000, "men": 2}, "5톤": {"price": 950000, "men": 3},
    "6톤": {"price": 1050000, "men": 3}, "7.5톤": {"price": 1300000, "men": 4},
    "10톤": {"price": 1700000, "men": 5}, "15톤": {"price": 2000000, "men": 6},
    "20톤": {"price": 2500000, "men": 8},
}
home_vehicle_prices = {
    "1톤": {"price": 400000, "men": 2, "housewife": 0}, "2.5톤": {"price": 900000, "men": 2, "housewife": 1},
    "3.5톤": {"price": 950000, "men": 2, "housewife": 1}, "5톤": {"price": 1200000, "men": 3, "housewife": 1},
    "6톤": {"price": 1350000, "men": 3, "housewife": 1}, "7.5톤": {"price": 1750000, "men": 4, "housewife": 1},
    "10톤": {"price": 2300000, "men": 5, "housewife": 1}, "15톤": {"price": 2800000, "men": 6, "housewife": 1},
    "20톤": {"price": 3500000, "men": 8, "housewife": 1},
}
# 사다리 비용
ladder_prices = {
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
# 특별일 비용
special_day_prices = {
    "평일(일반)": 0, "이사많은날 🏠": 200000, "손없는날 ✋": 100000,
    "월말 📅": 100000, "공휴일 🎉": 100000,
}
# 추가 비용
additional_person_cost = 200000
waste_disposal_cost = 300000
sky_base_price = 300000
sky_extra_hour_price = 50000
storage_daily_fee = 7000 # 보관이사 5톤 기준 1일당 보관료

# 장거리 추가비용 (옵션명, 가격은 기존 코드와 동일)
long_distance_prices = {
    "선택 안 함": 0,
    "100km 이내": 200000,
    "200km 이내": 500000,
    "200km 초과": 700000,
    "제주": 1000000,
}
long_distance_options = list(long_distance_prices.keys()) # 옵션 리스트 생성

# 품목 데이터 (통합)
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

# 이사 유형별 품목 정의
home_items_def = {
    "가정품목": ["장롱", "더블침대", "서랍장(5단)", "화장대", "TV(75인치)", "책상&의자", "책장", "옷행거", "소파(3인용)", "장식장", "에어컨", "4도어 냉장고", "김치냉장고(스탠드형)", "식탁(4인)", "주방용 선반(수납장)", "세탁기 및 건조기"],
    "기타품목": ["피아노(일반)", "피아노(디지털)", "안마기", "스타일러스", "신발장", "화분", "여행가방 및 캐리어"]
}
office_items_def = {
    "사무실품목": ["중역책상", "책상&의자", "서랍장(5단)", "4도어 냉장고", "TV(75인치)", "장식장", "에어컨", "오디오 및 스피커"],
    "기타품목": ["안마기", "공기청정기", "화분", "스타일러스", "신발장"]
}


# 차량 용량
vehicle_capacity = {"1톤": 5, "2.5톤": 12, "3.5톤": 18, "5톤": 25, "6톤": 30,"7.5톤": 40, "10톤": 50, "15톤": 70, "20톤": 90,}
vehicle_weight_capacity = {"1톤": 1000, "2.5톤": 2500, "3.5톤": 3500, "5톤": 5000, "6톤": 6000,"7.5톤": 7500, "10톤": 10000, "15톤": 15000, "20톤": 20000,}
# 박스 부피
box_volumes = {"중대박스": 0.1875, "옷박스": 0.219, "중박스": 0.1}

# --- 함수 정의 ---
# 차량 추천
def recommend_vehicle(total_volume, total_weight):
    loading_efficiency = 0.90
    sorted_vehicles = sorted(vehicle_capacity.keys(), key=lambda x: vehicle_capacity.get(x, 0))
    for name in sorted_vehicles:
        if name in vehicle_capacity and name in vehicle_weight_capacity:
            effective_capacity = vehicle_capacity[name] * loading_efficiency
            if total_volume <= effective_capacity and total_weight <= vehicle_weight_capacity[name]:
                remaining = ((effective_capacity - total_volume) / effective_capacity * 100) if effective_capacity > 0 else 0
                return name, remaining
    largest = sorted_vehicles[-1] if sorted_vehicles else None
    return f"{largest} 초과" if largest else "차량 정보 없음", 0

# 사다리 층수 구간
def get_ladder_range(floor):
    try:
        f = int(floor)
        if f < 2: return None
        if 2 <= f <= 5: return "2~5층"
        if 6 <= f <= 7: return "6~7층"
        if 8 <= f <= 9: return "8~9층"
        if 10 <= f <= 11: return "10~11층"
        if 12 <= f <= 13: return "12~13층"
        if f == 14: return "14층"
        if f == 15: return "15층"
        if f == 16: return "16층"
        if f == 17: return "17층"
        if f == 18: return "18층"
        if f == 19: return "19층"
        if f == 20: return "20층"
        if f == 21: return "21층"
        if f == 22: return "22층"
        if f == 23: return "23층"
        if f >= 24: return "24층"
    except (ValueError, TypeError):
        return None
    return None

# 전화번호 추출 (파일명용)
def extract_phone_number_part(phone_str):
    if not phone_str: return "번호없음"
    cleaned = re.sub(r'\D', '', phone_str)
    return cleaned[-4:] if len(cleaned) >= 4 else "번호없음"

# --- 세션 상태 초기화 ---
# selected_items 와 additional_boxes 는 더 이상 사용하지 않음
# 각 품목 수량은 고유 key를 가진 number_input 위젯의 session_state 로 관리
if "base_move_type" not in st.session_state:
    st.session_state.base_move_type = "가정 이사 🏠"
if "is_storage_move" not in st.session_state:
    st.session_state.is_storage_move = False
if "apply_long_distance" not in st.session_state: # 장거리 적용 여부 추가
    st.session_state.apply_long_distance = False

# 기본 입력값 설정 (세션 상태 키 사용)
default_values = {
    "customer_name": "", "customer_phone": "", "from_location": "", "to_location": "",
    "moving_date": datetime.now().date(), "from_floor": "", "from_method": "사다리차 🪜",
    "to_floor": "", "to_method": "사다리차 🪜", "special_notes": "",
    "storage_duration": 1, "final_to_location": "", "final_to_floor": "", "final_to_method": "사다리차 🪜",
    # "long_distance": long_distance_options[0], # <<< 기존 키 주석 처리 또는 삭제
    "long_distance_selector": long_distance_options[0], # <<< 수정됨: 새로운 키와 기본값 설정 (오류 수정)
    "vehicle_select_radio": "자동 추천 차량 사용",
    "manual_vehicle_select_value": None,
    "sky_hours_from": 2,
    "sky_hours_final": 2,
    "add_men": 0,
    "add_women": 0,
    "remove_women": 0,
    "has_waste_check": False,
    "waste_tons_input": 0.5,
    "date_opt_0_widget": False, # 날짜 옵션 체크박스 상태
    "date_opt_1_widget": False,
    "date_opt_2_widget": False,
    "date_opt_3_widget": False,
}
for key, value in default_values.items():
    if key not in st.session_state:
        st.session_state[key] = value

# 이사 유형별 품목 리스트 생성 및 초기화 (세션 상태에 없으면 0으로)
item_category_to_init = home_items_def if st.session_state.base_move_type == "가정 이사 🏠" else office_items_def
for section, item_list in item_category_to_init.items():
    for item in item_list:
        widget_key = f"qty_{st.session_state.base_move_type}_{section}_{item}"
        if widget_key not in st.session_state:
            st.session_state[widget_key] = 0

# 작업 방법 옵션
method_options = ["사다리차 🪜", "승강기 🛗", "계단 🚶", "스카이 🏗️"]

# --- 탭 생성 ---
tab1, tab2, tab3 = st.tabs(["고객 정보", "물품 선택", "견적 및 비용"])

# --- 탭 1: 고객 정보 ---
with tab1:
    st.header("📝 고객 기본 정보")

    # 이사 유형 선택
    base_move_type_options = ["가정 이사 🏠", "사무실 이사 🏢"]
    st.session_state.base_move_type = st.radio(
        "🏢 기본 이사 유형:", base_move_type_options,
        index=base_move_type_options.index(st.session_state.base_move_type),
        horizontal=True, key="base_move_type_radio_widget"
    )

    # 보관이사 및 장거리 이사 여부
    col_check1, col_check2 = st.columns(2)
    with col_check1:
        st.checkbox("📦 보관이사 여부", key="is_storage_move_checkbox_widget")
    with col_check2:
        st.checkbox("🛣️ 장거리 이사 적용", key="apply_long_distance") # 'disabled' 속성 없음 (원래대로)


    col1, col2 = st.columns(2)
    with col1:
        st.text_input("👤 고객명", key="customer_name")
        st.text_input("📍 출발지", key="from_location")
        st.date_input("🚚 이사일 (출발일)", key="moving_date")
        # 장거리 이사 옵션 (체크 시 활성화)
        if st.session_state.apply_long_distance:
            # <<< 수정됨: 새로운 키("long_distance_selector")를 사용하여 현재 값과 인덱스 계산 (오류 수정) >>>
            current_long_distance_value = st.session_state.get("long_distance_selector", long_distance_options[0])
            current_index = 0
            if current_long_distance_value in long_distance_options:
                current_index = long_distance_options.index(current_long_distance_value)

            st.selectbox("🛣️ 장거리 구간 선택", long_distance_options,
                         index=current_index,         # <<< 수정됨 >>>
                         key="long_distance_selector") # <<< 수정됨: key 변경 (오류 수정) >>>

    with col2:
        st.text_input("📞 전화번호", key="customer_phone", placeholder="01012345678")
        to_location_label = "보관지" if st.session_state.is_storage_move else "도착지"
        st.text_input(f"📍 {to_location_label}", key="to_location")

        try:
            kst = pytz.timezone("Asia/Seoul")
            estimate_date = datetime.now(kst).strftime("%Y-%m-%d %H:%M")
        except pytz.UnknownTimeZoneError:
            estimate_date = datetime.now().strftime("%Y-%m-%d %H:%M")
            st.warning("Asia/Seoul 타임존을 찾을 수 없음.", icon="⚠️")
        st.caption(f"⏱️ 견적일: {estimate_date}")

    st.divider()
    st.header("🏢 작업 조건")

    col3, col4 = st.columns(2)
    with col3:
        st.text_input("🔼 출발지 층수", key="from_floor", placeholder="예: 3")
        from_method_index = method_options.index(st.session_state.from_method) if st.session_state.from_method in method_options else 0
        st.selectbox("🛗 출발지 작업 방법", method_options, index=from_method_index, key="from_method")

    with col4:
        to_floor_label = "보관지 층수" if st.session_state.is_storage_move else "도착지 층수"
        to_method_label = "보관지 작업 방법" if st.session_state.is_storage_move else "도착지 작업 방법"
        st.text_input(f"{'🏢' if st.session_state.is_storage_move else '🔽'} {to_floor_label}", key="to_floor", placeholder="예: 5")
        to_method_index = method_options.index(st.session_state.to_method) if st.session_state.to_method in method_options else 0
        st.selectbox(f"🛠️ {to_method_label}", method_options, index=to_method_index, key="to_method")

    if st.session_state.is_storage_move:
        st.divider()
        st.subheader("📦 보관이사 추가 정보")
        col5, col6 = st.columns(2)
        with col5:
            st.number_input("🗓️ 보관 기간 (일)", min_value=1, step=1, key="storage_duration")
            st.text_input("📍 최종 도착지 (입고지)", key="final_to_location")
        with col6:
            st.text_input("🔽 최종 도착지 층수 (입고지)", key="final_to_floor", placeholder="예: 10")
            final_to_method_index = method_options.index(st.session_state.final_to_method) if st.session_state.final_to_method in method_options else 0
            st.selectbox("🚚 최종 도착지 작업 방법 (입고지)", method_options, index=final_to_method_index, key="final_to_method")
        st.info("보관이사는 기본 이사 비용(차량+인원)이 2배로 적용되며, 일일 보관료 및 최종 도착지 작업 비용이 추가됩니다.", icon="ℹ️")

    st.divider()
    st.header("🗒️ 특이 사항 입력")
    st.text_area("특이 사항이 있으면 입력해주세요.", height=100, key="special_notes")

# --- 탭 2: 물품 선택 ---
with tab2:
    st.header("📋 품목 선택")
    st.caption(f"현재 선택된 기본 이사 유형: **{st.session_state.base_move_type}**")

    # 이사 유형에 맞는 품목 정의 선택
    item_category_to_display = home_items_def if st.session_state.base_move_type == "가정 이사 🏠" else office_items_def

    for section, item_list in item_category_to_display.items():
        with st.expander(f"{section} 선택"):
            # 2열로 변경
            cols = st.columns(2)
            num_items = len(item_list)
            # 2열 기준 분배
            items_per_col = math.ceil(num_items / 2)

            for idx, item in enumerate(item_list):
                col_index = idx // items_per_col
                if col_index < len(cols): # Ensure col_index is within bounds (0 or 1)
                    with cols[col_index]:
                        if item in items: # 전체 items 딕셔너리에 있는지 확인
                            volume, weight = items[item]
                            unit = "칸" if item == "장롱" else "개"
                            widget_key = f"qty_{st.session_state.base_move_type}_{section}_{item}"

                            # st.number_input 사용 (반응성 개선 및 상태 관리 용이)
                            # label 에 품목명 포함하여 보이도록 수정
                            st.number_input(
                                label=f"{item} ({unit})",
                                min_value=0,
                                step=1,
                                key=widget_key,
                                # value는 세션 상태에서 직접 관리되므로 명시적 설정 불필요
                            )
                        else:
                             with cols[col_index]:
                                 st.warning(f"'{item}' 품목 정보 없음") # 데이터 불일치 시 경고

    st.divider()
    st.subheader("📦 선택한 품목 정보 및 예상 물량")

    # 선택된 품목 및 총량 계산 (st.number_input의 세션 상태 직접 사용)
    current_selection_display = {}
    total_volume = 0
    total_weight = 0
    calculated_boxes = {"중대박스": 0, "옷박스": 0, "중박스": 0} # 박스 수량 동적 계산

    # 현재 이사 유형에 맞는 품목 리스트로 반복
    item_category_to_calculate = home_items_def if st.session_state.base_move_type == "가정 이사 🏠" else office_items_def
    for section, item_list_calc in item_category_to_calculate.items():
        for item_calc in item_list_calc:
            widget_key_calc = f"qty_{st.session_state.base_move_type}_{section}_{item_calc}"
            qty = st.session_state.get(widget_key_calc, 0) # 세션에서 수량 가져오기

            if qty > 0 and item_calc in items:
                volume_calc, weight_calc = items[item_calc]
                unit_calc = "칸" if item_calc == "장롱" else "개"
                current_selection_display[item_calc] = (qty, unit_calc)
                total_volume += qty * volume_calc
                total_weight += qty * weight_calc

                # 박스 자동 계산 (가정 이사 기준)
                if st.session_state.base_move_type == "가정 이사 🏠":
                    if item_calc == "장롱": calculated_boxes["중대박스"] += qty * 5
                    if item_calc == "서랍장(5단)": calculated_boxes["중박스"] += qty * 5
                    # 다른 품목에 대한 박스 계산 규칙 추가 가능

    # 박스 부피 추가
    for box_type, count in calculated_boxes.items():
        if count > 0:
            total_volume += box_volumes[box_type] * count

    if current_selection_display:
        # 선택 품목 2열 표시
        cols_disp = st.columns(2)
        item_list_disp = list(current_selection_display.items())
        items_per_col_disp = math.ceil(len(item_list_disp) / 2)

        for i, (item_disp, (qty_disp, unit_disp)) in enumerate(item_list_disp):
            col_idx_disp = i // items_per_col_disp
            if col_idx_disp < 2:
                 with cols_disp[col_idx_disp]:
                     # 글자 크기 조정 제거 (기본 크기 사용)
                     st.write(f"**{item_disp}**: {qty_disp} {unit_disp}")

        # 계산된 박스 표시
        st.subheader("📦 자동 계산된 박스")
        box_texts = [f"{b_name}: {b_count}개" for b_name, b_count in calculated_boxes.items() if b_count > 0]
        if box_texts:
            st.info(", ".join(box_texts))
        else:
            st.info("자동 계산된 박스가 없습니다.")


        st.subheader("🚚 추천 차량 정보")
        st.info(f"📊 총 부피: {total_volume:.2f} m³ | 총 무게: {total_weight:.2f} kg")
        recommended_vehicle, remaining_space = recommend_vehicle(total_volume, total_weight)
        st.success(f"🚛 추천 차량: **{recommended_vehicle}** ({remaining_space:.1f}% 여유)")
        if recommended_vehicle in vehicle_capacity:
              st.caption(f"({recommended_vehicle} 최대: {vehicle_capacity[recommended_vehicle]}m³, {vehicle_weight_capacity[recommended_vehicle]:,}kg)")

    else:
        st.info("선택된 품목이 없습니다.")
        st.subheader("🚚 추천 차량 정보")
        st.info("📊 총 부피: 0.00 m³ | 총 무게: 0.00 kg")
        st.warning("🚛 추천 차량: 품목을 선택해주세요.")
        recommended_vehicle = None # 추천 차량 없음

# --- 탭 3: 견적 및 비용 ---
with tab3:
    st.header("💰 이사 비용 계산")
    is_storage = st.session_state.is_storage_move

    # --- 차량 선택 ---
    # 현재 물품 기반 총량 재계산 (tab2와 동일한 로직)
    current_total_volume = 0
    current_total_weight = 0
    recalculated_boxes = {"중대박스": 0, "옷박스": 0, "중박스": 0}
    item_category_to_recalc = home_items_def if st.session_state.base_move_type == "가정 이사 🏠" else office_items_def
    for section_recalc, item_list_recalc in item_category_to_recalc.items():
        for item_recalc in item_list_recalc:
            widget_key_recalc = f"qty_{st.session_state.base_move_type}_{section_recalc}_{item_recalc}"
            qty_recalc = st.session_state.get(widget_key_recalc, 0)
            if qty_recalc > 0 and item_recalc in items:
                volume_recalc, weight_recalc = items[item_recalc]
                current_total_volume += qty_recalc * volume_recalc
                current_total_weight += qty_recalc * weight_recalc
                # 박스 재계산
                if st.session_state.base_move_type == "가정 이사 🏠":
                    if item_recalc == "장롱": recalculated_boxes["중대박스"] += qty_recalc * 5
                    if item_recalc == "서랍장(5단)": recalculated_boxes["중박스"] += qty_recalc * 5

    for box_type_recalc, count_recalc in recalculated_boxes.items():
        if count_recalc > 0:
            current_total_volume += box_volumes[box_type_recalc] * count_recalc

    tab3_recommended_vehicle, tab3_remaining_space = recommend_vehicle(current_total_volume, current_total_weight)

    col_v1, col_v2 = st.columns([1, 2])
    with col_v1:
        st.radio( # radio는 key를 사용하면 자동으로 상태 저장
            "차량 선택 방식:", ["자동 추천 차량 사용", "수동으로 차량 선택"],
            index=["자동 추천 차량 사용", "수동으로 차량 선택"].index(st.session_state.vehicle_select_radio),
            key="vehicle_select_radio", # 키 변경 및 위젯 접미사 제거
            horizontal=False
        )

    selected_vehicle = None
    with col_v2:
        vehicle_prices_options = home_vehicle_prices if st.session_state.base_move_type == "가정 이사 🏠" else office_vehicle_prices
        available_trucks = sorted(vehicle_prices_options.keys(), key=lambda x: vehicle_capacity.get(x, 0))

        if st.session_state.vehicle_select_radio == "자동 추천 차량 사용":
            if tab3_recommended_vehicle and "초과" not in tab3_recommended_vehicle and tab3_recommended_vehicle in available_trucks:
                selected_vehicle = tab3_recommended_vehicle
                st.success(f"추천 차량: **{selected_vehicle}**")
                if selected_vehicle in vehicle_capacity:
                    st.caption(f"({selected_vehicle} 최대: {vehicle_capacity[selected_vehicle]}m³, {vehicle_weight_capacity[selected_vehicle]:,}kg)")
                    st.caption(f"현재 물량: {current_total_volume:.2f} m³ ({current_total_weight:.2f} kg)")
            else:
                st.error(f"자동 추천 실패 또는 부적합: {tab3_recommended_vehicle}. 수동 선택 필요.")
                # 자동 추천 실패 시 수동 선택 활성화 (옵션)
                # st.session_state.vehicle_select_radio = "수동으로 차량 선택" # 이 줄을 활성화하면 자동으로 수동 모드로 전환

        # 수동 선택 모드 (자동 추천 실패 시 포함)
        if st.session_state.vehicle_select_radio == "수동으로 차량 선택" or (st.session_state.vehicle_select_radio == "자동 추천 차량 사용" and (not tab3_recommended_vehicle or "초과" in tab3_recommended_vehicle or tab3_recommended_vehicle not in available_trucks)):

            if st.session_state.manual_vehicle_select_value is None or st.session_state.manual_vehicle_select_value not in available_trucks:
                 # 유효한 수동 선택값이 없으면, 추천 차량(유효하다면) 또는 첫번째 차량으로 설정
                 if tab3_recommended_vehicle and "초과" not in tab3_recommended_vehicle and tab3_recommended_vehicle in available_trucks:
                     st.session_state.manual_vehicle_select_value = tab3_recommended_vehicle
                 elif available_trucks:
                     st.session_state.manual_vehicle_select_value = available_trucks[0]

            current_manual_index = 0
            if st.session_state.manual_vehicle_select_value in available_trucks:
                current_manual_index = available_trucks.index(st.session_state.manual_vehicle_select_value)

            # selectbox는 key를 사용하면 자동으로 session_state.manual_vehicle_select_value 업데이트
            selected_vehicle = st.selectbox("🚚 차량 선택 (수동):", available_trucks, index=current_manual_index, key="manual_vehicle_select_value") # 키 변경
            st.info(f"선택 차량: **{selected_vehicle}**")
            if selected_vehicle in vehicle_capacity:
                st.caption(f"({selected_vehicle} 최대: {vehicle_capacity[selected_vehicle]}m³, {vehicle_weight_capacity[selected_vehicle]:,}kg)")
                st.caption(f"현재 물량: {current_total_volume:.2f} m³ ({current_total_weight:.2f} kg)")


    # --- 기타 옵션 ---
    st.divider()
    st.subheader("🛠️ 작업 및 추가 옵션")

    # 스카이 사용 여부 및 시간
    uses_sky_from = st.session_state.get('from_method') == "스카이 🏗️"
    final_dest_method_key = 'final_to_method' if is_storage else 'to_method'
    uses_sky_final_to = st.session_state.get(final_dest_method_key) == "스카이 🏗️"

    if uses_sky_from or uses_sky_final_to:
        st.warning("스카이 작업 포함됨. 필요시 시간 조절.", icon="🏗️")
        col_sky1, col_sky2 = st.columns(2)
        if uses_sky_from:
            with col_sky1:
                st.number_input( # key 사용으로 상태 자동 관리
                    "출발지 스카이 시간", min_value=2, step=1, key="sky_hours_from"
                )
        if uses_sky_final_to:
            to_label = "최종 도착지" if is_storage else "도착지"
            with col_sky2:
                st.number_input( # key 사용으로 상태 자동 관리
                    f"{to_label} 스카이 시간", min_value=2, step=1, key="sky_hours_final"
                )

    # 추가 인원
    col_add1, col_add2, col_add3 = st.columns(3)
    with col_add1:
        st.number_input("추가 남성 인원 👨", min_value=0, step=1, key="add_men") # key 사용
    with col_add2:
        # 가정 이사일 때 기본 여성 1명은 차량 비용에 포함되므로, '추가' 여성은 0부터 시작
        st.number_input("추가 여성 인원 👩", min_value=0, step=1, key="add_women") # key 사용
    with col_add3:
       # 가정 이사이고 기본 여성 인원이 있을 때만 빼는 옵션 제공
       base_women_count = 0
       if st.session_state.base_move_type == "가정 이사 🏠" and selected_vehicle:
           base_women_count = home_vehicle_prices.get(selected_vehicle, {}).get('housewife', 0)

       if base_women_count > 0:
          st.number_input("빼는 여성 인원 🧑‍🔧", min_value=0, step=1, max_value=base_women_count, key="remove_women") # key 사용, 최대값은 기본 여성 인원
       else:
          st.caption("기본 여성 인원 없음")
          if "remove_women" in st.session_state: # 관련 없는 상태 초기화
               st.session_state.remove_women = 0


    # 폐기물 처리
    col_waste1, col_waste2 = st.columns(2)
    with col_waste1:
        st.checkbox("폐기물 처리 필요 🗑️", key="has_waste_check") # key 사용
    with col_waste2:
        if st.session_state.has_waste_check: # 체크 시에만 표시
            st.number_input("폐기물 양 (톤)", min_value=0.5, max_value=10.0, step=0.5, key="waste_tons_input") # key 사용
            st.caption("💡 1톤당 30만원 추가")


    # 날짜 유형 선택
    st.subheader("📅 날짜 유형 선택 (중복 가능, 해당 시 할증)")
    date_options = ["이사많은날 🏠", "손없는날 ✋", "월말 📅", "공휴일 🎉"]
    selected_dates = []
    cols_date = st.columns(4)
    # 각 체크박스가 key를 통해 세션 상태를 직접 업데이트
    if cols_date[0].checkbox(date_options[0], key="date_opt_0_widget"): selected_dates.append(date_options[0])
    if cols_date[1].checkbox(date_options[1], key="date_opt_1_widget"): selected_dates.append(date_options[1])
    if cols_date[2].checkbox(date_options[2], key="date_opt_2_widget"): selected_dates.append(date_options[2])
    if cols_date[3].checkbox(date_options[3], key="date_opt_3_widget"): selected_dates.append(date_options[3])


    # --- 비용 계산 ---
    st.divider()
    st.subheader("💵 이사 비용 계산")

    total_cost = 0
    calculated_cost_items = []
    base_info = {} # 기본 차량 정보 저장용

    if selected_vehicle:
        # 비용 계산 시 세션 상태에서 값을 직접 읽어옴
        additional_men_calc = st.session_state.add_men
        additional_women_calc = st.session_state.add_women
        remove_women_calc = st.session_state.remove_women
        has_waste_calc = st.session_state.has_waste_check
        waste_tons_calc = st.session_state.waste_tons_input if has_waste_calc else 0

        # 1. 기본 비용 (차량 + 기본 인원)
        base_move_cost_type = home_vehicle_prices if st.session_state.base_move_type == "가정 이사 🏠" else office_vehicle_prices
        base_info = base_move_cost_type.get(selected_vehicle, {"price": 0, "men": 0, "housewife": 0}) # housewife 기본값 추가
        base_cost_one_way = base_info.get("price", 0)

        # 빼는 여성 인원 비용 차감 (기본 비용 계산 전에 반영)
        if st.session_state.base_move_type == "가정 이사 🏠" and remove_women_calc > 0:
            # 기본 여성 인원이 있는 경우에만 차감 가능
            if base_info.get('housewife', 0) >= remove_women_calc:
                # 여기서 base_cost_one_way를 직접 줄이지 않고, 나중에 추가 인원 비용 계산시 반영
                pass # 실제 차감은 추가 인원 비용 계산 파트에서
            else:
                # 혹시 모를 오류 방지 (max_value 설정으로 이 경우는 거의 없음)
                st.warning(f"기본 여성 인원({base_info.get('housewife',0)}명)보다 많은 인원({remove_women_calc}명)을 뺄 수 없습니다.")
                remove_women_calc = base_info.get('housewife', 0) # 최대치로 조정


        # 기본 비용 적용 (보관 여부에 따라)
        if is_storage:
            base_cost_calculated = base_cost_one_way * 2
            total_cost += base_cost_calculated
            calculated_cost_items.append(["기본 이사 비용 (보관x2)", f"{base_cost_calculated:,}원", f"{selected_vehicle} (기본 남{base_info.get('men', 0)}, 여{base_info.get('housewife', 0)})"])
        else:
            base_cost_calculated = base_cost_one_way
            total_cost += base_cost_calculated
            calculated_cost_items.append(["기본 이사 비용", f"{base_cost_calculated:,}원", f"{selected_vehicle} (기본 남{base_info.get('men', 0)}, 여{base_info.get('housewife', 0)})"])


        # 1.5 장거리 추가 비용 (조건부 적용)
        # <<< 수정됨: 값을 가져올 때 새로운 key("long_distance_selector") 사용 (오류 수정) >>>
        selected_distance_calc = st.session_state.get("long_distance_selector", "선택 안 함")
        if st.session_state.apply_long_distance and selected_distance_calc != "선택 안 함":
            long_distance_cost_calc = long_distance_prices.get(selected_distance_calc, 0)
            if long_distance_cost_calc > 0:
                total_cost += long_distance_cost_calc
                calculated_cost_items.append(["장거리 추가비용", f"{long_distance_cost_calc:,}원", selected_distance_calc])


        # 2. 작업 비용 (사다리, 스카이)
        ladder_vehicle_size = "5톤" # 사다리 비용 기준 톤수 결정
        try:
            # selected_vehicle 에서 톤 숫자 추출
            vehicle_ton = float(re.findall(r'\d+\.?\d*', selected_vehicle)[0])
            if vehicle_ton >= 10: ladder_vehicle_size = "10톤"
            elif vehicle_ton >= 7.5: ladder_vehicle_size = "7.5톤"
            elif vehicle_ton >= 6: ladder_vehicle_size = "6톤"
            # 그 외는 기본 "5톤" 유지
        except:
            pass # 숫자 추출 실패 시 기본 "5톤" 유지

        # 출발지
        ladder_from_cost = 0; sky_from_cost = 0
        from_method = st.session_state.get('from_method')
        from_floor_range = get_ladder_range(st.session_state.get('from_floor'))
        if from_method == "사다리차 🪜" and from_floor_range:
            ladder_from_cost = ladder_prices.get(from_floor_range, {}).get(ladder_vehicle_size, 0)
            if ladder_from_cost > 0: total_cost += ladder_from_cost; calculated_cost_items.append(["출발지 사다리차", f"{ladder_from_cost:,}원", f"{st.session_state.get('from_floor')}층"])
        elif from_method == "스카이 🏗️":
            sky_from_cost = sky_base_price + max(0, st.session_state.sky_hours_from - 2) * sky_extra_hour_price # 세션 상태 값 사용
            total_cost += sky_from_cost; calculated_cost_items.append(["출발지 스카이", f"{sky_from_cost:,}원", f"{st.session_state.sky_hours_from}시간"])

        # 도착지 (또는 최종 도착지)
        ladder_to_cost = 0; sky_to_cost = 0
        to_method = st.session_state.get('final_to_method') if is_storage else st.session_state.get('to_method')
        to_floor = st.session_state.get('final_to_floor') if is_storage else st.session_state.get('to_floor')
        to_label = "최종 도착지" if is_storage else "도착지"
        to_floor_range = get_ladder_range(to_floor)

        if to_method == "사다리차 🪜" and to_floor_range:
            ladder_to_cost = ladder_prices.get(to_floor_range, {}).get(ladder_vehicle_size, 0)
            if ladder_to_cost > 0: total_cost += ladder_to_cost; calculated_cost_items.append([f"{to_label} 사다리차", f"{ladder_to_cost:,}원", f"{to_floor}층"])
        elif to_method == "스카이 🏗️":
            sky_to_cost = sky_base_price + max(0, st.session_state.sky_hours_final - 2) * sky_extra_hour_price # 세션 상태 값 사용
            total_cost += sky_to_cost; calculated_cost_items.append([f"{to_label} 스카이", f"{sky_to_cost:,}원", f"{st.session_state.sky_hours_final}시간"])

        # 3. 보관료
        if is_storage:
            storage_days = st.session_state.get("storage_duration", 1)
            # 보관료는 차량 톤수 * 일일 보관료로 계산 (여기서 에러 발생 가능성 확인 필요: selected_vehicle에서 톤수 추출 로직)
            try:
                vehicle_ton_for_storage = float(re.findall(r'\d+\.?\d*', selected_vehicle)[0])
                storage_fee = storage_days * storage_daily_fee * vehicle_ton_for_storage # <<< 수정됨: 톤수 직접 곱하기 >>>
                total_cost += storage_fee; calculated_cost_items.append(["보관료", f"{storage_fee:,}원", f"{storage_days}일 ({selected_vehicle})"]) # <<< 비고에 차량정보 추가 >>>
            except Exception as e:
                st.error(f"보관료 계산 중 오류: {e}")
                calculated_cost_items.append(["보관료", "계산 오류", f"{selected_vehicle} 톤수 인식 불가?"])


        # 4. 추가 인원 (세션 상태 값 사용) - 수정됨: 인원수 표시 개선
        # 기존 코드에서 additional_men_cost, additional_women_cost, remove_women_cost 는 갯수 자체가 아니라 비용이었음. 변수명 변경 및 로직 수정
        additional_men_count = st.session_state.add_men
        additional_women_count = st.session_state.add_women
        remove_women_count = st.session_state.remove_women

        # 추가 남성 비용
        additional_men_cost_total = additional_men_count * additional_person_cost
        if additional_men_cost_total > 0:
            total_cost += additional_men_cost_total
            calculated_cost_items.append(["추가 남성 인원", f"{additional_men_cost_total:,}원", f"{additional_men_count}명"])

        # 추가 여성 비용
        additional_women_cost_total = additional_women_count * additional_person_cost
        if additional_women_cost_total > 0:
             total_cost += additional_women_cost_total
             calculated_cost_items.append(["추가 여성 인원", f"{additional_women_cost_total:,}원", f"{additional_women_count}명"])

        # 빼는 여성 비용 (차감)
        removed_women_cost_total = remove_women_count * additional_person_cost
        if removed_women_cost_total > 0:
             # 기본 여성 인원이 있는 경우에만 비용 차감
             if base_info.get('housewife', 0) >= remove_women_count:
                 total_cost -= removed_women_cost_total # <<< 차감 적용 >>>
                 calculated_cost_items.append(["빼는 여성 인원(차감)", f"(-){removed_women_cost_total:,}원", f"{remove_women_count}명"])
             # (오류 방지 로직은 위에서 처리했으므로 여기선 불필요)


        # 5. 폐기물 (세션 상태 값 사용) - 변수명 수정 has_waste_cost -> has_waste_calc
        if has_waste_calc and waste_tons_calc > 0:
            waste_cost = waste_tons_calc * waste_disposal_cost
            total_cost += waste_cost; calculated_cost_items.append(["폐기물 처리", f"{waste_cost:,}원", f"{waste_tons_calc}톤"])

        # 6. 날짜 할증 (selected_dates 는 위젯에서 직접 계산됨)
        special_day_cost_factor = sum(special_day_prices.get(date, 0) for date in selected_dates)
        if special_day_cost_factor > 0:
            total_cost += special_day_cost_factor; calculated_cost_items.append(["이사 집중일 운영비", f"{special_day_cost_factor:,}원", f"{', '.join(selected_dates)}"])

        # --- 비용 내역 표시 ---
        st.subheader("📊 비용 상세 내역")
        if calculated_cost_items:
            cost_df = pd.DataFrame(calculated_cost_items, columns=["항목", "금액", "비고"])
            st.table(cost_df.style.format({"금액": "{}"}))
        else: st.info("계산된 비용 항목이 없습니다.")

        st.subheader(f"💰 총 견적 비용: {total_cost:,.0f}원") # <<< 소수점 제거 >>>

        if st.session_state.get("special_notes", ""):
            st.subheader("📝 특이 사항")
            st.info(st.session_state.get("special_notes", ""))
    else:
        st.warning("차량을 먼저 선택해주세요.")

    # --- PDF 견적서 생성 기능 ---
    st.divider()
    st.subheader("📄 견적서 다운로드")
    can_generate_pdf = selected_vehicle and (st.session_state.get("customer_name") or st.session_state.get("customer_phone"))
    if st.button("PDF 견적서 생성", disabled=not can_generate_pdf, key="pdf_generate_button"):
        if not selected_vehicle: st.error("PDF 생성을 위해 차량을 선택해주세요.")
        elif not (st.session_state.get("customer_name") or st.session_state.get("customer_phone")): st.error("PDF 생성을 위해 고객명 또는 전화번호를 입력해주세요.")
        else:
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            # --- PDF 내용 구성 시작 ---
            font_path = "NanumGothic.ttf" # 사용자 환경에 맞게 경로 수정 필요
            font_registered = False
            try:
                if os.path.exists(font_path):
                    pdfmetrics.registerFont(TTFont("NanumGothic", font_path))
                    font_registered = True
                else:
                    st.error(f"폰트 파일({font_path}) 없음. PDF에 한글이 깨질 수 있습니다.")
            except Exception as e:
                st.error(f"폰트 등록 오류: {e}")

            styles = getSampleStyleSheet()
            if font_registered:
                # 모든 기본 스타일에 한글 폰트 적용 시도
                for style_name in styles.byName:
                    try: styles[style_name].fontName = "NanumGothic"
                    except: pass
                # 특정 스타일 재정의 (예: 제목)
                styles['Title'].fontName = "NanumGothic"
                styles['Heading1'].fontName = "NanumGothic"
                styles['Heading2'].fontName = "NanumGothic"
                styles['Normal'].fontName = "NanumGothic"
            else:
                st.warning("한글 폰트가 등록되지 않아 PDF에서 한글이 깨질 수 있습니다.")


            elements = []

            # 1. 제목
            title = "보관이사 견적서" if is_storage else "이사 견적서"
            elements.append(Paragraph(title, styles["Title"]))
            elements.append(Spacer(1, 20))

            # 2. 기본 정보
            try: kst = pytz.timezone("Asia/Seoul"); estimate_date_pdf = datetime.now(kst).strftime("%Y-%m-%d %H:%M")
            except: estimate_date_pdf = datetime.now().strftime("%Y-%m-%d %H:%M")
            elements.append(Paragraph("■ 기본 정보", styles["Heading2"]))
            elements.append(Spacer(1, 5))
            customer_display_name = st.session_state.get("customer_name") or st.session_state.get("customer_phone") or "미입력"
            to_location_label_pdf = "보관지" if is_storage else "도착지"
            basic_data = [
                ["고객명", customer_display_name], ["전화번호", st.session_state.get("customer_phone", "미입력")],
                ["이사일(출발)", str(st.session_state.get("moving_date", "미입력"))],
                ["출발지", st.session_state.get("from_location", "미입력")],
                [to_location_label_pdf, st.session_state.get("to_location", "미입력")],
            ]
            if is_storage:
                basic_data.append(["보관기간", f"{st.session_state.get('storage_duration', 1)}일"])
                basic_data.append(["최종 도착지", st.session_state.get("final_to_location", "미입력")])
            basic_data.append(["견적일", estimate_date_pdf])
            # <<< 수정됨: PDF에 값을 표시할 때 새로운 key("long_distance_selector") 사용 (오류 수정) >>>
            basic_data.append(["장거리", st.session_state.get("long_distance_selector", "미입력")])
            basic_table = Table(basic_data, colWidths=[100, 350])
            basic_table.setStyle(TableStyle([('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),('GRID', (0, 0), (-1, -1), 1, colors.black),('ALIGN', (0, 0), (-1, -1), "LEFT"),('VALIGN', (0, 0), (-1, -1), "MIDDLE"),('FONTNAME', (0, 0), (-1, -1), styles["Normal"].fontName if font_registered else 'Helvetica'), ('BOTTOMPADDING', (0, 0), (-1, -1), 6),('TOPPADDING', (0, 0), (-1, -1), 6)])) # <<< 폰트 적용 수정 >>>
            elements.append(basic_table); elements.append(Spacer(1, 12))

            # 3. 작업 정보
            elements.append(Paragraph("■ 작업 정보", styles["Heading2"]))
            elements.append(Spacer(1, 5))
            to_work_label_pdf = "보관지 작업" if is_storage else "도착지 작업"
            work_data = [
                ["선택 차량", selected_vehicle if selected_vehicle else "미선택"],
                ["출발지 작업", f"{st.session_state.get('from_floor', '?')}층 ({st.session_state.get('from_method', '?')})"],
                [to_work_label_pdf, f"{st.session_state.get('to_floor', '?')}층 ({st.session_state.get('to_method', '?')})"],
            ]
            if is_storage:
                work_data.append(["최종 도착지 작업", f"{st.session_state.get('final_to_floor', '?')}층 ({st.session_state.get('final_to_method', '?')})"])
            # PDF 생성 시점의 세션 상태 값 사용
            pdf_add_men = st.session_state.get('add_men', 0)
            pdf_add_women = st.session_state.get('add_women', 0)
            pdf_remove_women = st.session_state.get('remove_women', 0)
            work_data.append(["기본 인원", f"남 {base_info.get('men', 0)}명" + (f", 여 {base_info.get('housewife', 0)}명" if base_info.get('housewife', 0) > 0 else "")])
            work_data.append(["추가/변경 인원", f"추가 남 {pdf_add_men}명, 추가 여 {pdf_add_women}명, 빼는 여 {pdf_remove_women}명"]) # <<< 문구 수정 >>>
            work_table = Table(work_data, colWidths=[100, 350])
            work_table.setStyle(TableStyle([('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),('GRID', (0, 0), (-1, -1), 1, colors.black),('ALIGN', (0, 0), (-1, -1), "LEFT"),('VALIGN', (0, 0), (-1, -1), "MIDDLE"),('FONTNAME', (0, 0), (-1, -1), styles["Normal"].fontName if font_registered else 'Helvetica'),('BOTTOMPADDING', (0, 0), (-1, -1), 6),('TOPPADDING', (0, 0), (-1, -1), 6)])) # <<< 폰트 적용 수정 >>>
            elements.append(work_table); elements.append(Spacer(1, 12))

            # 4. 비용 상세 내역 (calculated_cost_items 사용)
            elements.append(Paragraph("■ 비용 상세 내역", styles["Heading2"]))
            elements.append(Spacer(1, 5))
            cost_data_pdf = [["항목", "금액", "비고"]]
            # calculated_cost_items의 각 항목이 리스트 형태라고 가정
            for item_row in calculated_cost_items:
                 # 모든 항목을 문자열로 변환 (Paragraph 위젯은 문자열 필요)
                 cost_data_pdf.append([str(col) for col in item_row])

            # 총 비용 행 추가
            cost_data_pdf.append(["총 견적 비용", f"{total_cost:,.0f}원", ""]) # <<< 소수점 제거 >>>

            cost_table = Table(cost_data_pdf, colWidths=[150, 100, 200])
            cost_table.setStyle(TableStyle([
                 ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                 ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
                 ('GRID', (0, 0), (-1, -1), 1, colors.black),
                 ('ALIGN', (0, 0), (-1, -1), "LEFT"),
                 ('ALIGN', (1, 1), (1, -1), "RIGHT"), # 금액 오른쪽 정렬
                 ('VALIGN', (0, 0), (-1, -1), "MIDDLE"),
                 ('FONTNAME', (0, 0), (-1, -1), styles["Normal"].fontName if font_registered else 'Helvetica'), # <<< 폰트 적용 수정 >>>
                 ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                 ('TOPPADDING', (0, 0), (-1, -1), 6),
                 # 마지막 행 (총 비용) 글자 굵게
                 ('FONTNAME', (0, -1), (-1, -1), styles["Normal"].fontName if font_registered else 'Helvetica-Bold'), # <<< 폰트 적용 수정 >>>
            ]))
            elements.append(cost_table); elements.append(Spacer(1, 12))

            # 5. 특이 사항
            special_notes_text = st.session_state.get("special_notes", "")
            if special_notes_text:
                elements.append(Paragraph("■ 특이 사항", styles["Heading2"]))
                elements.append(Spacer(1, 5))
                # Paragraph는 HTML 태그를 일부 지원하므로 줄바꿈은 <br/> 사용
                elements.append(Paragraph(special_notes_text.replace('\n', '<br/>'), styles["Normal"]))
                elements.append(Spacer(1, 12))

            # PDF 빌드 및 다운로드
            try:
                doc.build(elements)
                pdf_data = buffer.getvalue()
                b64_pdf = base64.b64encode(pdf_data).decode("utf-8")
                phone_part = extract_phone_number_part(st.session_state.get('customer_phone'))
                file_prefix = "보관이사견적서" if is_storage else "이사견적서"
                file_name = f"{file_prefix}_{phone_part}_{datetime.now().strftime('%Y%m%d')}.pdf"
                href = f'<a href="data:application/octet-stream;base64,{b64_pdf}" download="{file_name}">📥 {file_prefix} 다운로드 ({file_name})</a>'
                st.markdown(href, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"PDF 빌드 오류: {e}")
                st.error("PDF 생성 중 문제가 발생했습니다. 입력 값이나 폰트 설정을 확인해주세요.")


    elif not can_generate_pdf:
        st.caption("PDF를 생성하려면 고객명/전화번호 입력 및 차량 선택이 필요합니다.")


# --- (탭 네비게이션 버튼은 제거됨) ---
