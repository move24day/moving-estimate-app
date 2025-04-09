import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import base64
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from io import BytesIO

# 페이지 설정
st.set_page_config(page_title="통합 이사 비용 계산기", layout="wide")

# 로고 표시 (화면 좌측 상단)
try:
    st.image("logo.png", width=150)
except:
    st.title("🚚 통합 이사 비용 계산기")

# 차량 톤수와 유형에 따른 기본 비용
office_vehicle_prices = {
    '1톤': {'price': 400000, 'men': 2},
    '2.5톤': {'price': 650000, 'men': 2},
    '3.5톤': {'price': 700000, 'men': 2},
    '5톤': {'price': 950000, 'men': 3},
    '6톤': {'price': 1050000, 'men': 3},
    '7.5톤': {'price': 1300000, 'men': 4},
    '10톤': {'price': 1700000, 'men': 5},
    '15톤': {'price': 2000000, 'men': 6},
    '20톤': {'price': 2500000, 'men': 8}
}

home_vehicle_prices = {
    '1톤': {'price': 400000, 'men': 2, 'housewife': 0},
    '2.5톤': {'price': 900000, 'men': 2, 'housewife': 1},
    '3.5톤': {'price': 950000, 'men': 2, 'housewife': 1},
    '5톤': {'price': 1200000, 'men': 3, 'housewife': 1},
    '6톤': {'price': 1350000, 'men': 3, 'housewife': 1},
    '7.5톤': {'price': 1750000, 'men': 4, 'housewife': 1},
    '10톤': {'price': 2300000, 'men': 5, 'housewife': 1},
    '15톤': {'price': 2800000, 'men': 6, 'housewife': 1},
    '20톤': {'price': 3500000, 'men': 8, 'housewife': 1}
}

# 사다리 비용 (층수와 톤수에 따른)
ladder_prices = {
    '2~5층': {'5톤': 150000, '6톤': 180000, '7.5톤': 210000, '10톤': 240000},
    '6~7층': {'5톤': 160000, '6톤': 190000, '7.5톤': 220000, '10톤': 250000},
    '8~9층': {'5톤': 170000, '6톤': 200000, '7.5톤': 230000, '10톤': 260000},
    '10~11층': {'5톤': 180000, '6톤': 210000, '7.5톤': 240000, '10톤': 270000},
    '12~13층': {'5톤': 190000, '6톤': 220000, '7.5톤': 250000, '10톤': 280000},
    '14층': {'5톤': 200000, '6톤': 230000, '7.5톤': 260000, '10톤': 290000},
    '15층': {'5톤': 210000, '6톤': 240000, '7.5톤': 270000, '10톤': 300000},
    '16층': {'5톤': 220000, '6톤': 250000, '7.5톤': 280000, '10톤': 310000},
    '17층': {'5톤': 230000, '6톤': 260000, '7.5톤': 290000, '10톤': 320000},
    '18층': {'5톤': 250000, '6톤': 280000, '7.5톤': 310000, '10톤': 340000},
    '19층': {'5톤': 260000, '6톤': 290000, '7.5톤': 320000, '10톤': 350000},
    '20층': {'5톤': 280000, '6톤': 310000, '7.5톤': 340000, '10톤': 370000},
    '21층': {'5톤': 310000, '6톤': 340000, '7.5톤': 370000, '10톤': 400000},
    '22층': {'5톤': 340000, '6톤': 370000, '7.5톤': 400000, '10톤': 430000},
    '23층': {'5톤': 370000, '6톤': 400000, '7.5톤': 430000, '10톤': 460000},
    '24층': {'5톤': 400000, '6톤': 430000, '7.5톤': 460000, '10톤': 490000}
}

special_day_prices = {
    '평일(일반)': 0,
    '이사많은날 🏠': 200000,
    '손없는날 ✋': 100000,
    '월말 📅': 100000,
    '공휴일 🎉': 100000
}

# 추가 인원 비용
additional_person_cost = 200000  # 추가 인원 1명당 20만원

# 폐기물 처리 비용
waste_disposal_cost = 300000  # 폐기물 1톤당 30만원

# 스카이 비용
sky_base_price = 300000  # 기본 2시간
sky_extra_hour_price = 50000  # 추가 시간당

