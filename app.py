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

# 사다리 기본 가격 (층수별)
ladder_prices = {
    '사용안함': 0,
    '2~5층': 150000,
    '6~7층': 160000,
    '8~9층': 170000,
    '10~11층': 180000,
    '12~13층': 190000,
    '14층': 200000,
    '15층': 210000,
    '16층': 220000,
    '17층': 230000,
    '18층': 240000,
    '19층': 250000,
    '20층': 280000,
    '21층': 310000,
    '22층': 340000,
    '23층': 370000,
    '24층': 400000,
    '25층 이상': 450000
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

out_method = st.selectbox('나갈 때:', ['계단 🪜', '승강기 🛗', '사다리 🪜', '스카이 🚁'])
in_method = st.selectbox('들어갈 때:', ['계단 🪜', '승강기 🛗', '사다리 🪜', '스카이 🚁'])

# 사다리 옵션
ladder_floor = '사용안함'
ladder_weight = '기본'
if '사다리 🪜' in [out_method, in_method]:
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
    
    # 사다리 비용 계산 (층수 + 무게)
    if out_method == '사다리 🪜' or in_method == '사다리 🪜':
        total_cost += ladder_prices[ladder_floor] + ladder_weight_prices[ladder_weight]
    
    # 스카이 비용 계산
    if out_method == '스카이 🚁' or in_method == '스카이 🚁':
        total_cost += sky_base_price + (sky_hours - 2) * sky_extra_hour_price
    
    # 특별 날짜 비용 계산 (중복 적용)
    for date_type in selected_dates:
        if date_type != '평일(일반)':  # 평일은 추가 비용 없음
            total_cost += special_day_prices[date_type]
    
    st.subheader('📌 총 예상 이사 비용 및 인원:')
    
    # 비용 세부 내역 표시
    st.write("### 💵 비용 세부 내역:")
    st.write(f"- 기본 이사 비용: {base_cost:,}원")
    
    if out_method == '사다리 🪜' or in_method == '사다리 🪜':
        st.write(f"- 사다리 층수 비용 ({ladder_floor}): {ladder_prices[ladder_floor]:,}원")
        st.write(f"- 사다리 무게 추가 비용 ({ladder_weight}): {ladder_weight_prices[ladder_weight]:,}원")
    
    if out_method == '스카이 🚁' or in_method == '스카이 🚁':
        sky_cost = sky_base_price + (sky_hours - 2) * sky_extra_hour_price
        st.write(f"- 스카이 사용 비용 ({sky_hours}시간): {sky_cost:,}원")
    
    special_days_cost = sum([special_day_prices[date] for date in selected_dates if date != '평일(일반)'])
    if special_days_cost > 0:
        st.write(f"- 특별 날짜 추가 비용: {special_days_cost:,}원")
    
    st.write(f"### 총 비용: {total_cost:,}원 💸")
    
    # 인원 정보 표시
    st.write("### 👨‍👩‍👧 투입 인원:")
    if move_type == '가정 이사 🏠':
        st.write(f"- 남성 작업자 👨: {base_info['men']}명")
        st.write(f"- 주부사원 👩: {base_info['housewife']}명")
    else:
        st.write(f"- 남성 작업자 👨: {base_info['men']}명")
