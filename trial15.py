import streamlit as st
import random
import string
from datetime import datetime, timedelta

st.markdown(
    """<style>
    .stApp {
        background-color: #fffbea;
        color: #000;
    }
    .stButton>button {
        background-color: #f5b800;
        color: black;
        border: none;
    }
    </style>""",
    unsafe_allow_html=True
)

if 'cards_db' not in st.session_state:
    st.session_state.cards_db = {}
if 'transactions_db' not in st.session_state:
    st.session_state.transactions_db = []
if 'custom_allowed_sites_input' not in st.session_state:
    st.session_state.custom_allowed_sites_input = "amazon.com\nkbstar.com\ntemu.com"


def ai_recommend():
    return {
        "limit": random.choice([50, 100, 150, 200, 500]),
        "duration_days": random.choice([1, 3, 7, 14, 30]),
        "restricted_sites": random.choice([True, False])
    }


def generate_card_id():
    num_part = ''.join(random.choices(string.digits, k=3))
    alpha_part = ''.join(random.choices(string.ascii_uppercase, k=3))
    return f"CARD{num_part}-{alpha_part}"


def calculate_risk(payment_amount, card, site, country):
    risk = random.uniform(0.1, 1.0)
    reasons_list = [
        '결제금액이 카드 한도 근접',
        '고위험 시간대 사용',
        '미등록 기기 사용',
        '고위험 IP 접근',
        '과거 신고 내역 다수',
        '거래 패턴 이상 감지'
    ]

    if payment_amount > 0.7 * card['limit']:
        risk += 0.05

    if card['restricted'] and card.get('allowed_sites') and site not in card['allowed_sites']:
        risk += 0.1

    risk = min(risk, 1.0)

    if risk <= 0.4:
        reasons = []
    elif risk <= 0.5:
        reasons = random.sample(reasons_list, 1)
    elif risk <= 0.7:
        reasons = random.sample(reasons_list, 2)
    else:
        reasons = random.sample(reasons_list, 3)

    return round(risk, 2), reasons

st.title("가상카드 발급 & 결제 시뮬레이션")

# ------------------- 카드 발급 -------------------
st.header("1. 카드 발급")
purpose = st.text_input("거래 목적", "해외 쇼핑")
amount = st.number_input("결제 한도", min_value=1, max_value=5000, value=100, step=10)
duration = st.number_input("유효 기간(일)", min_value=1, max_value=365, value=7)
restrict_sites = st.checkbox("사용처 제한", value=True)

allowed_sites_list = None
if restrict_sites:
    st.info("결제를 허용할 사이트를 입력하세요. 한 줄에 하나씩 입력합니다.")
    st.session_state.custom_allowed_sites_input = st.text_area(
        "허용 사이트 목록",
        st.session_state.custom_allowed_sites_input,
        height=100,
    )
    allowed_sites_list = [s.strip() for s in st.session_state.custom_allowed_sites_input.split('\n') if s.strip()]

ai_cond = ai_recommend()
st.caption(f"AI 추천 조건 예시 → limit: {ai_cond['limit']}, duration_days: {ai_cond['duration_days']}, restricted_sites: {ai_cond['restricted_sites']}")

if st.button("카드 발급"):
    card_id = generate_card_id()
    expiry = datetime.now() + timedelta(days=int(duration))
    st.session_state.cards_db[card_id] = {
        "purpose": purpose,
        "limit": int(amount),
        "expiry": expiry,
        "restricted": bool(restrict_sites),
        "allowed_sites": allowed_sites_list if restrict_sites else None,
        "active": True,
    }
    st.success(f"{card_id} 발급 완료! 유효기간: {expiry.strftime('%Y-%m-%d %H:%M:%S')}")

# ------------------- 결제 요청 -------------------
st.header("2. 결제 요청")
if st.session_state.cards_db:
    selected_card = st.selectbox("결제에 사용할 카드 선택", options=list(st.session_state.cards_db.keys()))
    payment_amount = st.number_input("결제 금액", min_value=1, max_value=5000, value=80, step=10, key="pay_amount")
    site = st.text_input("결제 사이트", "amazon.com", key="pay_site")
    country = st.text_input("사용 국가", "KR", key="pay_country")

    if st.button("결제 시도"):
        card = st.session_state.cards_db[selected_card]

        if card['restricted'] and card.get('allowed_sites') and site not in card['allowed_sites']:
            st.error("AI 위험 탐지, 결제를 보류합니다. 사용처 제한 위반.")
        else:
            risk_score, reasons = calculate_risk(payment_amount, card, site, country)
            st.info(f"AI 위험 점수: {risk_score:.2f} | 분석 사유: {', '.join(reasons) if reasons else '없음'}")

            if risk_score > 0.4:
                st.error("AI 위험 점수 과다, 결제를 거절합니다.")
            else:
                st.success(f"결제 승인 완료 (AI 위험 점수: {risk_score:.2f})")
                card['active'] = False
                st.info("유효 기간이 지나면 자동 폐기됩니다.")
                st.session_state.transactions_db.append({
                    'card': selected_card,
                    'amount': int(payment_amount),
                    'site': site,
                    'country': country,
                    'risk_score': risk_score,
                    'reasons': reasons
                })
else:
    st.write("카드를 먼저 발급해주세요.")

# ------------------- 거래 기록 -------------------
st.header("3. 거래 기록 확인")
if st.session_state.transactions_db:
    st.table(st.session_state.transactions_db)
else:
    st.write("거래 기록이 없습니다.")
