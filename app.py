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
from reportlab.lib.units import mm  
from io import BytesIO  
  
# 한글 폰트 등록  
pdfmetrics.registerFont(TTFont('NanumGothic', 'NanumGothic.ttf'))  
  
# 로고 표시 (화면 좌측 상단)  
st.image("logo.png", width=150)  
  
# --- 고객 기본정보 입력 ---  
st.header("📝 고객 기본 정보")  
col1, col2 = st.columns(2)  
  
with col1:  
    customer_name = st.text_input("👤 고객명", value="")  
    from_location = st.text_input("📍 출발지", value="")  
  
with col2:  
    customer_phone = st.text_input("📞 전화번호", value="")  
    to_location = st.text_input("📍 도착지", value="")  
  
moving_date = st.date_input("🚚 이사일")  
  
# 견적일 자동 표시 (현재시간)  
kst = pytz.timezone('Asia/Seoul')  
estimate_date = datetime.now(kst).strftime("%Y-%m-%d %H:%M")  
  
  
# --- 작업 조건 입력 ---  
st.header("🏢 작업 조건")  
col1, col2 = st.columns(2)  
  
method_options = ["사다리차", "승강기", "계단", "스카이"]  
  
with col1:  
    from_floor = st.text_input("🔼 출발지 층수", value="")  
    from_method = st.selectbox("🛗 출발지 작업 방법", method_options, key='from_method')  
  
with col2:  
    to_floor = st.text_input("🔽 도착지 층수", value="")  
    to_method = st.selectbox("🛗 도착지 작업 방법", method_options, key='to_method')  
  
st.header("🗒️ 특이 사항 입력")  
special_notes = st.text_area("특이 사항이 있으면 입력해주세요.", height=100, value="")  
  
# --- 품목 데이터 ---  
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
  
  
# --- 품목 선택 및 박스 계산 ---  
st.header("📋 품목 선택")  
selected_items = {}  
additional_boxes = {"중대박스": 0, "옷박스": 0, "중박스": 0}  
  
