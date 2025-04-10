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

# --- 페이지 설정 ---
st.set_page_config(page_title="이삿날 스마트견적", layout="wide")

# --- 타이틀 ---
st.title("🚚 이삿날 스마트견적")

# --- 데이터 정의 ---
# (데이터 정의는 이전과 동일 - 생략)
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
storage_daily_fee = 7000 # 보관이사 1일당 보관료

# 품목 데이터
items = {
    "방": {"장롱": (1.05, 120.0), "싱글침대": (1.20, 60.0), "더블침대": (1.70, 70.0), "돌침대": (2.50, 150.0),"옷장": (1.05, 160.0), "서랍장(3단)": (0.40, 30.0), "서랍장(5단)": (0.75, 40.0), "화장대": (0.32, 80.0),"중역책상": (1.20, 80.0), "책장": (0.96, 56.0), "책상&의자": (0.25, 40.0), "옷행거": (0.35, 40.0),},
    "거실": {"소파(1인용)": (0.40, 30.0), "소파(3인용)": (0.60, 50.0), "소파 테이블": (0.65, 35.0),"TV(45인치)": (0.15, 15.0), "TV(75인치)": (0.30, 30.0), "장식장": (0.75, 40.0),"오디오 및 스피커": (0.10, 20.0), "에어컨": (0.15, 30.0), "피아노(일반)": (1.50, 200.0),"피아노(디지털)": (0.50, 50.0), "안마기": (0.90, 50.0), "공기청정기": (0.10, 8.0),},
    "주방": {"양문형 냉장고": (1.00, 120.0), "4도어 냉장고": (1.20, 130.0), "김치냉장고(스탠드형)": (0.80, 90.0),"김치냉장고(일반형)": (0.60, 60.0), "식탁(4인)": (0.40, 50.0), "식탁(6인)": (0.60, 70.0),"가스레인지 및 인덕션": (0.10, 10.0), "주방용 선반(수납장)": (1.10, 80.0),},
    "기타": {"세탁기 및 건조기": (0.50, 80.0), "신발장": (1.10, 60.0), "여행가방 및 캐리어": (0.15, 5.0),"화분": (0.20, 10.0), "스타일러스": (0.50, 20.0),},
}
# 차량 용량
vehicle_capacity = {"1톤": 5, "2.5톤": 12, "3.5톤": 18, "5톤": 25, "6톤": 30,"7.5톤": 40, "10톤": 50, "15톤": 70, "20톤": 90,}
vehicle_weight_capacity = {"1톤": 1000, "2.5톤": 2500, "3.5톤": 3500, "5톤": 5000, "6톤": 6000,"7.5톤": 7500, "10톤": 10000, "15톤": 15000, "20톤": 20000,}
# 박스 부피
box_volumes = {"중대박스": 0.1875, "옷박스": 0.219, "중박스": 0.1}

# --- 함수 정의 ---
# (함수 정의는 이전과 동일 - 생략)
# 차량 추천
def recommend_vehicle(total_volume, total_weight):
    loading_efficiency = 0.90
    sorted_vehicles = sorted(vehicle_capacity.keys(), key=lambda x: vehicle_capacity.get(x, 0)) # Use .get for safety
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
        # 14층부터는 해당 층수 키 사용 (ladder_prices 딕셔너리에 해당 키가 있어야 함)
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
        if f >= 24: return "24층" # 24층 이상은 '24층' 키 사용
    except (ValueError, TypeError):
        return None
    return None

# 전화번호 추출 (파일명용)
def extract_phone_number_part(phone_str):
    if not phone_str: return "번호없음"
    cleaned = re.sub(r'\D', '', phone_str)
    return cleaned[-4:] if len(cleaned) >= 4 else "번호없음"

# --- 세션 상태 초기화 ---
# active_tab_index 제거
if "selected_items" not in st.session_state:
    st.session_state.selected_items = {}
if "additional_boxes" not in st.session_state:
    st.session_state.additional_boxes = {"중대박스": 0, "옷박스": 0, "중박스": 0}
if "base_move_type" not in st.session_state:
    st.session_state.base_move_type = "가정 이사 🏠"
if "is_storage_move" not in st.session_state:
    st.session_state.is_storage_move = False

