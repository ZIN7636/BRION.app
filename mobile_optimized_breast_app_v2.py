import streamlit as st
import pandas as pd

# 페이지 설정 (모바일 친화적 중앙 정렬)
st.set_page_config(page_title="유방암 병기 기반 약제 추천", layout="centered")
st.markdown("<h2 style='text-align: center;'>📱 유방암 병기 기반 약제 추천 AI</h2>", unsafe_allow_html=True)
st.markdown("---")

# 최종 데이터 파일 로드 (pcbrion.py와 동일)
try:
    df = pd.read_csv("final_brion_data.csv", encoding='cp949')
except FileNotFoundError:
    st.error("final_brion_data.csv 파일을 찾을 수 없습니다. 앱 파일과 동일한 위치에 파일을 추가해주세요.")
    st.stop()

# 치료 단계 순서 정의 및 정렬
treatment_order = ["Neoadjuvant", "Adjuvant", "1st line", "2nd+ line", "Recurrent"]
df["TreatmentLine"] = pd.Categorical(df["TreatmentLine"], categories=treatment_order, ordered=True)

st.markdown("### 1️⃣ 병기 및 병리 정보 입력")

# T/N 사용자 정의 값 반영 (pcbrion.py와 동일)
t_mapping = {
    "TX": "T1", "T0": "T1", "Tis (DCIS)": "T1", "Tis (Paget)": "T1",
    "T1mi": "T1", "T1a": "T1", "T1b": "T1", "T1c": "T1",
    "T2": "T2", "T3": "T3",
    "T4a": "T4", "T4b": "T4", "T4c": "T4", "T4d": "T4"
}
n_mapping = {
    "cNX": "N0", "cN0": "N0", "cN1mi": "N1",
    "cN2a": "N2", "cN2b": "N2",
    "cN3a": "N3", "cN3b": "N3", "cN3c": "N3"
}

# 사용자 입력 위젯 (모바일 레이아웃에 맞게 배치)
t_raw = st.selectbox("Primary Tumor (T)", list(t_mapping.keys()))
n_raw = st.selectbox("Regional Lymph Nodes (N)", list(n_mapping.keys()))
m = st.selectbox("Distant Metastasis (M)", ["M0", "cM0(i+)", "M1"])
her2 = st.radio("HER2 Status", ["Neg (-)", "Pos (+)"], horizontal=True)
er = st.radio("ER Status", ["Neg (-)", "Pos (+)"], horizontal=True)
pr = st.radio("PR Status", ["Neg (-)", "Pos (+)"], horizontal=True)
oncotype = st.selectbox("OncotypeDx 조건", sorted(df['OncotypeDx'].dropna().unique()))
gbrca = st.selectbox("gBRCA 여부", sorted(df['gBRCA'].dropna().unique()))
pdl1 = st.selectbox("PD-L1 상태", sorted(df['PDL1'].dropna().unique()))

t = t_mapping[t_raw]
n = n_mapping[n_raw]

# 병기 계산 (pcbrion.py와 동일)
stage = "병기 계산 불가"
if "M1" in m:
    stage = "Stage IV"
elif t == "T1" and n == "N0" and "M0" in m:
    stage = "Stage I"
elif t == "T2" and n == "N0" and "M0" in m:
    stage = "Stage II"
elif t == "T3" or n == "N2" or n == "N3":
    stage = "Stage III"
elif t == "T0" and n == "N0" and "M0" in m:
    stage = "Stage 0"

# 아형 분류 (pcbrion.py와 동일)
subtype = "-"
if er == "Pos (+)" or pr == "Pos (+)":
    if her2 == "Neg (-)":
        subtype = "HR+/HER2-"
    elif her2 == "Pos (+)":
        subtype = "HR+/HER2+"
elif er == "Neg (-)" and pr == "Neg (-)" and her2 == "Pos (+)":
    subtype = "HR-/HER2+"
elif er == "Neg (-)" and pr == "Neg (-)" and her2 == "Neg (-)":
    subtype = "TNBC"

st.markdown(f"#### **계산된 병기:** {stage} | **계산된 아형:** {subtype}")
st.markdown("---")

# 필터링 (pcbrion.py와 동일)
filtered_df = df[
    (df['Stage'] == stage) &
    (df['Subtype'] == subtype) &
    (df['OncotypeDx'] == oncotype) &
    (df['gBRCA'] == gbrca) &
    (df['PDL1'] == pdl1)
].sort_values("TreatmentLine")

st.markdown("### 2️⃣ 치료전략 및 약제 추천 결과")

if filtered_df.empty:
    st.warning("선택된 조건에 맞는 추천 약제가 없습니다. 다른 조건을 선택해보세요.")
else:
    for _, row in filtered_df.iterrows():
        # 결과 출력 Expander
        expander_title = f"🩺 치료 단계: {row['TreatmentLine']} | 💊 약제명: {row['RecommendedRegimen']}"
        with st.expander(expander_title, expanded=True):
            st.markdown("---")
            
            # pcbrion.py와 동일한 '-' 처리 로직
            dose_per_session_raw = row['1회_용량(160cm/60kg)_mg']
            if isinstance(dose_per_session_raw, str):
                items = [item.strip() for item in dose_per_session_raw.split(',')]
                processed_items = ['정보 없음' if item == '-' else item for item in items]
                dose_per_session = ', '.join(processed_items)
            else:
                dose_per_session = dose_per_session_raw

            # 결과 출력 (모바일에 최적화된 st.markdown 사용)
            st.markdown(f"**🩺 치료 단계:** {row['TreatmentLine']}")
            st.markdown(f"**💊 약제명:** {row['RecommendedRegimen']}")
            st.markdown(f"**📌 NCCN 권고 등급:** {row['NCCN_Category']}")
            st.markdown(f"**🧪 임상시험:** {row['Trial']}")
            
            # 급여여부 (모바일에 최적화된 st.success/error/info 사용)
            coverage_text = str(row.get("급여여부", "")).strip()
            if coverage_text in ["급여", "선별급여(복합요법)"]:
                st.success(f"✅ 급여여부: {coverage_text}")
            elif coverage_text == "비급여":
                st.error("❌ 급여여부: 비급여")
            else:
                st.info(f"ℹ️ 급여 여부: {coverage_text or '정보 없음'}")

            # 최종 데이터 파일의 컬럼을 직접 출력
            st.markdown(f"**💉 권장 용량:** {row['권장용량_표시']}")
            st.markdown(f"**💊 1회 용량(160cm/60kg)mg:** {dose_per_session}")
            st.markdown(f"**💰 최종 비용:** {row['단가_표시']}")