for section, item_list in items.items():  
    with st.expander(f"{section} 품목 선택"):  
        cols = st.columns(3)  
        items_list = list(item_list.items())  
        third_len = len(items_list) // 3 + (len(items_list) % 3 > 0)  
        for idx, (item, (volume, weight)) in enumerate(items_list):  
            with cols[idx // third_len]:  
                unit = "칸" if item == "장롱" else "개"  
                qty = st.number_input(f"{item}", min_value=0, step=1, key=f"{section}_{item}")  
                if qty > 0:  
                    selected_items[item] = (qty, unit)  
                    if item == "장롱":  
                        additional_boxes["중대박스"] += qty * 5  
                    if item == "옷장":  
                        additional_boxes["옷박스"] += qty * 3  
                    if item == "서랍장(3단)":  
                        additional_boxes["중박스"] += qty * 3  
                    if item == "서랍장(5단)":  
                        additional_boxes["중박스"] += qty * 5  
  
# 박스 부피 계산  
box_volumes = {"중대박스": 0.1875, "옷박스": 0.219, "중박스": 0.1}  
total_volume = sum(items[sec][item][0] * qty for sec in items for item, (qty, _) in selected_items.items() if item in items[sec])  
total_volume += sum(box_volumes[box] * count for box, count in additional_boxes.items())  
  
# 차량 추천 및 여유공간 계산 (적재 효율 반영)  
def recommend_vehicle(total_volume, total_weight):  
    vehicles = [("1톤", 5, 1000), ("2.5톤", 12, 2500), ("5톤", 25, 5000), ("6톤", 30, 6000),  
                ("7.5톤", 40, 7500), ("10톤", 50, 10000), ("15톤", 70, 15000), ("20톤", 90, 20000)]  
    loading_efficiency = 0.90  
  
    for name, capacity, max_weight in vehicles:  
        effective_capacity = capacity * loading_efficiency  
        if total_volume <= effective_capacity and total_weight <= max_weight:  
            remaining_space = (effective_capacity - total_volume) / effective_capacity * 100  
            return name, remaining_space  
  
    return "20톤 이상 차량 필요", 0  
  
# 총 무게 계산  
total_weight = sum(items[sec][item][1] * qty for sec in items for item, (qty, _) in selected_items.items() if item in items[sec])  
  
# 차량 추천 및 여유 공간 계산  
recommended_vehicle, remaining_space = recommend_vehicle(total_volume, total_weight)  
  
# --- 결과 출력 ---  
st.subheader("✨ 실시간 견적 결과 ✨")  
col1, col2 = st.columns(2)  
  
with col1:  
    st.write(f"👤 고객명: {customer_name if customer_name else '미입력'}")  
    st.write(f"📞 전화번호: {customer_phone if customer_phone else '미입력'}")  
    st.write(f"📍 출발지: {from_location if from_location else '미입력'} ({from_floor if from_floor else '미입력'} {from_method})")  
  
with col2:  
    st.write(f"📍 도착지: {to_location if to_location else '미입력'} ({to_floor if to_floor else '미입력'} {to_method})")  
    st.write(f"📅 견적일: {estimate_date}")  
    st.write(f"🚚 이사일: {moving_date}")  
  
st.write("📋 **선택한 품목 리스트:**")  
if not selected_items:
    st.write("선택한 품목이 없습니다.")
else:
    cols = st.columns(3)  # 3열로 품목 리스트 표시 개선  
    items_list = list(selected_items.items())  
    third_len = len(items_list) // 3 + (len(items_list) % 3 > 0)  
    for idx, (item, (qty, unit)) in enumerate(items_list):  
        with cols[idx // third_len]:  
            st.write(f"- {item}: {qty}{unit}")  
  
# 특이 사항 출력  
if special_notes.strip():  
    st.info(f"🗒️ **특이 사항:** {special_notes}")  
  
st.success(f"📐 총 부피: {total_volume:.2f} m³")  
st.success(f"🚛 추천 차량: {recommended_vehicle}")  
st.info(f"🧮 차량의 여유 공간: {remaining_space:.2f}%")  
  
# PDF 생성 함수 - 상세 견적서 (품목 포함)
def create_detailed_pdf():  
    buffer = BytesIO()  
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=15*mm, leftMargin=15*mm, topMargin=15*mm, bottomMargin=15*mm)  
      
    # 스타일 설정  
    styles = getSampleStyleSheet()  
    styles.add(ParagraphStyle(name='Korean', fontName='NanumGothic', fontSize=10, leading=12))  
    styles.add(ParagraphStyle(name='KoreanTitle', fontName='NanumGothic', fontSize=16, leading=20, alignment=1))  
    styles.add(ParagraphStyle(name='KoreanSubTitle', fontName='NanumGothic', fontSize=12, leading=14, alignment=0))  
      
    # 문서 내용 구성  
    content = []  
      
    # 제목  
    content.append(Paragraph("이사 견적서 (상세)", styles['KoreanTitle']))  
    content.append(Spacer(1, 10*mm))  
      
    # 고객 정보 테이블  
    customer_data = [  
        ["고객명", customer_name if customer_name else "미입력", "전화번호", customer_phone if customer_phone else "미입력"],  
        ["출발지", f"{from_location if from_location else '미입력'} ({from_floor if from_floor else '미입력'} {from_method})", 
         "도착지", f"{to_location if to_location else '미입력'} ({to_floor if to_floor else '미입력'} {to_method})"],  
        ["견적일", estimate_date, "이사일", moving_date.strftime("%Y-%m-%d")]  
    ]  
      
    t = Table(customer_data, colWidths=[40*mm, 50*mm, 40*mm, 50*mm])  
    t.setStyle(TableStyle([  
        ('FONTNAME', (0, 0), (-1, -1), 'NanumGothic'),  
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),  
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),  
        ('BACKGROUND', (2, 0), (2, -1), colors.lightgrey),  
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  
    ]))  
    content.append(t)  
    content.append(Spacer(1, 7*mm))  
      
    # 품목 리스트 타이틀  
    content.append(Paragraph("선택한 품목 리스트", styles['KoreanSubTitle']))  
    content.append(Spacer(1, 3*mm))  
      
    # 품목 테이블 생성  
    if selected_items:  
        item_data = [["품목", "수량", "단위"]]  
        for item, (qty, unit) in selected_items.items():  
            item_data.append([item, str(qty), unit])  
          
        item_table = Table(item_data, colWidths=[110*mm, 30*mm, 30*mm])  
        item_table.setStyle(TableStyle([  
            ('FONTNAME', (0, 0), (-1, -1), 'NanumGothic'),  
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),  
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),  
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  
        ]))  
        content.append(item_table)  
    else:  
        content.append(Paragraph("선택한 품목이 없습니다.", styles['Korean']))  
      
    content.append(Spacer(1, 7*mm))  
      
    # 추가 박스 정보  
    if any(additional_boxes.values()):  
        content.append(Paragraph("추가 필요 박스", styles['KoreanSubTitle']))  
        content.append(Spacer(1, 3*mm))  
          
        box_data = [["박스 종류", "수량"]]  
        for box, count in additional_boxes.items():  
            if count > 0:  
                box_data.append([box, str(count)])  
          
        box_table = Table(box_data, colWidths=[110*mm, 60*mm])  
        box_table.setStyle(TableStyle([  
            ('FONTNAME', (0, 0), (-1, -1), 'NanumGothic'),  
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),  
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),  
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  
        ]))  
        content.append(box_table)  
        content.append(Spacer(1, 7*mm))  
      
    # 견적 결과  
    content.append(Paragraph("견적 결과", styles['KoreanSubTitle']))  
    content.append(Spacer(1, 3*mm))  
      
    result_data = [  
        ["총 부피", f"{total_volume:.2f} m³"],  
        ["추천 차량", recommended_vehicle],  
        ["차량 여유 공간", f"{remaining_space:.2f}%"]  
    ]  
      
    result_table = Table(result_data, colWidths=[80*mm, 90*mm])  
    result_table.setStyle(TableStyle([  
        ('FONTNAME', (0, 0), (-1, -1), 'NanumGothic'),  
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),  
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),  
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  
    ]))  
    content.append(result_table)  
    content.append(Spacer(1, 7*mm))  
      
    # 특이 사항  
    if special_notes.strip():  
        content.append(Paragraph("특이 사항", styles['KoreanSubTitle']))  
        content.append(Spacer(1, 3*mm))  
        content.append(Paragraph(special_notes, styles['Korean']))  
      
    # PDF 문서 생성  
    doc.build(content)  
    return buffer

