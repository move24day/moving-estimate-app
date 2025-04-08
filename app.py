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

# 사다리 비용 (층수와 톤수에 따른, 만원 단위를 원 단위로 변환)
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

special_day_prices = {
    '평일(일반)': 0,
    '이사많은날 🏠': 100000,
    '손없는날 ✋': 100000,
    '월말 📅': 100000,
    '공휴일 🎉': 100000
}

# 추가 인원 비용
additional_person_cost = 200000  # 추가 인원 1명당 20만원

# 폐기물 처리 비용
waste_disposal_cost = 300000  # 폐기물 1톤당 30만원

sky_base_price = 300000
sky_extra_hour_price = 50000

st.title('🚛 이사 비용 계산기')

move_type = st.radio('🏢 이사 유형 선택:', ('가정 이사 🏠', '사무실 이사 🏢'))

selected_vehicle = st.selectbox('🚚 차량 톤수 선택:', list(home_vehicle_prices.keys()))

st.subheader('📦 이삿짐 이동 방법')

out_method = st.selectbox('나갈 때:', ['승강기 🛗', '계단 🪜', '사다리 🪜', '스카이 🚁'])
in_method = st.selectbox('들어갈 때:', ['승강기 🛗', '계단 🪜', '사다리 🪜', '스카이 🚁'])

# 사다리 옵션
ladder_floor = '사용안함'
uses_ladder = '사다리 🪜' in [out_method, in_method]

if uses_ladder:
    ladder_floor = st.selectbox('사다리 사용 층수 선택:', list(ladder_prices.keys()))
    st.info('📊 사다리 비용은 차량 톤수와 층수에 따라 자동 계산됩니다.')

# 스카이 옵션
sky_hours = 2
if '스카이 🚁' in [out_method, in_method]:
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
has_waste = st.checkbox('폐기물 처리 필요')
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

if st.button('💰 이사 비용 계산하기'):
    if move_type == '가정 이사 🏠':
        base_info = home_vehicle_prices[selected_vehicle]
    else:
        base_info = office_vehicle_prices[selected_vehicle]
    
    base_cost = base_info['price']
    total_cost = base_cost
    
    # 사다리 비용 계산 (층수 + 톤수에 따른)
    ladder_cost = 0
    if uses_ladder and ladder_floor != '사용안함':
        # 5톤, 6톤, 7.5톤, 10톤 차량은 표에서 직접 가격 가져오기
        if selected_vehicle in ['5톤', '6톤', '7.5톤', '10톤']:
            ladder_cost = ladder_prices[ladder_floor][selected_vehicle]
        # 작은 차량은 5톤 가격에서 할인된 가격 적용
        else:
            discount_factor = small_vehicle_ladder_discount.get(selected_vehicle, 0.8)  # 기본 80% 적용
            ladder_cost = int(ladder_prices[ladder_floor]['5톤'] * discount_factor)
        
        total_cost += ladder_cost
    
    # 스카이 비용 계산
    sky_cost = 0
    if '스카이 🚁' in [out_method, in_method]:
        sky_cost = sky_base_price + (sky_hours - 2) * sky_extra_hour_price
        total_cost += sky_cost
    
    # 추가 인원 비용 계산
    additional_people = additional_men + additional_women
    additional_people_cost = 0
    if additional_people > 0:
        additional_people_cost = additional_person_cost * additional_people
        total_cost += additional_people_cost
    
    # 폐기물 처리 비용 계산
    waste_cost = 0
    if has_waste and waste_tons > 0:
        waste_cost = int(waste_disposal_cost * waste_tons)
        total_cost += waste_cost
    
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
    
    if uses_ladder and ladder_floor != '사용안함':
        st.write(f"- 사다리 비용 ({ladder_floor}, {selected_vehicle}): {ladder_cost:,}원")
    
    if '스카이 🚁' in [out_method, in_method]:
        st.write(f"- 스카이 사용 비용 ({sky_hours}시간): {sky_cost:,}원")
    
    if additional_people > 0:
        st.write(f"- 추가 인원 비용 (남성 {additional_men}명, 여성 {additional_women}명): {additional_people_cost:,}원")
    
    if has_waste and waste_tons > 0:
        st.write(f"- 폐기물 처리 비용 ({waste_tons}톤): {waste_cost:,}원")
    
    if special_days_cost > 0:
        special_days_text = ", ".join([d for d in selected_dates if d != '평일(일반)'])
        st.write(f"- 특별 날짜 추가 비용 ({special_days_text}): {special_days_cost:,}원")
    
    st.write(f"### 총 비용: {total_cost:,}원 💸")
    
    # 인원 정보 표시
    st.write("### 👨‍👩‍👧 투입 인원:")
    if move_type == '가정 이사 🏠':
        total_men = base_info['men'] + additional_men
        total_women = base_info.get('housewife', 0) + additional_women
        st.write(f"- 남성 작업자 👨: {total_men}명 (기본 {base_info['men']}명 + 추가 {additional_men}명)")
        st.write(f"- 여성 작업자 👩: {total_women}명 (기본 {base_info.get('housewife', 0)}명 + 추가 {additional_women}명)")
    else:
        total_men = base_info['men'] + additional_men
        st.write(f"- 남성 작업자 👨: {total_men}명 (기본 {base_info['men']}명 + 추가 {additional_men}명)")
        if additional_women > 0:
            st.write(f"- 여성 작업자 👩: {additional_women}명")
    
    # 사다리 사용 시 가격표 보여주기
    if uses_ladder and ladder_floor != '사용안함':
        st.subheader('📊 사다리 요금표 (만원)')
        
        # 사다리 요금표 데이터 준비
        ladder_table_data = []
        for floor in ladder_prices.keys():
            row = [floor]
            for ton in ['5톤', '6톤', '7.5톤', '10톤']:
                # 만원 단위로 표시 (10으로 나누기)
                row.append(int(ladder_prices[floor][ton] / 10000))
            ladder_table_data.append(row)
        
        # 표 열 이름
        columns = ['층수', '5톤', '6톤', '7.5톤', '10톤']
        
        # DataFrame 생성하여 표시
        import pandas as pd
        ladder_df = pd.DataFrame(ladder_table_data, columns=columns)
        st.table(ladder_df)