# 품목 데이터 (부피 m³, 무게 kg)
items = {
    '방': {
        '장롱': (1.05, 120.0), '싱글침대': (1.20, 60.0), '더블침대': (1.70, 70.0), '돌침대': (2.50, 150.0),
        '옷장': (1.05, 160.0), '서랍장(3단)': (0.40, 30.0), '서랍장(5단)': (0.75, 40.0), '화장대': (0.32, 80.0),
        '중역책상': (1.20, 80.0), '책장': (0.96, 56.0), '책상&의자': (0.25, 40.0), '옷행거': (0.35, 40.0),
    },
    '거실': {
        '소파(1인용)': (0.40, 30.0), '소파(3인용)': (0.60, 50.0), '소파 테이블': (0.65, 35.0),
        'TV(45인치)': (0.15, 15.0), 'TV(75인치)': (0.30, 30.0), '장식장': (0.75, 40.0),
        '오디오 및 스피커': (0.10, 20.0), '에어컨': (0.15, 30.0), '피아노(일반)': (1.50, 200.0),
        '피아노(디지털)': (0.50, 50.0), '안마기': (0.90, 50.0), '공기청정기': (0.10, 8.0)
    },
    '주방': {
        '양문형 냉장고': (1.00, 120.0), '4도어 냉장고': (1.20, 130.0), '김치냉장고(스탠드형)': (0.80, 90.0), '김치냉장고(일반형)': (0.60, 60.0),
        '식탁(4인)': (0.40, 50.0), '식탁(6인)': (0.60, 70.0),
        '가스레인지 및 인덕션': (0.10, 10.0),
        '주방용 선반(수납장)': (1.10, 80.0)
    },
    '기타': {
        '세탁기 및 건조기': (0.50, 80.0),
        '신발장': (1.10, 60.0), '여행가방 및 캐리어': (0.15, 5.0), '화분': (0.20, 10.0), 
        '스타일러스': (0.50, 20.0)
    }
}

# 차량 부피 용량 정보 (m³)
vehicle_capacity = {
    '1톤': 5, '2.5톤': 12, '3.5톤': 18, '5톤': 25, '6톤': 30,
    '7.5톤': 40, '10톤': 50, '15톤': 70, '20톤': 90
}

# 차량 무게 용량 정보 (kg)
vehicle_weight_capacity = {
    '1톤': 1000, '2.5톤': 2500, '3.5톤': 3500, '5톤': 5000, '6톤': 6000,
    '7.5톤': 7500, '10톤': 10000, '15톤': 15000, '20톤': 20000
}

# 차량 추천 함수
def recommend_vehicle(total_volume, total_weight):
    loading_efficiency = 0.90  # 적재 효율 90%
    
    for name in sorted(vehicle_capacity.keys(), key=lambda x: vehicle_capacity[x]):
        effective_capacity = vehicle_capacity[name] * loading_efficiency
        if total_volume <= effective_capacity and total_weight <= vehicle_weight_capacity[name]:
            remaining_space = (effective_capacity - total_volume) / effective_capacity * 100
            return name, remaining_space
    
    return "20톤 이상 차량 필요", 0

# 층수에 따른 사다리 세부 구간 매핑 함수
def get_ladder_range(floor):
    try:
        floor_num = int(floor)
        if floor_num < 2:
            return None  # 1층 이하는 사다리 필요 없음
        elif 2 <= floor_num <= 5:
            return '2~5층'
        elif 6 <= floor_num <= 7:
            return '6~7층'
        elif 8 <= floor_num <= 9:
            return '8~9층'
        elif 10 <= floor_num <= 11:
            return '10~11층'
        elif 12 <= floor_num <= 13:
            return '12~13층'
        elif floor_num == 14:
            return '14층'
        elif floor_num == 15:
            return '15층'
        elif floor_num == 16:
            return '16층'
        elif floor_num == 17:
            return '17층'
        elif floor_num == 18:
            return '18층'
        elif floor_num == 19:
            return '19층'
        elif floor_num == 20:
            return '20층'
        elif floor_num == 21:
            return '21층'
        elif floor_num == 22:
            return '22층'
        elif floor_num == 23:
            return '23층'
        elif floor_num >= 24:
            return '24층'
    except ValueError:
        return None  # 숫자로 변환할 수 없는 경우
    
    return None

