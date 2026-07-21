import streamlit as st
import pandas as pd
import plotly.express as px

# ────────────────────────────────────────────────────────────
# 기본 설정
# ────────────────────────────────────────────────────────────
st.set_page_config(page_title="서울 상권 분석 대시보드", page_icon="🏪", layout="wide")

DATA_PATH = "data_seoul.csv"   # app.py와 같은 폴더에 이 파일을 함께 올려주세요.

TOP4_GU = ["강남구", "서초구", "마포구", "용산구"]


@st.cache_data
def load_data():
    df = pd.read_csv(DATA_PATH)
    for col in ["상권업종대분류명", "상권업종중분류명", "상권업종소분류명", "시군구명", "행정동명", "법정동명"]:
        df[col] = df[col].astype(str)
    return df


df = load_data()

st.title("🏪 서울시 상가(상권) 정보 분석 대시보드")
st.caption("데이터 출처: 소상공인시장진흥공단 상가(상권)정보 - 서울 (2026년 3월 기준)")

# ────────────────────────────────────────────────────────────
# 0. 구별 "여기서 창업하면 위험한" 대표 업종 (소분류 기준, 유머)
# ────────────────────────────────────────────────────────────
st.header("☠️ 구별 레드오션 주의보 — 여기서 창업하면 망할 수도 있어요")
st.caption(
    "※ 진지한 폐업률 예측이 아니라, 해당 구에서 '이미 제일 많이 몰려있는' 소분류 업종을 뽑아본 유머용 코너입니다. "
    "경쟁이 세다는 뜻이지, 정말 망한다는 보장(?)은 아니니 참고만 해주세요 😅"
)

# 업종별 드립 코멘트 (없는 업종은 기본 코멘트로 대체)
ROAST_COMMENTS = {
    "백반/한정식": "골목마다 이미 이모님이 계십니다. '엄마 손맛'으로 뚫으려면 진짜 엄마급 실력이 필요해요.",
    "경영 컨설팅업": "옆집도, 그 옆집도 전부 컨설팅펌... 다들 서로를 컨설팅해주는 걸까요?",
    "변호사": "반경 100m 안에 변호사가 당신보다 많을 확률이 높습니다. 소장(訴狀)보다 명함이 더 많이 돌아다녀요.",
    "부동산 중개/대리업": "매물보다 중개사가 더 많은 동네일지도 모릅니다. '급매'보다 '급창업'이 더 많아요.",
    "입시·교과학원": "앞 학원, 옆 학원, 건너편 학원까지... 학생 쟁탈전에 오신 걸 환영합니다.",
    "미용실": "커트 3천원 전쟁까지 각오해야 할지도? 손님보다 미용실 간판이 더 자주 보여요.",
    "카페": "스타벅스, 투썸, 개인 카페가 골목 하나에 다 모여있는 곳일 가능성이 높습니다.",
    "치킨": "국룰 창업 아이템의 최종 보스. 반경 500m 안에 이미 형제 치킨집이 있을지도 몰라요.",
}
DEFAULT_COMMENT = "이미 너무 많아서 사장님만 모르는 레드오션일 수도 있어요. 창업 전에 꼭 한 바퀴 둘러보세요."

risky_rows = []
for gu, sub in df.groupby("시군구명"):
    vc = sub["상권업종소분류명"].value_counts()
    top_cat, top_n = vc.idxmax(), vc.max()
    pct = top_n / len(sub) * 100
    risky_rows.append({
        "구": gu,
        "위험 업종(소분류)": top_cat,
        "매장 수": top_n,
        "구 전체 대비 비중(%)": round(pct, 1),
        "한마디": ROAST_COMMENTS.get(top_cat, DEFAULT_COMMENT),
    })
risky_df = pd.DataFrame(risky_rows).sort_values("매장 수", ascending=False)

