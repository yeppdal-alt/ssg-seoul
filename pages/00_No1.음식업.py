import streamlit as st
import pandas as pd
import plotly.express as px

# ────────────────────────────────────────────────────────────
# 기본 설정
# ────────────────────────────────────────────────────────────
st.set_page_config(page_title="음식업종 전문 분석", page_icon="🍽️", layout="wide")

DATA_PATH = "data_seoul.csv"   # app.py와 같은 폴더에 있는 데이터를 그대로 사용합니다.

TOP4_GU = ["강남구", "서초구", "마포구", "용산구"]


@st.cache_data
def load_data():
    df = pd.read_csv(DATA_PATH)
    for col in ["상권업종대분류명", "상권업종중분류명", "상권업종소분류명", "시군구명", "행정동명", "법정동명"]:
        df[col] = df[col].astype(str)
    return df


df_all = load_data()
food = df_all[df_all["상권업종대분류명"] == "음식"].copy()

st.title("🍽️ 음식업종 전문 분석")
st.caption("서울시 상가(상권)정보 중 '음식' 대분류 업종만 추출하여 심층 분석합니다.")

# ────────────────────────────────────────────────────────────
# 1. 전체 개요 KPI
# ────────────────────────────────────────────────────────────
st.header("📌 음식업종 전체 개요")

total_all = len(df_all)
total_food = len(food)
share = total_food / total_all * 100 if total_all else 0
mid_n = food["상권업종중분류명"].nunique()
top_mid_all = food["상권업종중분류명"].value_counts().idxmax()

k1, k2, k3, k4 = st.columns(4)
k1.metric("서울 전체 음식업소 수", f"{total_food:,}개")
k2.metric("전체 업종 대비 비중", f"{share:.1f}%")
k3.metric("음식 중분류 종류", f"{mid_n}개")
k4.metric("서울 최다 음식 중분류", top_mid_all)

st.divider()

# ────────────────────────────────────────────────────────────
# 2. 구별 음식업 현황 비교 (25개 구 전체)
# ────────────────────────────────────────────────────────────
st.header("🏙️ 구별 음식업 현황 비교")

gu_food = food.groupby("시군구명").size().reset_index(name="음식업소수")
gu_total = df_all.groupby("시군구명").size().reset_index(name="전체업소수")
gu_stat = gu_food.merge(gu_total, on="시군구명")
gu_stat["음식업비중(%)"] = (gu_stat["음식업소수"] / gu_stat["전체업소수"] * 100).round(1)
gu_stat["구분"] = gu_stat["시군구명"].apply(lambda x: "관심 4개 구" if x in TOP4_GU else "기타")

c1, c2 = st.columns(2)
with c1:
    fig1 = px.bar(
        gu_stat.sort_values("음식업소수", ascending=True),
        x="음식업소수", y="시군구명", orientation="h", text="음식업소수",
        color="구분", color_discrete_map={"관심 4개 구": "#e74c3c", "기타": "#3498db"},
        title="구별 음식업소 수",
    )
    fig1.update_traces(textposition="outside")
    fig1.update_layout(yaxis=dict(title=None), height=650)
    st.plotly_chart(fig1, use_container_width=True)

with c2:
    fig2 = px.bar(
        gu_stat.sort_values("음식업비중(%)", ascending=True),
        x="음식업비중(%)", y="시군구명", orientation="h", text="음식업비중(%)",
        color="구분", color_discrete_map={"관심 4개 구": "#e74c3c", "기타": "#3498db"},
        title="구별 음식업 비중 (해당 구 전체 업종 대비 %)",
    )
    fig2.update_traces(textposition="outside")
    fig2.update_layout(yaxis=dict(title=None), height=650)
    st.plotly_chart(fig2, use_container_width=True)

st.divider()

