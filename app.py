import streamlit as st

# 차량 톤수와 유형에 따른 기본 비용 (예시 비용)
office_vehicle_prices = {
    '1톤': {'price': 400000, 'men': 2},
    '2.5톤': {'price': 650000, 'men': 2},
    '3.5톤': {'price': 700000, 'men': 2},
    '5톤': {'price': 950000, 'men': 3},
    '6톤': {'price': 1050000, 'men': 3},
    '7.5톤': {'price': 1300000, 'men': 4},
    '10톤': {'price': 1700000, 'men': 5}
}

home_vehicle_prices = {
    '1톤': {'price': 400000, 'men': 2, 'housewife': 0},
    '2.5톤': {'price': 900000, 'men': 2, 'housewife': 1},
    '3.5톤': {'price': 950000, 'men': 2, 'housewife': 1},
    '5톤': {'price': 1200000, 'men': 3, 'housewife': 1},
    '6톤': {'price': 1350000, 'men': 3, 'housewife': 1},
    '7.5톤': {'price': 1750000, 'men': 4, 'housewife': 1},
    '10톤': {'price': 2300000, 'men': 5, 'housewife': 1}
}

# 사다리 비용 (층수와 톤수에 따른 만원 단위, 표 기준)
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

# 작은 톤수 차량 사다리 가격 적용 (표에 없는 톤수에 대한 처리)
small_vehicle_ladder_discount = {
    '1톤': 0.7,  # 5톤 가격의 70%
    '2.5톤': 0.8,  # 5톤 가격의 80%
    '3.5톤': 0.9   # 5톤 가격의 90%
}

# 사다리 무게별 추가 비용
ladder_weight_prices = {
    '기본': 0,
    '100kg 이상': 50000,
    '200kg 이상': 100000,
    '300kg 이상': 150000,
    '400kg 이상': 200000,
    '500kg 이상': 250000
}

special_day_prices = {
    '평일(일반)': 0,
    '이사많은날 🏠': 100000,
    '손없는날 ✋': 100000,
    '월말 📅': 100000,
    '공휴일 🎉': 100000
}

sky_base_price = 300000
sky_extra_hour_price = 50000

st.title('🚛 이사 비용 계산기')

move_type = st.radio('🏢 이사 유형 선택:', ('가정 이사 🏠', '사무실 이사 🏢'))

selected_vehicle = st.selectbox('🚚 차량 톤수 선택:', list(home_vehicle_prices.keys()))

st.subheader('📦 이삿짐 이동 방법')

out_method = st.selectbox('나갈 때:', ['승강기 🛗', '계단 🪜', '사다리 🪜', '스카이 🚁'])
in_method = st.selectbox('들어갈 때:', ['승강기 🛗', '계단 🪜', '사다리 🪜', '스카이 🚁'])

# 사다리 옵션
ladder_floor = None
ladder_weight = '기본'
uses_ladder = '사다리 🪜' in [out_method, in_method]

if uses_ladder:
    col1, col2 = st.columns(2)
    with col1:
        ladder_floor = st.selectbox('사다리 사용 층수 선택:', list(ladder_prices.keys()))
    with col2:
        ladder_weight = st.selectbox('사다리 무게 옵션:', list(ladder_weight_prices.keys()))

# 스카이 옵션
sky_hours = 2
if '스카이 🚁' in [out_method, in_method]:
    sky_hours = st.number_input('스카이 사용 시간 (기본 2시간 포함) ⏱️', min_value=2, step=1)

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

if st.button('💰 이사 비용 계산하기'):
    if move_type == '가정 이사 🏠':
        base_info = home_vehicle_prices[selected_vehicle]
    else:
        base_info = office_vehicle_prices[selected_vehicle]
    
    base_cost = base_info['price']
    total_cost = base_cost
    
    # 사다리 비용 계산 (층수 + 톤수에 따른)
    ladder_cost = 0
    if uses_ladder and ladder_floor:
        # 5톤, 6톤, 7.5톤, 10톤 차량은 표에서 직접 가격 가져오기
        if selected_vehicle in ['5톤', '6톤', '7.5톤', '10톤']:
            ladder_cost += ladder_prices[ladder_floor][selected_vehicle]
        # 작은 차량은 5톤 가격에서 할인된 가격 적용
        else:
            discount_factor = small_vehicle_ladder_discount.get(selected_vehicle, 0.8)  # 기본 80% 적용
            ladder_cost += int(ladder_prices[ladder_floor]['5톤'] * discount_factor)
        
        # 무게에 따른 추가 비용
        ladder_cost += ladder_weight_prices[ladder_weight]
        
        total_cost += ladder_cost
    
    # 스카이 비용 계산
    sky_cost = 0
    if '스카이 🚁' in [out_method, in_method]:
        sky_cost = sky_base_price + (sky_hours - 2) * sky_extra_hour_price
        total_cost += sky_cost
    
    # 특별 날짜 비용 계산 (중복 적용)
    special_days_cost = 0
    for date_type in selected_dates:
        if date_type != '평일(일반)':  # 평일은 추가 비용 없음
            special_days_cost += special_day_prices[date_type]
    
    total_cost += special_days_cost
    
    st.subheader('📌 총 예상 이사 비용 및 인원:')
    
    # 비용 세부 내역 표시
    st.write("### 💵 비용 세부 내역:")
    st.write(f"- 기본 이사 비용: {base_cost:,}원")
    
    if uses_ladder and ladder_floor:
        st.write(f"- 사다리 비용 ({ladder_floor}, {selected_vehicle}, {ladder_weight}): {ladder_cost:,}원")
    
    if '스카이 🚁' in [out_method, in_method]:
        st.write(f"- 스카이 사용 비용 ({sky_hours}시간): {sky_cost:,}원")
    
    if special_days_cost > 0:
        special_days_text = ", ".join([d for d in selected_dates if d != '평일(일반)'])
        st.write(f"- 특별 날짜 추가 비용 ({special_days_text}): {special_days_cost:,}원")
    
    st.write(f"### 총 비용: {total_cost:,}원 💸")
    
    # 인원 정보 표시
    st.write("### 👨‍👩‍👧 투입 인원:")
    if move_type == '가정 이사 🏠':
        st.write(f"- 남성 작업자 👨: {base_info['men']}명")
        st.write(f"- 주부사원 👩: {base_info['housewife']}명")
    else:
        st.write(f"- 남성 작업자 👨: {base_info['men']}명")