worst = risky_df.iloc[0]
st.warning(
    f"🥇 오늘의 최고 위험 지역은 **{worst['구']}**의 **'{worst['위험 업종(소분류)']}'**! "
    f"무려 **{worst['매장 수']:,}개**나 있어요 (구 전체 업소의 {worst['구 전체 대비 비중(%)']}%). {worst['한마디']}"
)

fig_risk = px.bar(
    risky_df.sort_values("매장 수", ascending=True),
    x="매장 수", y="구", orientation="h", text="위험 업종(소분류)",
    color="매장 수", color_continuous_scale="Reds",
    title="구별 대표 레드오션 업종 (막대 위 텍스트 = 업종명)",
)
fig_risk.update_traces(textposition="outside")
fig_risk.update_layout(yaxis=dict(title=None), height=720, coloraxis_showscale=False)
st.plotly_chart(fig_risk, use_container_width=True)

st.markdown("#### 구별 레드오션 업종 상세 코멘트")
st.dataframe(risky_df.reset_index(drop=True), use_container_width=True)

st.divider()

# ────────────────────────────────────────────────────────────
# 1. 상단 고정 대시보드 - 강남구·서초구·마포구·용산구 업종(중분류) TOP10
# ────────────────────────────────────────────────────────────
st.header("📊 관심 4개 구 업종 TOP 10 (중분류)")

cols = st.columns(4)
for col, gu in zip(cols, TOP4_GU):
    sub = df[df["시군구명"] == gu]
    top10 = sub["상권업종중분류명"].value_counts().head(10).reset_index()
    top10.columns = ["업종", "개수"]

    fig = px.bar(
        top10, x="개수", y="업종", orientation="h", text="개수",
        title=f"{gu} ({len(sub):,}개 업소)",
        color="개수", color_continuous_scale="Blues",
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        yaxis=dict(autorange="reversed", title=None),
        xaxis=dict(title=None),
        height=430, margin=dict(l=10, r=10, t=40, b=10),
        coloraxis_showscale=False,
        title_font_size=14,
    )
    col.plotly_chart(fig, use_container_width=True)

st.divider()

# ────────────────────────────────────────────────────────────
# 2. 지역 선택 (드롭다운 선택 + 직접 입력 모두 지원)
# ────────────────────────────────────────────────────────────
st.header("🔍 지역별 상권 업종 현황")

gu_list = sorted(df["시군구명"].dropna().unique().tolist())
select_options = ["전체 (서울)"] + gu_list + ["✏️ 직접 입력"]

c1, c2 = st.columns([1, 1])
with c1:
    selected = st.selectbox("지역 선택 (구 단위)", select_options, index=0)
with c2:
    manual_input = ""
    if selected == "✏️ 직접 입력":
        manual_input = st.text_input(
            "지역명을 직접 입력하세요 (구/동/법정동 이름 일부만 입력해도 검색됩니다)",
            placeholder="예: 성동구, 역삼동, 망원동 ...",
        )

# 필터링
if selected == "✏️ 직접 입력" and manual_input.strip():
    keyword = manual_input.strip()
    mask = (
        df["시군구명"].str.contains(keyword, na=False)
        | df["행정동명"].str.contains(keyword, na=False)
        | df["법정동명"].str.contains(keyword, na=False)
    )
    filtered = df[mask]
    region_label = keyword
elif selected == "✏️ 직접 입력":
    filtered = df.iloc[0:0]
    region_label = "(지역명을 입력해주세요)"
elif selected == "전체 (서울)":
    filtered = df
    region_label = "서울 전체"
else:
    filtered = df[df["시군구명"] == selected]
    region_label = selected

# 행정동 세부 필터 (선택 사항)
if not filtered.empty and selected not in ("전체 (서울)",):
    dong_list = sorted(filtered["행정동명"].dropna().unique().tolist())
    dong_select = st.multiselect("행정동으로 더 좁혀보기 (선택 사항)", dong_list)
    if dong_select:
        filtered = filtered[filtered["행정동명"].isin(dong_select)]