# ────────────────────────────────────────────────────────────
# 3. 구별 음식업종 경쟁강도 분석 (HHI 지수)
# ────────────────────────────────────────────────────────────
st.header("🧮 구별 음식업종 쏠림도 분석 (HHI 지수)")
st.caption(
    "HHI(허핀달-허쉬만 지수)는 구 내 음식 중분류별 점유율 제곱합입니다. "
    "값이 높을수록 특정 업종(예: 한식)에 쏠려 있고, 낮을수록 다양한 업종이 고르게 분포합니다. "
    "(기준: 2,500 이상 = 쏠림/저경쟁, 1,500~2,500 = 보통, 1,500 미만 = 다양/과밀경쟁)"
)

hhi_rows = []
for gu, sub in food.groupby("시군구명"):
    shares = sub["상권업종중분류명"].value_counts(normalize=True)
    hhi = (shares ** 2).sum() * 10000
    hhi_rows.append({
        "시군구명": gu,
        "HHI": round(hhi, 0),
        "음식업소수": len(sub),
        "최다업종(중분류)": shares.idxmax(),
        "최다업종비중(%)": round(shares.max() * 100, 1),
    })
hhi_df = pd.DataFrame(hhi_rows).sort_values("HHI", ascending=False)


def hhi_grade(v):
    if v >= 2500:
        return "쏠림 (저경쟁)"
    elif v >= 1500:
        return "보통"
    return "다양 (과밀경쟁)"


hhi_df["평가"] = hhi_df["HHI"].apply(hhi_grade)

fig_hhi = px.bar(
    hhi_df.sort_values("HHI", ascending=True),
    x="HHI", y="시군구명", orientation="h", color="평가", text="HHI",
    color_discrete_map={"쏠림 (저경쟁)": "#e74c3c", "보통": "#f39c12", "다양 (과밀경쟁)": "#2ecc71"},
    title="구별 음식업종 HHI 지수",
)
fig_hhi.update_traces(textposition="outside")
fig_hhi.update_layout(yaxis=dict(title=None), height=700)
st.plotly_chart(fig_hhi, use_container_width=True)

with st.expander("구별 HHI 상세 테이블 보기"):
    st.dataframe(hhi_df.reset_index(drop=True))

st.divider()

# ────────────────────────────────────────────────────────────
# 4. 지역별 음식업종 심층 분석 (선택 + 직접 입력)
# ────────────────────────────────────────────────────────────
st.header("🔍 지역별 음식업종 심층 분석")

gu_list = sorted(food["시군구명"].dropna().unique().tolist())
select_options = ["전체 (서울)"] + gu_list + ["✏️ 직접 입력"]

c1, c2 = st.columns([1, 1])
with c1:
    selected = st.selectbox("지역 선택 (구 단위)", select_options, index=0, key="food_region_select")
with c2:
    manual_input = ""
    if selected == "✏️ 직접 입력":
        manual_input = st.text_input(
            "지역명을 직접 입력하세요 (구/동/법정동 이름 일부만 입력해도 검색됩니다)",
            placeholder="예: 성동구, 역삼동, 망원동 ...",
            key="food_region_manual",
        )

if selected == "✏️ 직접 입력" and manual_input.strip():
    keyword = manual_input.strip()
    mask = (
        food["시군구명"].str.contains(keyword, na=False)
        | food["행정동명"].str.contains(keyword, na=False)
        | food["법정동명"].str.contains(keyword, na=False)
    )
    fsub = food[mask]
    region_label = keyword
elif selected == "✏️ 직접 입력":
    fsub = food.iloc[0:0]
    region_label = "(지역명을 입력해주세요)"
elif selected == "전체 (서울)":
    fsub = food
    region_label = "서울 전체"
else:
    fsub = food[food["시군구명"] == selected]
    region_label = selected

# 행정동 세부 필터 (선택 사항)
if not fsub.empty and selected not in ("전체 (서울)",):
    dong_list = sorted(fsub["행정동명"].dropna().unique().tolist())
    dong_select = st.multiselect("행정동으로 더 좁혀보기 (선택 사항)", dong_list, key="food_dong_filter")
    if dong_select:
        fsub = fsub[fsub["행정동명"].isin(dong_select)]

st.subheader(f"'{region_label}' 음식업종 현황 ({len(fsub):,}개 업소)")

