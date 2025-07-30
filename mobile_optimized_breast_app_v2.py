
import streamlit as st
import pandas as pd

st.set_page_config(page_title="유방암 약제 추천", layout="centered")
st.markdown("<h2 style='text-align: center;'>📱 유방암 병기 기반 약제 추천 AI</h2>", unsafe_allow_html=True)
st.markdown("---")

df = pd.read_csv("nccn_breast_stage_drug_map_final_500plus.csv", encoding='cp949')
treatment_order = ["Neoadjuvant", "Adjuvant", "1st line", "2nd+ line", "Recurrent"]
df["TreatmentLine"] = pd.Categorical(df["TreatmentLine"], categories=treatment_order, ordered=True)

st.markdown("### 1️⃣ 병기 및 병리 정보 입력")

t_mapping = {"TX": "T1", "T0": "T1", "Tis (DCIS)": "T1", "Tis (Paget)": "T1",
             "T1mi": "T1", "T1a": "T1", "T1b": "T1", "T1c": "T1",
             "T2": "T2", "T3": "T3", "T4a": "T4", "T4b": "T4", "T4c": "T4", "T4d": "T4"}
n_mapping = {"cNX": "N0", "cN0": "N0", "cN1mi": "N1", "cN2a": "N2", "cN2b": "N2",
             "cN3a": "N3", "cN3b": "N3", "cN3c": "N3"}

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

st.markdown(f"#### 병기: {stage} | 아형: {subtype}")
st.markdown("---")

filtered_df = df[(df['Stage'] == stage) &
                 (df['Subtype'] == subtype) &
                 (df['OncotypeDx'] == oncotype) &
                 (df['gBRCA'] == gbrca) &
                 (df['PDL1'] == pdl1)].sort_values("TreatmentLine")

st.markdown("### 2️⃣ 치료전략 및 약제 추천 결과"\n(Based on 2025 NCCN Guideline))

if filtered_df.empty:
    st.warning("조건에 맞는 추천 약제가 없습니다. 다른 조건을 선택해보세요.")
else:
    for _, row in filtered_df.iterrows():
        with st.expander(f"💊 약제명: {row['RecommendedRegimen']} | 🩺 단계: {row['TreatmentLine']}", expanded=True):
            st.markdown(f"**💊 약제명:** {row['RecommendedRegimen']}")
            st.markdown(f"**🩺 치료 단계:** {row['TreatmentLine']}")
            st.markdown(f"**📌 NCCN 권고 등급:** {row['NCCN_Category']}")
            st.markdown(f"**🧪 임상시험:** {row['Trial']}")
            if 'Notes' in row and pd.notna(row['Notes']):
                st.markdown(f"**📝 비고:** {row['Notes']}")


            coverage = str(row.get("급여여부", "")).strip()
            if coverage in ["급여", "선별급여(복합요법)", "True", "true", "TRUE"]:
                st.success(f"✅ {coverage}")
            elif coverage == "비급여":
                st.error("❌ 비급여")
            else:
                st.info("ℹ️ 급여 정보 없음")

            try:
                dosage_val = float(row.get("Dosage_Value", 0))
                dosage_type = row.get("Dosage_Type", "")
                unit_price = float(row.get("Unit_Price", 0))
                avg_bsa = 1.6
                avg_weight = 60.0
                total_dose = 0
                dose_text = "용량 정보 없음"
                if dosage_type == "mg/kg":
                    total_dose = dosage_val * avg_weight
                    dose_text = f"{dosage_val} mg/kg → {total_dose:.1f} mg"
                elif dosage_type == "mg/m²":
                    total_dose = dosage_val * avg_bsa
                    dose_text = f"{dosage_val} mg/m² → {total_dose:.1f} mg"
                elif dosage_type == "mg":
                    total_dose = dosage_val
                    dose_text = f"{total_dose:.1f} mg"

                st.markdown(f"**💉 권장 용량:** {dose_text}")
                if total_dose > 0 and unit_price > 0:
                    total_cost = int(total_dose * unit_price)
                    st.markdown(f"**💊 단가:** {unit_price:,.0f}원/1mg")
                    st.markdown(f"**💰 예상 비용:** 약 {total_cost:,}원")
            except:
                st.markdown("💉 용량 정보 없음")
