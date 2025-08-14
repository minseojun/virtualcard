import streamlit as st
import random
from datetime import datetime, timedelta

# ------------------------------
# 세션 상태 초기화
if 'cards_db' not in st.session_state:
    st.session_state.cards_db = {}
if 'transactions_db' not in st.session_state:
    st.session_state.transactions_db = []
if 'custom_allowed_sites_input' not in st.session_state:
    st.session_state.custom_allowed_sites_input = "amazon.com\nkbstar.com\ntemu.com"
# 결제 보류(인증 필요) 상태를 보관
if 'pending_payment' not in st.session_state:
    st.session_state.pending_payment = None  # dict: {card_id, amount, site, country, reason}

# ------------------------------
# AI 추천 조건(샘플)
def ai_recommend():
    return {
        "limit": random.choice([50, 100, 150, 200, 500]),
        "duration_days": random.choice([1, 3, 7, 14, 30]),
        "restricted_sites": random.choice([True, False])
    }

st.title("가상카드 발급 & 결제 시뮬레이션")

# ------------------------------
# 1) 카드 발급
st.header("1. 카드 발급")
purpose = st.text_input("거래 목적", "해외 쇼핑")
amount = st.number_input("결제 한도", min_value=1, max_value=5000, value=100, step=10)
duration = st.number_input("유효 기간(일)", min_value=1, max_value=365, value=7)
restrict_sites = st.checkbox("사용처 제한", value=True)

# 사용처 제한 시 허용 사이트 입력 UI
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
    card_id = f"CARD{len(st.session_state.cards_db)+1:03d}"
    expiry = datetime.now() + timedelta(days=int(duration))
    st.session_state.cards_db[card_id] = {
        "purpose": purpose,
        "limit": int(amount),
        "expiry": expiry,
        "restricted": bool(restrict_sites),
        # 카드 발급 시점의 허용 사이트 목록을 카드에 저장(카드별 정책 유지)
        "allowed_sites": allowed_sites_list if restrict_sites else None,
        "active": True,
    }
    st.success(f"{card_id} 발급 완료! 유효기간: {expiry.strftime('%Y-%m-%d %H:%M:%S')}")

# ------------------------------
# 2) 결제 요청
st.header("2. 결제 요청")
if st.session_state.cards_db:
    selected_card = st.selectbox("결제에 사용할 카드 선택", options=list(st.session_state.cards_db.keys()))
    payment_amount = st.number_input("결제 금액", min_value=1, max_value=5000, value=80, step=10, key="pay_amount")
    site = st.text_input("결제 사이트", "amazon.com", key="pay_site")
    country = st.text_input("사용 국가", "KR", key="pay_country")

    # 결제 시도 버튼
    if st.button("결제 시도"):
        card = st.session_state.cards_db[selected_card]
        # 기본 검증
        if payment_amount > card['limit']:
            st.error("결제 금액이 카드 한도를 초과했습니다.")
        elif card['expiry'] < datetime.now():
            st.error("카드 유효기간이 만료되었습니다.")
        # 사용처 제한 위반 시: 보류 + 인증 플로우로 이관
        elif card['restricted'] and card.get('allowed_sites') and site not in card['allowed_sites']:
            st.warning("AI 위험 탐지, 결제를 보류합니다")
            # 인증 필요 상태를 세션에 저장 (다음 렌더에서 라디오/버튼 노출)
            st.session_state.pending_payment = {
                'card_id': selected_card,
                'amount': int(payment_amount),
                'site': site,
                'country': country,
                'reason': 'site_not_allowed',
            }
        else:
            # 일반 위험도(샘플)
            risk_score = random.random()
            if risk_score > 0.8 or country in ['NG', 'RU']:
                st.warning("AI 위험 탐지, 결제를 보류합니다")
            else:
                st.success("결제 승인 완료")
                card['active'] = False
                st.info("카드 자동 폐기 처리됨")
            st.session_state.transactions_db.append({
                'card': selected_card,
                'amount': int(payment_amount),
                'site': site,
                'country': country,
                'risk_score': risk_score if 'risk_score' in locals() else 'N/A',
            })

    # 보류된 결제 처리(사용자 선택 유지 위해 버튼 블록 밖에서 렌더)
    if st.session_state.pending_payment:
        pp = st.session_state.pending_payment
        card = st.session_state.cards_db[pp['card_id']]
        st.subheader("추가 확인 필요")
        st.info(
            f"허용된 사이트 목록에 없는 결제 시도입니다.\n\n"
            f"카드: {pp['card_id']} | 금액: {pp['amount']} | 사이트: {pp['site']} | 국가: {pp['country']}"
        )
        choice = st.radio("무시하고 다시 결제를 진행하시겠습니까?", ("아니오", "예"), key="override_choice")
        if choice == "예":
            if st.button("본인인증 진행", key="do_auth"):
                # 인증 성공으로 간주하고 승인 처리
                st.success("결제 승인 완료")
                card['active'] = False
                st.info("카드 자동 폐기 처리됨")
                st.session_state.transactions_db.append({
                    'card': pp['card_id'],
                    'amount': pp['amount'],
                    'site': pp['site'],
                    'country': pp['country'],
                    'risk_score': 'Bypassed',
                })
                # 보류 상태 해제
                st.session_state.pending_payment = None
        else:
            st.info("결제가 취소되었습니다.")
            if st.button("보류된 결제 닫기", key="close_pending"):
                st.session_state.pending_payment = None
else:
    st.info("먼저 카드를 발급해주세요.")

# ------------------------------
# 3) 거래 기록 확인
st.header("3. 거래 기록 확인")
if st.session_state.transactions_db:
    st.table(st.session_state.transactions_db)
else:
    st.write("거래 기록이 없습니다.")