# 기본 입력값 설정 (세션 상태 키 사용)
default_values = {
    "customer_name": "", "customer_phone": "", "from_location": "", "to_location": "",
    "moving_date": datetime.now().date(), "from_floor": "", "from_method": "사다리차",
    "to_floor": "", "to_method": "사다리차", "special_notes": "",
    "storage_duration": 1, "final_to_location": "", "final_to_floor": "", "final_to_method": "사다리차",
    # 차량 선택 관련 상태 추가 (Tab 3에서 사용)
    "vehicle_select_radio": "자동 추천 차량 사용",
    "manual_vehicle_select_value": None, # 수동 선택 값 저장
    # 스카이 시간 상태 추가 (Tab 3에서 사용)
    "sky_hours_from": 2,
    "sky_hours_final": 2
}
for key, value in default_values.items():
    if key not in st.session_state:
        st.session_state[key] = value

# 작업 방법 옵션
method_options = ["사다리차", "승강기", "계단", "스카이"]

# --- 탭 생성 (st.tabs 사용) ---
tab1, tab2, tab3 = st.tabs(["고객 정보", "물품 선택", "견적 및 비용"])

# --- 탭 1: 고객 정보 ---
with tab1:
    # active_tab_index 조건 제거 -> 항상 렌더링
    st.header("📝 고객 기본 정보")

    # 이사 유형 선택 (기본: 가정/사무실)
    base_move_type_options = ["가정 이사 🏠", "사무실 이사 🏢"]
    st.session_state.base_move_type = st.radio(
        "🏢 기본 이사 유형:", base_move_type_options,
        index=base_move_type_options.index(st.session_state.base_move_type),
        horizontal=True, key="base_move_type_radio_widget"
    )

    # 보관이사 여부 체크박스
    st.session_state.is_storage_move = st.checkbox("📦 보관이사 여부", key="is_storage_move_checkbox_widget", value=st.session_state.is_storage_move)

    col1, col2 = st.columns(2)
    with col1:
        st.text_input("👤 고객명", key="customer_name")
        st.text_input("📍 출발지", key="from_location")
        st.date_input("🚚 이사일 (출발일)", key="moving_date")

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
    # active_tab_index 조건 제거
    st.header("📋 품목 선택")
    st.caption(f"현재 선택된 기본 이사 유형: **{st.session_state.base_move_type}**")

    # (물품 선택 로직은 이전과 동일 - 코드 생략)
    # 품목 데이터 정의 (탭 내에서 사용)
    home_items_def = {
        "가정품목": {"장롱": items["방"]["장롱"], "더블침대": items["방"]["더블침대"], "서랍장(5단)": items["방"]["서랍장(5단)"],"화장대": items["방"]["화장대"], "TV(75인치)": items["거실"]["TV(75인치)"], "책상&의자": items["방"]["책상&의자"],"책장": items["방"]["책장"], "옷행거": items["방"]["옷행거"], "소파(3인용)": items["거실"]["소파(3인용)"],"장식장": items["거실"]["장식장"], "에어컨": items["거실"]["에어컨"], "4도어 냉장고": items["주방"]["4도어 냉장고"],"김치냉장고(스탠드형)": items["주방"]["김치냉장고(스탠드형)"], "식탁(4인)": items["주방"]["식탁(4인)"],"주방용 선반(수납장)": items["주방"]["주방용 선반(수납장)"], "세탁기 및 건조기": items["기타"]["세탁기 및 건조기"],},
        "기타품목": {"피아노(일반)": items["거실"]["피아노(일반)"], "피아노(디지털)": items["거실"]["피아노(디지털)"],"안마기": items["거실"]["안마기"], "스타일러스": items["기타"]["스타일러스"], "신발장": items["기타"]["신발장"],"화분": items["기타"]["화분"], "여행가방 및 캐리어": items["기타"]["여행가방 및 캐리어"],},
    }
    office_items_def = {
        "사무실품목": {"중역책상": items["방"]["중역책상"], "책상&의자": items["방"]["책상&의자"], "서랍장(5단)": items["방"]["서랍장(5단)"],"4도어 냉장고": items["주방"]["4도어 냉장고"], "TV(75인치)": items["거실"]["TV(75인치)"], "장식장": items["거실"]["장식장"],"에어컨": items["거실"]["에어컨"], "오디오 및 스피커": items["거실"]["오디오 및 스피커"],},
        "기타품목": {"안마기": items["거실"]["안마기"], "공기청정기": items["거실"]["공기청정기"], "화분": items["기타"]["화분"],"스타일러스": items["기타"]["스타일러스"], "신발장": items["기타"]["신발장"],},
    }

    item_category_to_display = home_items_def if st.session_state.base_move_type == "가정 이사 🏠" else office_items_def

    current_selection = {}
    current_boxes = {"중대박스": 0, "옷박스": 0, "중박스": 0}

    for section, item_list in item_category_to_display.items():
        with st.expander(f"{section} 선택"):
            cols = st.columns(3)
            items_list_items = list(item_list.items())
            num_items = len(items_list_items)
            items_per_col = (num_items + 2) // 3

            for idx, (item, (volume, weight)) in enumerate(items_list_items):
                col_index = idx // items_per_col
                if col_index < len(cols):
                    with cols[col_index]:
                        unit = "칸" if item == "장롱" else "개"
                        default_qty = st.session_state.selected_items.get(item, (0,))[0]
                        widget_key = f"qty_{st.session_state.base_move_type}_{section}_{item}"
                        qty = st.number_input(f"{item}", min_value=0, step=1, value=default_qty, key=widget_key)
                        if qty > 0:
                            current_selection[item] = (qty, unit, volume, weight)
                            if st.session_state.base_move_type == "가정 이사 🏠":
                                if item == "장롱": current_boxes["중대박스"] += qty * 5
                                if item == "서랍장(5단)": current_boxes["중박스"] += qty * 5

    st.session_state.selected_items = current_selection
    st.session_state.additional_boxes = current_boxes

    st.divider()
    st.subheader("📦 선택한 품목 정보")
    if st.session_state.selected_items:
        total_volume = sum(q * v for i, (q, u, v, w) in st.session_state.selected_items.items()) + \
                       sum(box_volumes[b] * c for b, c in st.session_state.additional_boxes.items())
        total_weight = sum(q * w for i, (q, u, v, w) in st.session_state.selected_items.items())

        cols_disp = st.columns(3)
        item_list_disp = list(st.session_state.selected_items.items())
        items_per_col_disp = (len(item_list_disp) + 2) // 3
        for i, (item, (qty, unit, vol, weight)) in enumerate(item_list_disp):
             col_idx_disp = i // items_per_col_disp
             if col_idx_disp < 3:
                 with cols_disp[col_idx_disp]:
                     st.write(f"**{item}**: {qty} {unit}")

        st.subheader("🚚 추천 차량 정보")
        recommended_vehicle, remaining_space = recommend_vehicle(total_volume, total_weight)
        st.info(f"📊 총 부피: {total_volume:.2f} m³ | 총 무게: {total_weight:.2f} kg")

        if recommended_vehicle and "초과" not in recommended_vehicle:
             st.success(f"🚛 추천 차량: {recommended_vehicle} (예상 여유 공간: {remaining_space:.2f}%)")
             if recommended_vehicle in vehicle_capacity:
                  loading_eff = 0.9
                  st.markdown(f"""
                  **{recommended_vehicle} 정보**:
                  - 최대 부피: {vehicle_capacity[recommended_vehicle]} m³ (적재율 {loading_eff*100:.0f}% 적용 시: {vehicle_capacity[recommended_vehicle]*loading_eff:.2f} m³)
                  - 최대 무게: {vehicle_weight_capacity[recommended_vehicle]:,} kg
                  """)
             else: st.warning("차량 상세 정보 로드 실패")
        else: st.error(f"🚛 추천 차량: {recommended_vehicle}")
    else:
        st.info("선택된 품목이 없습니다.")
        st.subheader("🚚 추천 차량 정보")
        st.info("📊 총 부피: 0.00 m³ | 총 무게: 0.00 kg")
        st.warning("🚛 추천 차량: 품목을 선택해주세요.")
        # recommended_vehicle = None # 이 변수는 아래에서 다시 계산되므로 여기서 None 설정 불필요