# 세션 상태 초기화
if 'selected_items' not in st.session_state:
    st.session_state.selected_items = {}
if 'additional_boxes' not in st.session_state:
    st.session_state.additional_boxes = {"중대박스": 0, "옷박스": 0, "중박스": 0}
if 'move_type' not in st.session_state:
    st.session_state.move_type = '가정 이사 🏠'

# 탭 생성
tab1, tab2, tab3 = st.tabs(["고객 정보", "물품 선택", "견적 및 비용"])

# 탭 1: 고객 정보
with tab1:
    st.header("📝 고객 기본 정보")
    
    # 이사 유형 선택
    move_type_options = ['가정 이사 🏠', '사무실 이사 🏢']
    st.session_state.move_type = st.radio('🏢 이사 유형 선택:', move_type_options, horizontal=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        customer_name = st.text_input("👤 고객명", key="customer_name")
        from_location = st.text_input("📍 출발지", key="from_location")
    
    with col2:
        customer_phone = st.text_input("📞 전화번호", key="customer_phone")
        to_location = st.text_input("📍 도착지", key="to_location")
    
    moving_date = st.date_input("🚚 이사일", key="moving_date")
    
    # 견적일 자동 표시 (현재시간)
    kst = pytz.timezone('Asia/Seoul')
    estimate_date = datetime.now(kst).strftime("%Y-%m-%d %H:%M")
    
    st.header("🏢 작업 조건")
    col1, col2 = st.columns(2)
    
    method_options = ["사다리차", "승강기", "계단", "스카이"]
    
    with col1:
        from_floor = st.text_input("🔼 출발지 층수", key="from_floor")
        from_method = st.selectbox("🛗 출발지 작업 방법", method_options, key='from_method')
    
    with col2:
        to_floor = st.text_input("🔽 도착지 층수", key="to_floor")
        to_method = st.selectbox("🛗 도착지 작업 방법", method_options, key='to_method')
    
    st.header("🗒️ 특이 사항 입력")
    special_notes = st.text_area("특이 사항이 있으면 입력해주세요.", height=100, key="special_notes")

# 탭 2: 물품 선택
with tab2:
    st.header("📋 품목 선택")

    selected_items = {}
    additional_boxes = {"중대박스": 0, "옷박스": 0, "중박스": 0}
    
    # 이사 유형에 따른 품목 분류 정의
    home_items = {
        '가정품목': {
            '장롱': items['방']['장롱'],
            '더블침대': items['방']['더블침대'],
            '서랍장(5단)': items['방']['서랍장(5단)'],
            '화장대': items['방']['화장대'],
            'TV(75인치)': items['거실']['TV(75인치)'],
            '책상&의자': items['방']['책상&의자'],
            '책장': items['방']['책장'],
            '옷행거': items['방']['옷행거'],
            '소파(3인용)': items['거실']['소파(3인용)'],
            '장식장': items['거실']['장식장'],
            '에어컨': items['거실']['에어컨'],
            '4도어 냉장고': items['주방']['4도어 냉장고'],
            '김치냉장고(스탠드형)': items['주방']['김치냉장고(스탠드형)'],
            '식탁(4인)': items['주방']['식탁(4인)'],
            '주방용 선반(수납장)': items['주방']['주방용 선반(수납장)'],
            '세탁기 및 건조기': items['기타']['세탁기 및 건조기']
        },
        '기타품목': {
            '피아노(일반)': items['거실']['피아노(일반)'],
            '피아노(디지털)': items['거실']['피아노(디지털)'],
            '안마기': items['거실']['안마기'],
            '스타일러스': items['기타']['스타일러스'],
            '신발장': items['기타']['신발장'],
            '화분': items['기타']['화분'],
            '여행가방 및 캐리어': items['기타']['여행가방 및 캐리어']
        }
    }

    office_items = {
        '사무실품목': {
            '중역책상': items['방']['중역책상'],
            '책상&의자': items['방']['책상&의자'],
            '서랍장(5단)': items['방']['서랍장(5단)'],
            '4도어 냉장고': items['주방']['4도어 냉장고'],
            'TV(75인치)': items['거실']['TV(75인치)'],
            '장식장': items['거실']['장식장'],
            '에어컨': items['거실']['에어컨'],
            '오디오 및 스피커': items['거실']['오디오 및 스피커']
        },
        '기타품목': {
            '안마기': items['거실']['안마기'],
            '공기청정기': items['거실']['공기청정기'],
            '화분': items['기타']['화분'],
            '스타일러스': items['기타']['스타일러스'],
            '신발장': items['기타']['신발장']
        }
    }

    # 선택된 이사 유형에 따라 품목 출력
    item_category = home_items if st.session_state.move_type == '가정 이사 🏠' else office_items

    for section, item_list in item_category.items():
        with st.expander(f"{section} 선택"):
            cols = st.columns(3)
            items_list = list(item_list.items())
            third_len = len(items_list) // 3 + (len(items_list) % 3 > 0)
            for idx, (item, (volume, weight)) in enumerate(items_list):
                with cols[idx // third_len]:
                    unit = "칸" if item == "장롱" else "개"
                    qty = st.number_input(f"{item}", min_value=0, step=1, key=f"{section}_{item}")
                    if qty > 0:
                        selected_items[item] = (qty, unit, volume, weight)

                        # 박스 자동 추가 조건 (가정 이사만 적용)
                        if st.session_state.move_type == '가정 이사 🏠':
                            if item == "장롱":
                                additional_boxes["중대박스"] += qty * 5
                            if item == "옷장":
                                additional_boxes["옷박스"] += qty * 3
                            if item == "서랍장(5단)":
                                additional_boxes["중박스"] += qty * 5

    # 세션 상태 저장
    st.session_state.selected_items = selected_items
    st.session_state.additional_boxes = additional_boxes

    # 박스 부피 계산
    box_volumes = {"중대박스": 0.1875, "옷박스": 0.219, "중박스": 0.1}

    # 총 부피와 무게 계산
    total_volume = sum(qty * vol for item, (qty, unit, vol, weight) in selected_items.items())
    total_volume += sum(box_volumes[box] * count for box, count in additional_boxes.items())

    total_weight = sum(qty * weight for item, (qty, unit, vol, weight) in selected_items.items())

    # 차량 추천 및 여유 공간 계산
    recommended_vehicle, remaining_space = recommend_vehicle(total_volume, total_weight)

    # 선택한 품목 정보 출력
    st.subheader("📦 선택한 품목 정보")

    if selected_items:
        item_data = []
        for item, (qty, unit, vol, weight) in selected_items.items():
            item_data.append([
                item, qty, unit, f"{vol:.2f} m³", f"{weight:.1f} kg",
                f"{qty * vol:.2f} m³", f"{qty * weight:.1f} kg"
            ])
        df = pd.DataFrame(item_data, columns=["품목", "수량", "단위", "단위 부피", "단위 무게", "총 부피", "총 무게"])
        st.dataframe(df, use_container_width=True)

        # 추가 박스 정보
        if any(additional_boxes.values()):
            st.subheader("📦 추가 박스 정보")
            box_data = []
            for box, count in additional_boxes.items():
                if count > 0:
                    vol = box_volumes[box]
                    box_data.append([box, count, f"{vol:.3f} m³", f"{vol * count:.3f} m³"])
            df_box = pd.DataFrame(box_data, columns=["박스 종류", "수량", "단위 부피", "총 부피"])
            st.dataframe(df_box, use_container_width=True)
    else:
        st.info("선택된 품목이 없습니다.")

# 탭 3: 견적 및 비용
with tab3:
    st.header("💰 이사 비용 계산")
    
    # 차량 선택 옵션 (자동 추천 또는 수동 선택)
    col1, col2 = st.columns(2)
    with col1:
        vehicle_selection = st.radio(
            "차량 선택 방식:",
            ["자동 추천 차량 사용", "수동으로 차량 선택"],
            horizontal=True
        )
    
    with col2:
        if vehicle_selection == "자동 추천 차량 사용":
            selected_vehicle = recommended_vehicle
            st.info(f"추천 차량: {recommended_vehicle} (여유 공간: {remaining_space:.2f}%)")
        else:
            selected_vehicle = st.selectbox('🚚 차량 톤수 선택:', sorted(list(home_vehicle_prices.keys())))
    
    # 출발지와 도착지에서 사다리차 사용 확인
    uses_ladder_from = False
    uses_ladder_to = False
    ladder_from_floor = None
    ladder_to_floor = None
    
    if 'from_method' in st.session_state and st.session_state.from_method == '사다리차' and 'from_floor' in st.session_state:
        uses_ladder_from = True
        ladder_from_floor = get_ladder_range(st.session_state.from_floor)
    
    if 'to_method' in st.session_state and st.session_state.to_method == '사다리차' and 'to_floor' in st.session_state:
        uses_ladder_to = True
        ladder_to_floor = get_ladder_range(st.session_state.to_floor)
    
    # 사다리 정보 표시
    if uses_ladder_from or uses_ladder_to:
        st.subheader('🪜 사다리차 사용 정보')
        col1, col2 = st.columns(2)
        with col1:
            if uses_ladder_from:
                if ladder_from_floor:
                    st.info(f'출발지 사다리차 사용: {ladder_from_floor}')
                else:
                    st.warning('출발지 층수가 유효하지 않거나 사다리차가 필요하지 않습니다.')
        
        with col2:
            if uses_ladder_to:
                if ladder_to_floor:
                    st.info(f'도착지 사다리차 사용: {ladder_to_floor}')
                else:
                    st.warning('도착지 층수가 유효하지 않거나 사다리차가 필요하지 않습니다.')
    
    # 스카이 옵션
    sky_hours = 2
    if 'from_method' in st.session_state and 'to_method' in st.session_state:
        if '스카이' in [st.session_state.from_method, st.session_state.to_method]:
            sky_hours = st.number_input('스카이 사용 시간 (기본 2시간 포함) ⏱️', min_value=2, step=1)
    
    # 추가 인원 옵션
    st.subheader('👥 인원 추가 옵션')
    col1, col2 = st.columns(2)
    with col1:
        additional_men = st.number_input('추가 남성 인원 👨', min_value=0, step=1)
    with col2:
        additional_women = st.number_input('추가 여성 인원 👩', min_value=0, step=1)
    
    # 폐기물 처리 옵션
    st.subheader('🗑️ 폐기물 처리 옵션')
    col1, col2 = st.columns(2)
    with col1:
        has_waste = st.checkbox('폐기물 처리 필요')
    with col2:
        waste_tons = 0
        if has_waste:
            waste_tons = st.number_input('폐기물 양 (톤)', min_value=0.5, max_value=10.0, value=1.0, step=0.5)
            st.info('💡 폐기물 처리 비용: 1톤당 30만원이 추가됩니다.')
    
    # 날짜 유형 다중 선택
    st.subheader('📅 날짜 유형 선택 (중복 가능)')
    date_options = list(special_day_prices.keys())
    selected_dates = []
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.checkbox(date_options[0]):
            selected_dates.append(date_options[0])
        if len(date_options) > 2 and st.checkbox(date_options[2]):
            selected_dates.append(date_options[2])
    with col2:
        if len(date_options) > 1 and st.checkbox(date_options[1]):
            selected_dates.append(date_options[1])
        if len(date_options) > 3 and st.checkbox(date_options[3]):
            selected_dates.append(date_options[3])
    with col3:
        if len(date_options) > 4 and st.checkbox(date_options[4]):
            selected_dates.append(date_options[4])
    
    # 선택된 날짜가 없으면 '평일(일반)'을 기본값으로 설정
    if not selected_dates:
        selected_dates.append('평일(일반)')
    
    # 선택한 물품 간략 표시
    if st.session_state.selected_items:
        st.subheader("📦 선택한 물품 정보")
        col1, col2 = st.columns(2)
        with col1:
            st.write("##### 품목 목록")
            for item, (qty, unit, _, _) in st.session_state.selected_items.items():
                st.write(f"- {item}: {qty} {unit}")
        
        with col2:
            st.write("##### 부피 및 무게 정보")
            st.write(f"- 총 부피: {total_volume:.2f} m³")
            st.write(f"- 총 무게: {total_weight:.2f} kg")
    
    # 비용 계산
    if st.button('💰 이사 비용 계산하기'):
        # 기본 비용 설정
        if st.session_state.move_type == '가정 이사 🏠':
            base_info = home_vehicle_prices.get(selected_vehicle, {'price':0, 'men':0, 'housewife':0})
        else:
            base_info = office_vehicle_prices.get(selected_vehicle, {'price':0, 'men':0})

        base_cost = base_info['price']
        total_cost = base_cost

        # 사다리 비용 계산 (출발지 및 도착지, 5톤 미만은 5톤 가격 적용)
        ladder_from_cost = ladder_to_cost = 0
        ladder_vehicle = selected_vehicle if selected_vehicle in ['5톤', '6톤', '7.5톤', '10톤'] else '5톤'

       if uses_ladder_from and ladder_from_floor and ladder_from_floor in ladder_prices and ladder_vehicle in ladder_prices[ladder_from_floor]:
            ladder_from_cost = ladder_prices[ladder_from_floor][ladder_vehicle]
            total_cost += ladder_from_cost
        
        if uses_ladder_to and ladder_to_floor and ladder_to_floor in ladder_prices and ladder_vehicle in ladder_prices[ladder_to_floor]:
            ladder_to_cost = ladder_prices[ladder_to_floor][ladder_vehicle]
            total_cost += ladder_to_cost
        
        # 스카이 비용 계산
        sky_cost = 0
        if 'from_method' in st.session_state and 'to_method' in st.session_state:
            if '스카이' in [st.session_state.from_method, st.session_state.to_method]:
                sky_cost = sky_base_price + (sky_hours - 2) * sky_extra_hour_price if sky_hours > 2 else sky_base_price
                total_cost += sky_cost
        
        # 추가 인원 비용 계산
        additional_person_total = (additional_men + additional_women) * additional_person_cost
        total_cost += additional_person_total
        
        # 폐기물 처리 비용 계산
        waste_cost = waste_tons * waste_disposal_cost if has_waste else 0
        total_cost += waste_cost
        
        # 특별 날짜 비용 계산
        special_day_total = sum(special_day_prices[date] for date in selected_dates if date != '평일(일반)')
        total_cost += special_day_total
        
        # 계산 결과 표시
        st.header("🧾 최종 견적 정보")
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📊 기본 정보")
            st.write(f"**고객명:** {st.session_state.get('customer_name', '')}")
            st.write(f"**전화번호:** {st.session_state.get('customer_phone', '')}")
            st.write(f"**이사 유형:** {st.session_state.move_type}")
            st.write(f"**이사일:** {st.session_state.get('moving_date', '')}")
            st.write(f"**견적일:** {estimate_date}")
            st.write(f"**출발지:** {st.session_state.get('from_location', '')}")
            st.write(f"**도착지:** {st.session_state.get('to_location', '')}")
        
        with col2:
            st.subheader("🚚 작업 정보")
            st.write(f"**선택 차량:** {selected_vehicle}")
            st.write(f"**출발지 층수:** {st.session_state.get('from_floor', '')} ({st.session_state.get('from_method', '')})")
            st.write(f"**도착지 층수:** {st.session_state.get('to_floor', '')} ({st.session_state.get('to_method', '')})")
            st.write(f"**기본 작업 인원:** 남성 {base_info['men']}명" + (f", 여성 {base_info.get('housewife', 0)}명" if 'housewife' in base_info else ""))
            st.write(f"**추가 인원:** 남성 {additional_men}명, 여성 {additional_women}명")
        
        # 비용 세부 내역 표시
        st.subheader("💵 비용 세부 내역")
        
        cost_items = [
            ["기본 이사 비용", f"{base_cost:,}원"],
            ["출발지 사다리차 비용", f"{ladder_from_cost:,}원"] if ladder_from_cost > 0 else None,
            ["도착지 사다리차 비용", f"{ladder_to_cost:,}원"] if ladder_to_cost > 0 else None,
            ["스카이 비용", f"{sky_cost:,}원 (기본 2시간 + 추가 {sky_hours-2}시간)"] if sky_cost > 0 else None,
            ["추가 인원 비용", f"{additional_person_total:,}원 ({additional_men + additional_women}명)"] if additional_person_total > 0 else None,
            ["폐기물 처리 비용", f"{waste_cost:,}원 ({waste_tons}톤)"] if waste_cost > 0 else None,
            ["특별 날짜 추가 비용", f"{special_day_total:,}원 ({', '.join([date for date in selected_dates if date != '평일(일반)'])})"] if special_day_total > 0 else None
        ]
        
        # None 값 제거
        cost_items = [item for item in cost_items if item is not None]
        
        # 비용 테이블 표시
        cost_df = pd.DataFrame(cost_items, columns=["항목", "금액"])
        st.table(cost_df)
        
        # 총 비용 표시
        st.subheader(f"💰 총 견적 비용: {total_cost:,}원")
        
        # 특이사항 표시
        if st.session_state.get('special_notes', ''):
            st.subheader("📝 특이 사항")
            st.info(st.session_state.get('special_notes', ''))
        
        # PDF 견적서 생성 기능
        st.subheader("📄 견적서 다운로드")
        if st.button("PDF 견적서 생성"):
            # PDF 생성 로직
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            styles = getSampleStyleSheet()
            elements = []
            
            # 제목
            title_style = styles["Title"]
            elements.append(Paragraph("이사 견적서", title_style))
            elements.append(Spacer(1, 12))
            
            # 기본 정보
            elements.append(Paragraph("■ 기본 정보", styles["Heading2"]))
            data = [
                ["고객명", st.session_state.get('customer_name', '')],
                ["전화번호", st.session_state.get('customer_phone', '')],
                ["이사 유형", st.session_state.move_type],
                ["이사일", str(st.session_state.get('moving_date', ''))],
                ["견적일", estimate_date],
                ["출발지", st.session_state.get('from_location', '')],
                ["도착지", st.session_state.get('to_location', '')]
            ]
            
            table = Table(data, colWidths=[100, 400])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(table)
            elements.append(Spacer(1, 12))
            
            # 작업 정보
            elements.append(Paragraph("■ 작업 정보", styles["Heading2"]))
            data = [
                ["선택 차량", selected_vehicle],
                ["출발지 층수", f"{st.session_state.get('from_floor', '')} ({st.session_state.get('from_method', '')})"],
                ["도착지 층수", f"{st.session_state.get('to_floor', '')} ({st.session_state.get('to_method', '')})"],
                ["기본 작업 인원", f"남성 {base_info['men']}명" + (f", 여성 {base_info.get('housewife', 0)}명" if 'housewife' in base_info else "")],
                ["추가 인원", f"남성 {additional_men}명, 여성 {additional_women}명"]
            ]
            
            table = Table(data, colWidths=[100, 400])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(table)
            elements.append(Spacer(1, 12))
            
            # 비용 상세 내역
            elements.append(Paragraph("■ 비용 상세 내역", styles["Heading2"]))
            data = [["항목", "금액"]]
            for item in cost_items:
                data.append(item)
            data.append(["총 견적 비용", f"{total_cost:,}원"])
            
            table = Table(data, colWidths=[250, 250])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(table)
            elements.append(Spacer(1, 12))
            
            # 특이 사항
            if st.session_state.get('special_notes', ''):
                elements.append(Paragraph("■ 특이 사항", styles["Heading2"]))
                elements.append(Paragraph(st.session_state.get('special_notes', ''), styles["Normal"]))
            
            # PDF 빌드
            doc.build(elements)
            
            # 다운로드 링크 생성
            pdf_data = buffer.getvalue()
            b64_pdf = base64.b64encode(pdf_data).decode('utf-8')
            
            # 현재 날짜를 파일명에 포함
            file_name = f"이사견적서_{st.session_state.get('customer_name', '고객')}_{datetime.now().strftime('%Y%m%d')}.pdf"
            
            href = f'<a href="data:application/octet-stream;base64,{b64_pdf}" download="{file_name}">📥 견적서 다운로드</a>'
            st.markdown(href, unsafe_allow_html=True)

# 앱 메인 실행
if __name__ == "__main__":
    st.sidebar.header("👋 통합 이사 비용 계산기")
    st.sidebar.write("이 앱은 이사 비용을 간편하게 계산할 수 있는 도구입니다.")
    st.sidebar.write("Step 1: 고객 정보 입력")
    st.sidebar.write("Step 2: 물품 선택")
    st.sidebar.write("Step 3: 비용 계산")
    
    st.sidebar.header("🏢 회사 정보")
    st.sidebar.write("회사명: 이사천국")
    st.sidebar.write("전화번호: 1234-5678")
    st.sidebar.write("주소: 서울시 이사구 이사동 123-45")
    
    # 현재 날짜 표시
    st.sidebar.header("📅 오늘 날짜")
    st.sidebar.write(datetime.now(pytz.timezone('Asia/Seoul')).strftime("%Y년 %m월 %d일"))