if fsub.empty:
    st.warning("해당 조건에 맞는 데이터가 없습니다. 지역명을 다시 확인해주세요.")
else:
    # 중분류 분포: 막대 + 파이
    b1, b2 = st.columns(2)
    with b1:
        mid_counts = fsub["상권업종중분류명"].value_counts().reset_index()
        mid_counts.columns = ["중분류", "개수"]
        fig3 = px.bar(
            mid_counts, x="개수", y="중분류", orientation="h", text="개수",
            title="음식 중분류별 현황", color="개수", color_continuous_scale="Oranges",
        )
        fig3.update_traces(textposition="outside")
        fig3.update_layout(yaxis=dict(autorange="reversed", title=None), height=480, coloraxis_showscale=False)
        st.plotly_chart(fig3, use_container_width=True)

    with b2:
        fig4 = px.pie(
            mid_counts, names="중분류", values="개수", hole=0.45,
            title="음식 중분류 비중",
        )
        fig4.update_traces(textposition="inside", textinfo="percent+label")
        fig4.update_layout(height=480)
        st.plotly_chart(fig4, use_container_width=True)

    # 소분류 TOP 20
    st.markdown("#### 세부 업종(소분류) TOP 20")
    small_counts = fsub["상권업종소분류명"].value_counts().head(20).reset_index()
    small_counts.columns = ["소분류", "개수"]
    fig5 = px.bar(
        small_counts, x="소분류", y="개수", text="개수", color="개수",
        color_continuous_scale="Reds", title="음식 소분류 TOP 20",
    )
    fig5.update_traces(textposition="outside")
    fig5.update_layout(xaxis_tickangle=-45, xaxis_title=None, height=480, coloraxis_showscale=False)
    st.plotly_chart(fig5, use_container_width=True)

    # 트리맵: 중분류 -> 소분류
    st.markdown("#### 업종 계층 구조 (중분류 → 소분류)")
    tree = fsub.groupby(["상권업종중분류명", "상권업종소분류명"]).size().reset_index(name="개수")
    fig6 = px.treemap(
        tree, path=["상권업종중분류명", "상권업종소분류명"], values="개수",
        title="음식업종 트리맵 (박스가 클수록 업소 수가 많음)",
        color="개수", color_continuous_scale="Oranges",
    )
    fig6.update_layout(height=550, margin=dict(t=50, l=10, r=10, b=10))
    st.plotly_chart(fig6, use_container_width=True)

    # 동별 밀집 TOP 15
    st.markdown("#### 음식업 밀집 행정동 TOP 15")
    dong_counts = fsub["행정동명"].value_counts().head(15).reset_index()
    dong_counts.columns = ["행정동", "개수"]
    fig7 = px.bar(
        dong_counts.sort_values("개수", ascending=True),
        x="개수", y="행정동", orientation="h", text="개수", color="개수",
        color_continuous_scale="Purples", title="음식업 밀집 행정동 TOP 15",
    )
    fig7.update_traces(textposition="outside")
    fig7.update_layout(yaxis=dict(title=None), height=500, coloraxis_showscale=False)
    st.plotly_chart(fig7, use_container_width=True)

    # 밀도 지도
    if {"경도", "위도"}.issubset(fsub.columns):
        st.markdown("#### 음식점 분포 밀도 지도")
        map_df = fsub.dropna(subset=["경도", "위도"])
        if len(map_df) > 6000:
            map_df = map_df.sample(6000, random_state=42)
            st.caption("지도에는 표시 성능을 위해 최대 6,000개 업소를 무작위로 표시합니다.")
        fig8 = px.density_mapbox(
            map_df, lat="위도", lon="경도", radius=8, zoom=11, height=550,
            title="음식점 밀도 히트맵",
        )
        fig8.update_layout(mapbox_style="open-street-map", margin=dict(l=0, r=0, t=40, b=0))
        st.plotly_chart(fig8, use_container_width=True)

    with st.expander("원본 데이터 보기 (최대 500행)"):
        st.dataframe(fsub.head(500))
