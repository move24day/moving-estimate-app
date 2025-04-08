import streamlit as st
from datetime import datetime
import pytz
import base64
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO

# 한글 폰트 설정
pdfmetrics.registerFont(TTFont('NanumGothic', 'NanumGothic.ttf'))

# 로고 표시
try:
    st.image("logo.png", width=150)
except:
    st.write("로고 이미지를 찾을 수 없습니다.")

# 고객 정보 입력
st.header("📝 고객 기본 정보")
col1, col2 = st.columns(2)
with col1:
    customer_name = st.text_input("👤 고객명")
    from_location = st.text_input("📍 출발지")
with col2:
    customer_phone = st.text_input("📞 전화번호")
    to_location = st.text_input("📍 도착지")

moving_date = st.date_input("🚚 이사일")

kst = pytz.timezone('Asia/Seoul')
estimate_date = datetime.now(kst).strftime("%Y-%m-%d %H:%M")

# 작업 조건 입력
st.header("🏢 작업 조건")
col1, col2 = st.columns(2)
method_options = ["사다리차", "승강기", "계단", "스카이"]
with col1:
    from_floor = st.number_input("🔼 출발지 층수", min_value=1, step=1)
    from_method = st.selectbox("🛗 출발지 작업 방법", method_options)
with col2:
    to_floor = st.number_input("🔽 도착지 층수", min_value=1, step=1)
    to_method = st.selectbox("🛗 도착지 작업 방법", method_options, key='to')

special_notes = st.text_area("🗒️ 특이 사항 입력", height=100)

# 품목 분류
items = {
    '가정': {
        '장롱': (1.05,120),'싱글침대':(1.2,60),'더블침대':(1.7,70),'돌침대':(2.5,150),'서랍장(3단)':(0.4,30),'서랍장(5단)':(0.75,40),
        '피아노(일반)':(1.5,200),'피아노(디지털)':(0.5,50),'소파(1인용)':(0.4,30),'소파(3인용)':(0.6,50),'안마기':(0.9,50),
        '양문형냉장고':(1.0,120),'4도어냉장고':(1.2,130),'김치냉장고(스탠드형)':(0.8,90),'김치냉장고(일반형)':(0.6,60),
        '주방용선반(수납장)':(1.1,80),'세탁기':(0.5,80),'건조기':(0.5,80),'신발장':(1.1,60)
    },
    '기타': {
        '옷장':(1.05,160),'화장대':(0.32,80),'책장':(0.96,56),'책상&의자':(0.25,40),'옷행거':(0.35,40),
        '소파테이블':(0.65,35),'TV(45인치)':(0.15,15),'TV(75인치)':(0.3,30),'장식장':(0.75,40),'오디오및스피커':(0.1,20),
        '에어컨':(0.15,30),'공기청정기':(0.1,8),'식탁(4인)':(0.4,50),'식탁(6인)':(0.6,70),'가스레인지및인덕션':(0.1,10),
        '여행가방및캐리어':(0.15,5),'화분':(0.2,10),'스타일러스':(0.5,20)
    }
}

selected_items = {}
total_volume, total_weight = 0,0

st.header("📋 품목 선택")
for category, item_dict in items.items():
    with st.expander(f"{category} 품목 선택"):
        cols = st.columns(3)
        for idx,(item,(vol,wt)) in enumerate(item_dict.items()):
            with cols[idx%3]:
                qty = st.number_input(f"{item}",min_value=0,step=1,key=f"{category}_{item}")
                if qty>0:
                    selected_items[item]=(qty,"개")
                    total_volume+=vol*qty
                    total_weight+=wt*qty

# 차량 추천
vehicles=[("1톤",5,1000),("2.5톤",12,2500),("5톤",25,5000),("6톤",30,6000),("7.5톤",40,7500),("10톤",50,10000),("15톤",70,15000),("20톤",90,20000)]
loading_efficiency=0.9
for name,cap,wt in vehicles:
    if total_volume<=cap*loading_efficiency and total_weight<=wt:
        recommended_vehicle=name
        remaining_space=(cap*loading_efficiency-total_volume)/(cap*loading_efficiency)*100
        break
else:
    recommended_vehicle="20톤 이상 차량 필요"
    remaining_space=0

st.success(f"📐 총 부피: {total_volume:.2f} m³")
st.success(f"🚛 추천 차량: {recommended_vehicle}")
st.info(f"🧮 여유 공간: {remaining_space:.2f}%")

# PDF 생성 및 다운로드
# [기존 PDF 생성 로직에서 한글 폰트 스타일 적용한 코드로 교체 필수]
# (PDF 코드 생략됨 - 글자 수 제한으로 여기에 간략화)

if st.button("PDF 견적서 다운로드"):
    if customer_name and customer_phone and from_location and to_location:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='Korean', fontName='NanumGothic', fontSize=12))
        content = [Paragraph("이사 견적서", styles['Korean'])]  # (예시)
        doc.build(content)
        pdf_data = buffer.getvalue()
        b64_pdf = base64.b64encode(pdf_data).decode('utf-8')
        st.markdown(f'<a href="data:application/octet-stream;base64,{b64_pdf}" download="estimate.pdf">📥 PDF 다운로드</a>',unsafe_allow_html=True)
        st.success("견적서 생성 완료.")
    else:
        st.error("모든 정보를 입력하세요.")