# --- 탭 3: 견적 및 비용 ---
with tab3:
    st.header("💰 이사 비용 계산")
    is_storage = st.session_state.is_storage_move

    # --- 차량 선택 ---
    # (차량 선택 로직은 이전과 동일)
    current_total_volume = sum(q * v for i, (q, u, v, w) in st.session_state.selected_items.items()) + \
                           sum(box_volumes[b] * c for b, c in st.session_state.additional_boxes.items())
    current_total_weight = sum(q * w for i, (q, u, v, w) in st.session_state.selected_items.items())
    tab3_recommended_vehicle, tab3_remaining_space = recommend_vehicle(current_total_volume, current_total_weight)

    col_v1, col_v2 = st.columns([1, 2])
    with col_v1:
        st.session_state.vehicle_select_radio = st.radio(
            "차량 선택 방식:", ["자동 추천 차량 사용", "수동으로 차량 선택"],
            index=["자동 추천 차량 사용", "수동으로 차량 선택"].index(st.session_state.vehicle_select_radio),
            key="vehicle_select_radio_widget_tab3", horizontal=False
        )

    selected_vehicle = None
    with col_v2:
        if st.session_state.vehicle_select_radio == "자동 추천 차량 사용":
            if tab3_recommended_vehicle and "초과" not in tab3_recommended_vehicle:
                selected_vehicle = tab3_recommended_vehicle
                st.success(f"추천 차량: **{selected_vehicle}**")
                if selected_vehicle in vehicle_capacity: st.caption(f"({selected_vehicle} 최대: {vehicle_capacity[selected_vehicle]}m³, {vehicle_weight_capacity[selected_vehicle]:,}kg)")
            else:
                 st.error(f"자동 추천 실패: {tab3_recommended_vehicle}. 수동 선택 필요.")

        if st.session_state.vehicle_select_radio == "수동으로 차량 선택":
             available_trucks = sorted(home_vehicle_prices.keys(), key=lambda x: vehicle_capacity.get(x, 0))
             if st.session_state.manual_vehicle_select_value is None and available_trucks:
                 st.session_state.manual_vehicle_select_value = available_trucks[0]
             current_manual_index = 0
             if st.session_state.manual_vehicle_select_value in available_trucks:
                  current_manual_index = available_trucks.index(st.session_state.manual_vehicle_select_value)
             selected_vehicle = st.selectbox("🚚 차량 선택 (수동):", available_trucks, index=current_manual_index, key="manual_vehicle_select_widget_tab3")
             st.session_state.manual_vehicle_select_value = selected_vehicle
             st.info(f"선택 차량: **{selected_vehicle}**")

        if st.session_state.vehicle_select_radio == "자동 추천 차량 사용" and (not tab3_recommended_vehicle or "초과" in tab3_recommended_vehicle):
            st.info("자동 추천 차량이 없어 수동으로 선택해주세요.")
            available_trucks = sorted(home_vehicle_prices.keys(), key=lambda x: vehicle_capacity.get(x, 0))
            if st.session_state.manual_vehicle_select_value is None and available_trucks:
                 st.session_state.manual_vehicle_select_value = available_trucks[0]
            current_manual_index = 0
            if st.session_state.manual_vehicle_select_value in available_trucks:
                  current_manual_index = available_trucks.index(st.session_state.manual_vehicle_select_value)
            selected_vehicle = st.selectbox("🚚 차량 선택 (수동):", available_trucks, index=current_manual_index, key="manual_vehicle_select_widget_tab3_fallback")
            st.session_state.manual_vehicle_select_value = selected_vehicle

    # --- 기타 옵션 ---
    st.divider()
    st.subheader("🛠️ 작업 및 추가 옵션")

    # 스카이 사용 여부 및 시간
    uses_sky_from = st.session_state.get('from_method') == "스카이"
    final_dest_method_key = 'final_to_method' if is_storage else 'to_method'
    uses_sky_final_to = st.session_state.get(final_dest_method_key) == "스카이"

    if uses_sky_from or uses_sky_final_to:
         st.warning("스카이 작업 포함됨. 필요시 시간 조절.", icon="🏗️")
         col_sky1, col_sky2 = st.columns(2)
         if uses_sky_from:
              with col_sky1:
                  # 위젯이 세션 상태 sky_hours_from을 직접 업데이트
                  st.number_input(
                      "출발지 스카이 시간", min_value=2, step=1,
                      key="sky_hours_from", # value 대신 key 사용
                      # value=st.session_state.sky_hours_from # value 명시 불필요
                  )
         if uses_sky_final_to:
              to_label = "최종 도착지" if is_storage else "도착지"
              with col_sky2:
                  # 위젯이 세션 상태 sky_hours_final을 직접 업데이트
                  st.number_input(
                      f"{to_label} 스카이 시간", min_value=2, step=1,
                      key="sky_hours_final", # value 대신 key 사용
                      # value=st.session_state.sky_hours_final # value 명시 불필요
                  )

    # 추가 인원
    col_add1, col_add2 = st.columns(2)
    with col_add1:
        # 위젯이 세션 상태 add_men 을 직접 업데이트
        st.number_input("추가 남성 인원 👨", min_value=0, step=1, key="add_men") # value 제거
    with col_add2:
        # 위젯이 세션 상태 add_women 을 직접 업데이트
        st.number_input("추가 여성 인원 👩", min_value=0, step=1, key="add_women") # value 제거
    # ---- 아래 두 줄 제거 ----
    # st.session_state.add_men = additional_men
    # st.session_state.add_women = additional_women

    # 폐기물 처리
    col_waste1, col_waste2 = st.columns(2)
    with col_waste1:
        # 위젯이 세션 상태 has_waste_check 를 직접 업데이트
        st.checkbox("폐기물 처리 필요 🗑️", key="has_waste_check") # value 제거
    # ---- 아래 줄 제거 ----
    # st.session_state.has_waste_check = has_waste
    with col_waste2:
        waste_tons = 0 # 로컬 변수는 필요시 계속 사용 가능
        if st.session_state.has_waste_check: # 세션 상태에서 직접 확인
            # 위젯이 세션 상태 waste_tons_input 를 직접 업데이트
            waste_tons = st.number_input("폐기물 양 (톤)", min_value=0.5, max_value=10.0, step=0.5, key="waste_tons_input") # value 제거
            st.caption("💡 1톤당 30만원 추가")
            # ---- 아래 줄 제거 ----
            # st.session_state.waste_tons_input = waste_tons


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
    # ---- 체크박스 값에 대한 명시적 세션 상태 할당 제거 ----


    # --- 비용 계산 ---
    st.divider()
    st.subheader("💵 이사 비용 계산")

    total_cost = 0
    calculated_cost_items = []
    base_info = {}

    if selected_vehicle:
        # 비용 계산 시에는 세션 상태에서 값을 직접 읽어옴
        additional_men_cost = st.session_state.add_men # 세션 상태에서 읽기
        additional_women_cost = st.session_state.add_women # 세션 상태에서 읽기
        has_waste_cost = st.session_state.has_waste_check # 세션 상태에서 읽기
        waste_tons_cost = st.session_state.waste_tons_input if has_waste_cost else 0 # 세션 상태에서 읽기

        # 1. 기본 비용
        base_move_cost_type = home_vehicle_prices if st.session_state.base_move_type == "가정 이사 🏠" else office_vehicle_prices
        base_info = base_move_cost_type.get(selected_vehicle, {"price": 0, "men": 0})
        if 'housewife' not in base_info: base_info['housewife'] = 0
        base_cost_one_way = base_info.get("price", 0)

        if is_storage:
            base_cost_calculated = base_cost_one_way * 2
            total_cost += base_cost_calculated
            calculated_cost_items.append(["기본 이사 비용 (보관x2)", f"{base_cost_calculated:,}원", f"{selected_vehicle} 기준"])
        else:
            base_cost_calculated = base_cost_one_way
            total_cost += base_cost_calculated
            calculated_cost_items.append(["기본 이사 비용", f"{base_cost_calculated:,}원", f"{selected_vehicle} 기준"])

        # 2. 작업 비용
        ladder_vehicle_size = "5톤"
        if selected_vehicle in ["6톤", "7.5톤", "10톤"]: ladder_vehicle_size = selected_vehicle

        # 출발지
        ladder_from_cost = 0; sky_from_cost = 0
        from_method = st.session_state.get('from_method')
        from_floor_range = get_ladder_range(st.session_state.get('from_floor'))
        if from_method == "사다리차" and from_floor_range:
             ladder_from_cost = ladder_prices.get(from_floor_range, {}).get(ladder_vehicle_size, 0)
             if ladder_from_cost > 0: total_cost += ladder_from_cost; calculated_cost_items.append(["출발지 사다리차", f"{ladder_from_cost:,}원", f"{st.session_state.get('from_floor')}층"])
        elif from_method == "스카이":
             sky_from_cost = sky_base_price + max(0, st.session_state.sky_hours_from - 2) * sky_extra_hour_price # 세션 상태 값 사용
             total_cost += sky_from_cost; calculated_cost_items.append(["출발지 스카이", f"{sky_from_cost:,}원", f"{st.session_state.sky_hours_from}시간"])

        # 도착지 (또는 최종 도착지)
        ladder_to_cost = 0; sky_to_cost = 0
        to_method = st.session_state.get('final_to_method') if is_storage else st.session_state.get('to_method')
        to_floor = st.session_state.get('final_to_floor') if is_storage else st.session_state.get('to_floor')
        to_label = "최종 도착지" if is_storage else "도착지"
        to_floor_range = get_ladder_range(to_floor)

        if to_method == "사다리차" and to_floor_range:
             ladder_to_cost = ladder_prices.get(to_floor_range, {}).get(ladder_vehicle_size, 0)
             if ladder_to_cost > 0: total_cost += ladder_to_cost; calculated_cost_items.append([f"{to_label} 사다리차", f"{ladder_to_cost:,}원", f"{to_floor}층"])
        elif to_method == "스카이":
             sky_to_cost = sky_base_price + max(0, st.session_state.sky_hours_final - 2) * sky_extra_hour_price # 세션 상태 값 사용
             total_cost += sky_to_cost; calculated_cost_items.append([f"{to_label} 스카이", f"{sky_to_cost:,}원", f"{st.session_state.sky_hours_final}시간"])

        # 3. 보관료
        if is_storage:
            storage_days = st.session_state.get("storage_duration", 1)
            storage_fee = storage_days * storage_daily_fee
            total_cost += storage_fee; calculated_cost_items.append(["보관료", f"{storage_fee:,}원", f"{storage_days}일"])

        # 4. 추가 인원 (세션 상태 값 사용)
        additional_person_total = (additional_men_cost + additional_women_cost) * additional_person_cost
        if additional_person_total > 0:
            total_cost += additional_person_total; calculated_cost_items.append(["추가 인원", f"{additional_person_total:,}원", f"남{additional_men_cost}, 여{additional_women_cost}명"])

        # 5. 폐기물 (세션 상태 값 사용)
        if has_waste_cost and waste_tons_cost > 0:
            waste_cost = waste_tons_cost * waste_disposal_cost
            total_cost += waste_cost; calculated_cost_items.append(["폐기물 처리", f"{waste_cost:,}원", f"{waste_tons_cost}톤"])

        # 6. 날짜 할증 (selected_dates 는 위젯에서 직접 계산됨)
        special_day_cost_factor = sum(special_day_prices.get(date, 0) for date in selected_dates)
        if special_day_cost_factor > 0:
            total_cost += special_day_cost_factor; calculated_cost_items.append(["날짜 할증", f"{special_day_cost_factor:,}원", f"{', '.join(selected_dates)}"])

        # --- 비용 내역 표시 ---
        st.subheader("📊 비용 상세 내역")
        if calculated_cost_items:
            cost_df = pd.DataFrame(calculated_cost_items, columns=["항목", "금액", "비고"])
            st.table(cost_df.style.format({"금액": "{}"}))
        else: st.info("계산된 비용 항목이 없습니다.")

        st.subheader(f"💰 총 견적 비용: {total_cost:,}원")

        if st.session_state.get("special_notes", ""):
            st.subheader("📝 특이 사항")
            st.info(st.session_state.get("special_notes", ""))
    else:
        st.warning("차량을 먼저 선택해주세요.")

    # --- PDF 견적서 생성 기능 ---
    st.divider()
    st.subheader("📄 견적서 다운로드")
    # (PDF 생성 로직은 이전과 거의 동일, 비용 계산 시 사용된 변수명 확인 필요)
    can_generate_pdf = selected_vehicle and (st.session_state.get("customer_name") or st.session_state.get("customer_phone"))
    if st.button("PDF 견적서 생성", disabled=not can_generate_pdf, key="pdf_generate_button"):
        if not selected_vehicle: st.error("PDF 생성을 위해 차량을 선택해주세요.")
        elif not (st.session_state.get("customer_name") or st.session_state.get("customer_phone")): st.error("PDF 생성을 위해 고객명 또는 전화번호를 입력해주세요.")
        else:
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            # (폰트 설정 등 PDF 세부 로직은 이전과 동일 - 생략)
            # ... PDF elements generation using session state values ...
            # 예시: 작업 정보에서 추가 인원 가져올 때 세션 상태 사용
            # work_data.append(["추가 인원", f"남 {st.session_state.add_men}명, 여 {st.session_state.add_women}명"])
            # ... rest of PDF generation ...

            # --- PDF 내용 구성 시작 ---
            font_path = "NanumGothic.ttf"
            font_registered = False
            try:
                if os.path.exists(font_path): pdfmetrics.registerFont(TTFont("NanumGothic", font_path)); font_registered = True
                else: st.error(f"폰트 파일({font_path}) 없음.")
            except Exception as e: st.error(f"폰트 등록 오류: {e}")

            styles = getSampleStyleSheet()
            if font_registered:
                for style_name in styles.byName:
                    try: styles[style_name].fontName = "NanumGothic"
                    except: pass

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
            basic_table = Table(basic_data, colWidths=[100, 350])
            basic_table.setStyle(TableStyle([('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),('GRID', (0, 0), (-1, -1), 1, colors.black),('ALIGN', (0, 0), (-1, -1), "LEFT"),('VALIGN', (0, 0), (-1, -1), "MIDDLE"),('FONTNAME', (0, 0), (-1, -1), styles["Normal"].fontName),('BOTTOMPADDING', (0, 0), (-1, -1), 6),('TOPPADDING', (0, 0), (-1, -1), 6)]))
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
            work_data.append(["기본 인원", f"남 {base_info.get('men', 0)}명" + (f", 여 {base_info.get('housewife', 0)}명" if base_info.get('housewife', 0) > 0 else "")])
            work_data.append(["추가 인원", f"남 {pdf_add_men}명, 여 {pdf_add_women}명"])
            work_table = Table(work_data, colWidths=[100, 350])
            work_table.setStyle(TableStyle([('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),('GRID', (0, 0), (-1, -1), 1, colors.black),('ALIGN', (0, 0), (-1, -1), "LEFT"),('VALIGN', (0, 0), (-1, -1), "MIDDLE"),('FONTNAME', (0, 0), (-1, -1), styles["Normal"].fontName),('BOTTOMPADDING', (0, 0), (-1, -1), 6),('TOPPADDING', (0, 0), (-1, -1), 6)]))
            elements.append(work_table); elements.append(Spacer(1, 12))

            # 4. 비용 상세 내역 (calculated_cost_items 사용)
            elements.append(Paragraph("■ 비용 상세 내역", styles["Heading2"]))
            elements.append(Spacer(1, 5))
            cost_data_pdf = [["항목", "금액", "비고"]]
            cost_data_pdf.extend(calculated_cost_items)
            cost_data_pdf.append(["총 견적 비용", f"{total_cost:,}원", ""])
            cost_table = Table(cost_data_pdf, colWidths=[150, 100, 200])
            cost_table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey), ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey), ('GRID', (0, 0), (-1, -1), 1, colors.black), ('ALIGN', (0, 0), (-1, -1), "LEFT"), ('ALIGN', (1, 1), (1, -1), "RIGHT"), ('VALIGN', (0, 0), (-1, -1), "MIDDLE"), ('FONTNAME', (0, 0), (-1, -1), styles["Normal"].fontName), ('FONTNAME', (0, 0), (-1, 0), styles["Normal"].fontName), ('FONTNAME', (0, -1), (-1, -1), styles["Normal"].fontName), ('BOTTOMPADDING', (0, 0), (-1, -1), 6), ('TOPPADDING', (0, 0), (-1, -1), 6)]))
            elements.append(cost_table); elements.append(Spacer(1, 12))

            # 5. 특이 사항
            special_notes_text = st.session_state.get("special_notes", "")
            if special_notes_text:
                elements.append(Paragraph("■ 특이 사항", styles["Heading2"]))
                elements.append(Spacer(1, 5))
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
            except Exception as e: st.error(f"PDF 빌드 오류: {e}")

    elif not can_generate_pdf:
         st.caption("PDF를 생성하려면 고객명/전화번호 입력 및 차량 선택이 필요합니다.")


# --- (탭 네비게이션 버튼은 제거됨) ---