# PDF 생성 함수 - 계약용 간소화 견적서 (품목 제외)
def create_contract_pdf():
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=15*mm, leftMargin=15*mm, topMargin=15*mm, bottomMargin=15*mm)
    
    # 스타일 설정
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Korean', fontName='NanumGothic', fontSize=10, leading=12))
    styles.add(ParagraphStyle(name='KoreanTitle', fontName='NanumGothic', fontSize=16, leading=20, alignment=1))
    styles.add(ParagraphStyle(name='KoreanSubTitle', fontName='NanumGothic', fontSize=12, leading=14, alignment=0))
    
    # 문서 내용 구성
    content = []
    
    # 제목
    content.append(Paragraph("이사 계약서", styles['KoreanTitle']))
    content.append(Spacer(1, 10*mm))
    
    # 고객 정보 테이블
    customer_data = [
        ["고객명", customer_name if customer_name else "미입력", "전화번호", customer_phone if customer_phone else "미입력"],
        ["출발지", f"{from_location if from_location else '미입력'} ({from_floor if from_floor else '미입력'} {from_method})", 
         "도착지", f"{to_location if to_location else '미입력'} ({to_floor if to_floor else '미입력'} {to_method})"],
        ["견적일", estimate_date, "이사일", moving_date.strftime("%Y-%m-%d")]
    ]
    
    t = Table(customer_data, colWidths=[40*mm, 50*mm, 40*mm, 50*mm])
    t.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'NanumGothic'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('BACKGROUND', (2, 0), (2, -1), colors.lightgrey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    content.append(t)
    content.append(Spacer(1, 7*mm))
    
    # 견적 결과
    content.append(Paragraph("견적 결과", styles['KoreanSubTitle']))
    content.append(Spacer(1, 3*mm))
    
    result_data = [
        ["총 부피", f"{total_volume:.2f} m³"],
        ["추천 차량", recommended_vehicle],
        ["차량 여유 공간", f"{remaining_space:.2f}%"]
    ]
    
    result_table = Table(result_data, colWidths=[80*mm, 90*mm])
    result_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'NanumGothic'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    content.append(result_table)
    content.append(Spacer(1, 7*mm))
    
    # 특이 사항
    if special_notes.strip():
        content.append(Paragraph("특이 사항", styles['KoreanSubTitle']))
        content.append(Spacer(1, 3*mm))
        content.append(Paragraph(special_notes, styles['Korean']))
    
    # 계약 서명란 추가
    content.append(Spacer(1, 20*mm))
    content.append(Paragraph("계약 동의", styles['KoreanSubTitle']))
    content.append(Spacer(1, 3*mm))
    
    contract_text = "본인은 위 내용에 대해 동의하며, 이사 서비스를 계약합니다."
    content.append(Paragraph(contract_text, styles['Korean']))
    content.append(Spacer(1, 10*mm))
    
    # 서명 테이블
    signature_data = [
        ["고객 서명", "", "날짜", ""]
    ]
    
    sig_table = Table(signature_data, colWidths=[40*mm, 60*mm, 30*mm, 40*mm])
    sig_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'NanumGothic'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (0, 0), colors.lightgrey),
        ('BACKGROUND', (2, 0), (2, 0), colors.lightgrey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    content.append(sig_table)
    
    # PDF 문서 생성
    doc.build(content)
    return buffer
  
# PDF 다운로드 버튼들
col1, col2 = st.columns(2)

with col1:
    if st.button("상세 견적서 다운로드"):
        pdf_buffer = create_detailed_pdf()
        pdf_data = pdf_buffer.getvalue()
        b64_pdf = base64.b64encode(pdf_data).decode('utf-8')
          
        # 다운로드 링크 생성
        pdf_filename = f"{customer_name if customer_name else '고객'}_이사_상세견적서.pdf"
        st.markdown(
            f'<a href="data:application/octet-stream;base64,{b64_pdf}" download="{pdf_filename}">📥 상세 견적서 다운로드</a>',
            unsafe_allow_html=True
        )
        st.success("상세 견적서가 생성되었습니다. 위 링크를 클릭하여 다운로드하세요.")

with col2:
    if st.button("계약용 견적서 다운로드"):
        pdf_buffer = create_contract_pdf()
        pdf_data = pdf_buffer.getvalue()
        b64_pdf = base64.b64encode(pdf_data).decode('utf-8')
          
        # 다운로드 링크 생성
        pdf_filename = f"{customer_name if customer_name else '고객'}_이사_계약서.pdf"
        st.markdown(
            f'<a href="data:application/octet-stream;base64,{b64_pdf}" download="{pdf_filename}">📥 계약용 견적서 다운로드</a>',
            unsafe_allow_html=True
        )
        st.success("계약용 견적서가 생성되었습니다. 위 링크를 클릭하여 다운로드하세요.")