st.subheader(f"'{region_label}' 상권 현황")

if filtered.empty:
    st.warning("해당 조건에 맞는 데이터가 없습니다. 지역명을 다시 확인해주세요.")
else:
    # KPI 카드
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("전체 업소 수", f"{len(filtered):,}개")
    k2.metric("업종 대분류 수", f"{filtered['상권업종대분류명'].nunique()}개")
    top_cat = filtered["상권업종대분류명"].value_counts().idxmax()
    k3.metric("최다 업종(대분류)", top_cat)
    top_mid = filtered["상권업종중분류명"].value_counts().idxmax()
    k4.metric("최다 업종(중분류)", top_mid)

    st.write("")

    # 대분류 현황: 막대 + 파이
    b1, b2 = st.columns(2)
    with b1:
        cat_counts = filtered["상권업종대분류명"].value_counts().reset_index()
        cat_counts.columns = ["업종대분류", "개수"]
        fig1 = px.bar(
            cat_counts, x="개수", y="업종대분류", orientation="h", text="개수",
            title="업종 대분류별 현황", color="개수", color_continuous_scale="Blues",
        )
        fig1.update_traces(textposition="outside")
        fig1.update_layout(yaxis=dict(autorange="reversed", title=None), height=450, coloraxis_showscale=False)
        st.plotly_chart(fig1, use_container_width=True)

    with b2:
        fig2 = px.pie(
            cat_counts, names="업종대분류", values="개수", hole=0.45,
            title="업종 대분류 비중",
        )
        fig2.update_traces(textposition="inside", textinfo="percent+label")
        fig2.update_layout(height=450)
        st.plotly_chart(fig2, use_container_width=True)

    # 중분류 TOP 15
    st.markdown("#### 세부 업종(중분류) TOP 15")
    mid_counts = filtered["상권업종중분류명"].value_counts().head(15).reset_index()
    mid_counts.columns = ["업종중분류", "개수"]
    fig3 = px.bar(
        mid_counts, x="업종중분류", y="개수", text="개수", color="개수",
        color_continuous_scale="Tealgrn", title="업종 중분류 TOP 15",
    )
    fig3.update_traces(textposition="outside")
    fig3.update_layout(xaxis_tickangle=-45, xaxis_title=None, height=450, coloraxis_showscale=False)
    st.plotly_chart(fig3, use_container_width=True)

    # 대분류 -> 중분류 트리맵
    st.markdown("#### 업종 계층 구조 (대분류 → 중분류)")
    tree = filtered.groupby(["상권업종대분류명", "상권업종중분류명"]).size().reset_index(name="개수")
    fig4 = px.treemap(
        tree, path=["상권업종대분류명", "상권업종중분류명"], values="개수",
        title="업종 트리맵 (박스가 클수록 업소 수가 많음)",
        color="개수", color_continuous_scale="Blues",
    )
    fig4.update_layout(height=550, margin=dict(t=50, l=10, r=10, b=10))
    st.plotly_chart(fig4, use_container_width=True)

    # 지도
    if {"경도", "위도"}.issubset(filtered.columns):
        st.markdown("#### 업소 위치 지도")
        map_df = filtered.dropna(subset=["경도", "위도"])
        if len(map_df) > 8000:
            map_df = map_df.sample(8000, random_state=42)
            st.caption("지도에는 표시 성능을 위해 최대 8,000개 업소를 무작위로 표시합니다.")
        fig5 = px.scatter_mapbox(
            map_df, lat="위도", lon="경도", color="상권업종대분류명",
            hover_name="상호명", hover_data=["상권업종소분류명"],
            zoom=11, height=550,
        )
        fig5.update_layout(mapbox_style="open-street-map", margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig5, use_container_width=True)

    with st.expander("원본 데이터 보기 (최대 500행)"):
        st.dataframe(filtered.head(500))
