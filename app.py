from __future__ import annotations

import io
import json
import math
from dataclasses import dataclass
from typing import Optional

import joblib
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline


LEAKY_COLS_DEFAULT = {
    # 미래 누적 강수량/라벨 원천 계열은 피처에서 제외(누수 방지)
    "target_rain_1h_mm",
    "target_rain_3h_mm",
    "target_heavy_rain_flag",
}

# 프로토타입 참고용: 2022년 8월 강남권 집중호우 사례를 동일 10점 척도로 환산한 가정 구간(교육·의사소통용, 공식 통계 아님)
REFERENCE_SCORE10_GANGNAM_2022 = (8.2, 9.4)

# 지도 초점: 상위 5구 확대 vs 서울시 전체(행정구역 bounds)
MAP_FOCUS_SEOUL_ALL = "서울시 전체"

OPTIONAL_CONTEXT_COLS: dict[str, str] = {
    "elev_m": "평균 고도(m)",
    "elevation_m": "평균 고도(m)",
    "avg_elevation_m": "평균 고도(m)",
    "river_stage_m": "하천 수위(m)",
    "river_max_stage_m": "하천 최대 수위(m)",
    "sewer_level_m": "하수관로 수위(m)",
    "drainage_capacity_index": "배수 용량 지수",
    "flood_trace_score": "침수흔적도(집계)",
}


@dataclass
class TrainedModel:
    pipeline: Pipeline
    feature_cols: list[str]
    threshold: float
    meta: dict


def _inject_css() -> None:
    st.markdown(
        """
<style>
  .block-container { padding-top: 1.0rem; padding-bottom: 2.0rem; background: #ffffff !important; }
  .stApp { background-color: #ffffff !important; }
  [data-testid="stAppViewContainer"] { background-color: #ffffff !important; }
  header { visibility: hidden; }
  footer { visibility: hidden; }
  [data-testid="stSidebar"] { background: #f4f6f9 !important; border-right: 1px solid #e2e6ed; }

  .hud-hero {
    background: #0f2744;
    border-radius: 0 0 14px 14px;
    padding: 1rem 1.1rem 1.05rem;
    margin: -0.35rem -1rem 1rem -1rem;
    box-shadow: 0 6px 24px rgba(15, 39, 68, 0.25);
  }
  @media (min-width: 768px) {
    .hud-hero { margin-left: -2rem; margin-right: -2rem; padding-left: 2rem; padding-right: 2rem; }
  }
  .hud-title {
    text-align:center;
    font-weight: 800;
    font-size: 1.65rem;
    letter-spacing: 0.02em;
    margin-top: 0.2rem;
    margin-bottom: 0.25rem;
    color: #1a1d26;
  }
  .hud-hero .hud-title {
    color: #f4f7fb;
    margin-top: 0;
  }
  .hud-sub {
    text-align:center;
    opacity: 0.95;
    margin-top: 0;
    margin-bottom: 1rem;
    color: #3d4454;
  }
  .hud-hero .hud-sub {
    color: rgba(244, 247, 251, 0.94);
    margin-bottom: 0;
  }
  .hud-pill {
    display:inline-block;
    padding: 0.2rem 0.55rem;
    border-radius: 999px;
    font-weight: 700;
    border: 1px solid #d8dee6;
    background: #f8fafc;
    color: #1a1d26;
  }
  .hud-hero .hud-pill {
    background: rgba(255, 255, 255, 0.14);
    border-color: rgba(255, 255, 255, 0.28);
    color: #f4f7fb;
  }
  .card {
    border: 1px solid #e2e6ed;
    background: #ffffff;
    border-radius: 14px;
    padding: 0.9rem 1.0rem;
    box-shadow: 0 4px 18px rgba(0,0,0,0.06);
  }
  .card h3, .card h4 { margin: 0 0 0.35rem 0; color: #1a1d26; }
  .muted { opacity: 0.88; font-size: 0.92rem; color: #4a5568; }
  .kpi {
    display:flex; gap: 0.8rem; flex-wrap: wrap; margin-top: 0.35rem;
  }
  .kpi .item {
    border: 1px solid #e2e6ed;
    background: #f8fafc;
    border-radius: 12px;
    padding: 0.55rem 0.65rem;
    min-width: 120px;
  }
  .kpi .label { opacity:0.85; font-size:0.82rem; color: #5c6578; }
  .kpi .value { font-weight:800; font-size:1.05rem; margin-top:0.1rem; color: #1a1d26; }
  .kpi-stack { margin-top: 0.35rem; }
  .kpi-stack .kpi-label {
    font-size: 0.82rem;
    color: #5c6578;
    margin-top: 0.65rem;
    margin-bottom: 0.15rem;
  }
  .kpi-stack .kpi-label:first-child { margin-top: 0; }
  .kpi-stack .kpi-value {
    font-size: 1.05rem;
    font-weight: 700;
    color: #1a1d26;
    line-height: 1.35;
    margin-bottom: 0.35rem;
  }
  .map-card-body { width: 100%; }
  .risk-legend-bar {
    display: flex;
    flex-wrap: nowrap;
    align-items: stretch;
    width: 100%;
    max-width: 100%;
    box-sizing: border-box;
    margin-top: 0.35rem;
    margin-bottom: 0.15rem;
    border: 1px solid #e2e6ed;
    border-radius: 10px;
    overflow: hidden;
    background: #f8fafc;
  }
  .risk-legend-bar .risk-legend-item {
    flex: 1 1 0;
    min-width: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.45rem;
    padding: 0.55rem 0.35rem;
    font-size: 0.88rem;
    font-weight: 600;
    color: #2d3340;
    border-right: 1px solid #e2e6ed;
  }
  .risk-legend-bar .risk-legend-item:last-child { border-right: none; }
  .risk-legend-bar .dot {
    width: 12px;
    height: 12px;
    border-radius: 3px;
    flex-shrink: 0;
  }
  .legend {
    display:grid;
    grid-template-columns: 12px 1fr;
    gap: 0.45rem 0.55rem;
    align-items:center;
    margin-top: 0.35rem;
    font-size: 0.92rem;
    color: #2d3340;
  }
  .dot { width:12px; height:12px; border-radius: 3px; }
  .hr { height:1px; background: #e2e6ed; margin: 0.75rem 0; }
</style>
        """.strip(),
        unsafe_allow_html=True,
    )


def _read_csv(uploaded_file) -> pd.DataFrame:
    raw = uploaded_file.getvalue()
    # utf-8-sig 우선, 실패 시 utf-8로 fallback
    for enc in ("utf-8-sig", "utf-8"):
        try:
            return pd.read_csv(io.BytesIO(raw), encoding=enc)
        except Exception:
            continue
    return pd.read_csv(io.BytesIO(raw))


def _coerce_label(df: pd.DataFrame) -> Optional[pd.Series]:
    if "label" in df.columns:
        return df["label"]
    if "target_heavy_rain_flag" in df.columns:
        return df["target_heavy_rain_flag"]
    return None


def _pick_feature_cols(df: pd.DataFrame) -> list[str]:
    drop = set(LEAKY_COLS_DEFAULT)
    drop |= {"label", "split_type", "dataset_status", "is_trainable"}
    drop |= {"district_name", "base_datetime"}  # 식별자/시간은 우선 제외(원하면 확장)

    numeric_cols = [c for c in df.columns if c not in drop and pd.api.types.is_numeric_dtype(df[c])]
    # 숫자형이 거의 없을 때를 대비해, 숫자로 변환 가능한 컬럼을 추가 탐색
    if len(numeric_cols) < 3:
        for c in df.columns:
            if c in drop or c in numeric_cols:
                continue
            coerced = pd.to_numeric(df[c], errors="coerce")
            if coerced.notna().mean() >= 0.6:  # 대충이라도 숫자형이면 사용
                df[c] = coerced
                numeric_cols.append(c)
    return numeric_cols


def _train_baseline(
    df: pd.DataFrame,
    label_col: str,
    feature_cols: list[str],
    test_size: float,
    random_state: int,
) -> tuple[TrainedModel, dict]:
    X = df[feature_cols].copy()
    y = df[label_col].astype(int).copy()

    X_train, X_valid, y_train, y_valid = train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=random_state,
        stratify=y if y.nunique() == 2 else None,
    )

    pre = ColumnTransformer(
        transformers=[
            ("num", Pipeline([("imputer", SimpleImputer(strategy="median"))]), feature_cols),
        ],
        remainder="drop",
    )

    clf = LogisticRegression(
        max_iter=2000,
        class_weight="balanced",
        n_jobs=None,
    )

    pipe = Pipeline([("pre", pre), ("clf", clf)])
    pipe.fit(X_train, y_train)

    proba_valid = pipe.predict_proba(X_valid)[:, 1]
    pr_auc = float(average_precision_score(y_valid, proba_valid)) if y_valid.nunique() == 2 else float("nan")

    prec, rec, thr = precision_recall_curve(y_valid, proba_valid)
    f1 = (2 * prec * rec) / (prec + rec + 1e-12)
    best_i = int(np.nanargmax(f1)) if len(f1) else 0
    best_thr = float(thr[best_i - 1]) if best_i > 0 and (best_i - 1) < len(thr) else 0.5

    yhat_thr = (proba_valid >= best_thr).astype(int)
    metrics = {
        "rows": int(len(df)),
        "features": int(len(feature_cols)),
        "positive_rate": float(y.mean()) if len(y) else float("nan"),
        "pr_auc_valid": pr_auc,
        "threshold_best_f1": best_thr,
        "f1_valid": float(f1_score(y_valid, yhat_thr)) if y_valid.nunique() == 2 else float("nan"),
        "precision_valid": float(precision_score(y_valid, yhat_thr, zero_division=0)) if y_valid.nunique() == 2 else float("nan"),
        "recall_valid": float(recall_score(y_valid, yhat_thr, zero_division=0)) if y_valid.nunique() == 2 else float("nan"),
    }

    trained = TrainedModel(
        pipeline=pipe,
        feature_cols=feature_cols,
        threshold=best_thr,
        meta={"label_col": label_col, "random_state": random_state, "test_size": test_size},
    )
    return trained, metrics


def _predict(df: pd.DataFrame, model: TrainedModel) -> pd.DataFrame:
    missing = [c for c in model.feature_cols if c not in df.columns]
    if missing:
        raise ValueError(f"입력 데이터에 필요한 피처 컬럼이 없습니다: {missing[:10]}" + (" ..." if len(missing) > 10 else ""))
    X = df[model.feature_cols].copy()
    proba = model.pipeline.predict_proba(X)[:, 1]
    out = df.copy()
    out["risk_proba"] = proba
    out["risk_level"] = np.where(proba >= model.threshold, "주의(임계값↑)", "관심")
    return out


def _score_10(p: float) -> float:
    if p is None or (isinstance(p, float) and math.isnan(p)):
        return 0.0
    return float(np.clip(p, 0.0, 1.0) * 10.0)


def _risk_bucket(score10: float) -> tuple[str, str]:
    # (label, color)
    if score10 >= 8.0:
        return "매우 높음", "#b1121a"
    if score10 >= 6.0:
        return "높음", "#ff7a18"
    if score10 >= 4.0:
        return "보통", "#f7c948"
    return "낮음", "#34c759"


def _risk_gauge(p: float) -> go.Figure:
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=float(p) * 100.0,
            number={"suffix": "%"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": "#1f77b4"},
                "steps": [
                    {"range": [0, 30], "color": "#e8f4ff"},
                    {"range": [30, 60], "color": "#cfe8ff"},
                    {"range": [60, 80], "color": "#ffd9b3"},
                    {"range": [80, 100], "color": "#ffb3b3"},
                ],
            },
        )
    )
    fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=250)
    return fig


def _city_summary_scores(pred: pd.DataFrame) -> tuple[float, float, float]:
    """(구 평균 점수10, 최고 구 점수10, 최고 구 확률) — 상한만으로 과장되지 않게 평균과 최고를 함께 씀."""
    s = pred["risk_proba"].astype(float).fillna(0.0)
    if len(s) == 0:
        return 0.0, 0.0, 0.0
    mean10 = _score_10(float(s.mean()))
    max_p = float(s.max())
    max10 = _score_10(max_p)
    return mean10, max10, max_p


def _reference_case_html(score10_max: float) -> str:
    lo, hi = REFERENCE_SCORE10_GANGNAM_2022
    if score10_max >= lo:
        cmp_txt = "참고 사례 구간과 <b>비슷하거나 그 이상</b>입니다. 현장 확인·대피 안내를 우선 검토하세요."
    elif score10_max >= lo - 1.5:
        cmp_txt = "참고 사례에 <b>근접</b>한 수준입니다. 저지대·반지하 등 취약 시설을 점검하세요."
    else:
        cmp_txt = "참고 사례 대비 <b>상대적으로 낮은</b> 구간입니다(단, 국지 호우는 소규모에서도 급상승할 수 있음)."
    return f"""
<div class="muted" style="max-width:920px;margin:0 auto 0.75rem auto;text-align:center;line-height:1.45;">
  <b>사례 비교(참고)</b> · 2022년 8월 강남권 집중호우 당시, 동일 10점 척도로 환산한 <b>가정 구간 약 {lo:.1f}~{hi:.1f}점</b>을 기준으로 안내합니다(공식 재난 등급 아님).<br/>
  현재 화면의 <b>최고 구 점수 {score10_max:.1f}/10</b>은 위 구간과 비교했을 때 {cmp_txt}
</div>
    """.strip()


def _synthetic_timeline_for_district(
    base_dt: pd.Timestamp,
    current_p: float,
    past_rain_3h: float,
    hours_back: int = 6,
) -> pd.DataFrame:
    """스냅샷 1건일 때도 X축을 '시각'으로 보여주기 위한 단순 전개(실데이터 시계열이 있으면 대체)."""
    base_dt = pd.Timestamp(base_dt)
    rain_w = float(np.clip(past_rain_3h / 45.0, 0.0, 1.0))
    rows = []
    for h in range(hours_back, -1, -1):
        t = base_dt - pd.Timedelta(hours=h)
        frac = (hours_back - h) / max(hours_back, 1)
        # 과거로 갈수록 약간 낮게, 강수 가중 시 상승 곡선
        p = current_p * (0.72 + 0.22 * frac + 0.06 * rain_w * frac)
        p = float(np.clip(p, 0.0, 1.0))
        rows.append({"시각": t, "위험도(확률)": p})
    return pd.DataFrame(rows)


def _horizon_forecast_probs(base_p: float, past_rain_3h: float) -> tuple[list[str], list[float]]:
    """향후 1·2·3·4·6시간 단순 시뮬레이션(다중 시점 모델 도입 시 교체)."""
    w = float(np.clip(past_rain_3h / 40.0, 0.0, 1.2))
    labels = ["+1h", "+2h", "+3h", "+4h", "+6h"]
    mults = [1.02 + 0.06 * w, 1.05 + 0.10 * w, 1.10 + 0.14 * w, 1.08 + 0.10 * w, 1.02 + 0.04 * w]
    vals = [float(np.clip(base_p * m, 0.0, 1.0)) for m in mults]
    return labels, vals


@st.cache_data(show_spinner=False)
def _load_seoul_gu_geojson() -> dict:
    with open("data/seoul_gu_simple.geojson", "r", encoding="utf-8") as f:
        return json.load(f)


def _geojson_lonlat_bounds(geo: dict) -> tuple[float, float, float, float]:
    """(min_lon, max_lon, min_lat, max_lat) — Polygon/MultiPolygon 좌표 순회."""
    min_lon, max_lon = 180.0, -180.0
    min_lat, max_lat = 90.0, -90.0

    def visit_coord_pair(pair: list) -> None:
        nonlocal min_lon, max_lon, min_lat, max_lat
        if len(pair) < 2:
            return
        lon, lat = float(pair[0]), float(pair[1])
        min_lon, max_lon = min(min_lon, lon), max(max_lon, lon)
        min_lat, max_lat = min(min_lat, lat), max(max_lat, lat)

    def walk(obj: object) -> None:
        if not obj:
            return
        if isinstance(obj[0], (int, float)):
            visit_coord_pair(obj)  # type: ignore[arg-type]
            return
        for item in obj:
            walk(item)

    for feat in geo.get("features", []):
        g = feat.get("geometry") or {}
        t, coords = g.get("type"), g.get("coordinates")
        if not coords:
            continue
        if t == "Polygon":
            walk(coords)
        elif t == "MultiPolygon":
            for poly in coords:
                walk(poly)
    if max_lon < min_lon:
        return 126.76, 127.19, 37.42, 37.71
    return min_lon, max_lon, min_lat, max_lat


@st.cache_data(show_spinner=False)
def _district_centroids() -> pd.DataFrame:
    geo = _load_seoul_gu_geojson()
    rows = []
    for feat in geo.get("features", []):
        name = feat.get("properties", {}).get("name")
        geom = feat.get("geometry", {})
        coords = geom.get("coordinates", [])
        pts = []
        if geom.get("type") == "Polygon" and coords:
            for ring in coords:
                for lon, lat in ring:
                    pts.append((lon, lat))
        elif geom.get("type") == "MultiPolygon" and coords:
            for poly in coords:
                for ring in poly:
                    for lon, lat in ring:
                        pts.append((lon, lat))
        if not pts or not name:
            continue
        lons = [p[0] for p in pts]
        lats = [p[1] for p in pts]
        rows.append({"district_name": str(name).strip(), "lon": float(np.mean(lons)), "lat": float(np.mean(lats))})
    return pd.DataFrame(rows)


def _seoul_gu_map(pred: pd.DataFrame, focus_district: Optional[str] = None) -> Optional[go.Figure]:
    if "district_name" not in pred.columns or "risk_proba" not in pred.columns:
        return None
    try:
        geo = _load_seoul_gu_geojson()
    except Exception:
        return None

    df = pred.copy()
    df["district_name"] = df["district_name"].astype(str).str.strip()
    df["score10"] = df["risk_proba"].apply(_score_10)

    center = {"lat": 37.5665, "lon": 126.9780}
    zoom = 9.35
    fit_bounds: Optional[dict[str, float]] = None
    focus_gu: Optional[str] = None
    if focus_district and str(focus_district).strip() != MAP_FOCUS_SEOUL_ALL:
        focus_gu = str(focus_district).strip()
    if focus_gu:
        try:
            c = _district_centroids()
            row = c[c["district_name"] == focus_gu]
            if len(row):
                center = {"lat": float(row.iloc[0]["lat"]), "lon": float(row.iloc[0]["lon"])}
                zoom = 11.4
        except Exception:
            pass
    else:
        # 첫 진입: 서울시 행정구역 전체가 들어오도록 bounds + 여백
        mn_lon, mx_lon, mn_lat, mx_lat = _geojson_lonlat_bounds(geo)
        pad_lon = max((mx_lon - mn_lon) * 0.12, 0.02)
        pad_lat = max((mx_lat - mn_lat) * 0.12, 0.015)
        fit_bounds = {
            "west": mn_lon - pad_lon,
            "east": mx_lon + pad_lon,
            "south": mn_lat - pad_lat,
            "north": mx_lat + pad_lat,
        }
        center = {"lat": (mn_lat + mx_lat) / 2, "lon": (mn_lon + mx_lon) / 2}

    fig = px.choropleth_mapbox(
        df,
        geojson=geo,
        locations="district_name",
        featureidkey="properties.name",
        color="risk_proba",
        color_continuous_scale=["#2a4a6f", "#5a7a9a", "#f7c948", "#ff7a18", "#b1121a"],
        range_color=(0.0, max(0.05, float(np.nanmax(df["risk_proba"])) if len(df) else 1.0)),
        hover_name="district_name",
        hover_data={"risk_proba": ":.3f", "score10": ":.1f"},
        # 밝은 베이스맵 + 진한 경계로 가독성 확보
        mapbox_style="carto-positron",
        center=center,
        zoom=zoom,
        opacity=0.82,
    )
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=560, coloraxis_colorbar=dict(title="위험도"))
    if fit_bounds is not None:
        fig.update_layout(mapbox=dict(bounds=fit_bounds))
    fig.update_traces(
        marker_line_width=2.2,
        marker_line_color="rgba(20, 35, 55, 0.92)",
    )

    # 구 라벨(점수) 오버레이
    try:
        cent = _district_centroids()
        lab = cent.merge(df[["district_name", "score10"]], on="district_name", how="left")
        lab["text"] = lab.apply(
            lambda r: f"{r['district_name']}<br><b>{(r['score10'] if pd.notna(r['score10']) else 0.0):.1f}</b>",
            axis=1,
        )
        fig.add_trace(
            go.Scattermapbox(
                lat=lab["lat"],
                lon=lab["lon"],
                mode="text",
                text=lab["text"],
                textfont=dict(color="rgba(26,29,38,0.92)", size=12, family="Arial Black"),
                hoverinfo="skip",
                showlegend=False,
            )
        )
    except Exception:
        pass

    return fig


def _render_hud(pred: pd.DataFrame, model: Optional[TrainedModel]) -> None:
    mean10, max10, _ = _city_summary_scores(pred)
    bucket, color = _risk_bucket(max10)

    st.markdown(
        f"""
<div class="hud-hero">
  <div class="hud-title">서울시 데이터 기반 폭우 발생 가능성 예측 시스템 (프로토타입)</div>
  <div class="hud-sub">
    <span class="hud-pill">서울 전체 요약: <b style="color:{color}">{bucket}</b>
    · 구 평균 <b>{mean10:.1f}/10</b> · 최고 구 <b>{max10:.1f}/10</b></span>
  </div>
</div>
        """.strip(),
        unsafe_allow_html=True,
    )
    st.markdown(_reference_case_html(max10), unsafe_allow_html=True)

    # 3분할 레이아웃
    left, center, right = st.columns([1.05, 2.2, 1.05], gap="large")

    top = pred.sort_values("risk_proba", ascending=False).reset_index(drop=True)
    top_name = str(top.loc[0, "district_name"]) if "district_name" in top.columns and len(top) else "-"
    top_p = float(top.loc[0, "risk_proba"]) if len(top) else 0.0
    top_score10 = _score_10(top_p)
    top_row = top.iloc[0] if len(top) else None
    rows: list[tuple[int, str, float]] = []
    focus: Optional[str] = None

    with left:
        st.markdown('<div class="card"><h4>주요 기상 데이터</h4>', unsafe_allow_html=True)

        def _fmt_stack_val(v: object, default: str = "-") -> str:
            if v is None or (isinstance(v, float) and math.isnan(v)):
                return default
            return str(v)

        elev_val = None
        river_val = None
        if top_row is not None:
            for col in ("elev_m", "elevation_m", "avg_elevation_m"):
                if col in top.columns and pd.notna(top_row.get(col)):
                    try:
                        elev_val = f"{float(top_row[col]):.2f}"
                    except (TypeError, ValueError):
                        elev_val = str(top_row[col])
                    break
            for col in ("river_stage_m", "river_max_stage_m"):
                if col in top.columns and pd.notna(top_row.get(col)):
                    try:
                        river_val = f"{float(top_row[col]):.2f}"
                    except (TypeError, ValueError):
                        river_val = str(top_row[col])
                    break

        stack_html = ['<div class="kpi-stack">']
        if top_row is not None and "base_datetime" in top.columns:
            stack_html.append('<div class="kpi-label">기준 시각</div>')
            stack_html.append(f'<div class="kpi-value">{_fmt_stack_val(top_row["base_datetime"])}</div>')
        stack_html.append('<div class="kpi-label">최고 위험 구</div>')
        stack_html.append(f'<div class="kpi-value">{top_name}</div>')
        stack_html.append('<div class="kpi-label">해당 구 점수</div>')
        stack_html.append(f'<div class="kpi-value">{top_score10:.1f}/10</div>')
        if top_row is not None and "past_rain_3h_mm" in top.columns:
            stack_html.append('<div class="kpi-label">과거 3h 강수</div>')
            stack_html.append(f'<div class="kpi-value">{float(top_row["past_rain_3h_mm"]):.1f} mm</div>')
        if top_row is not None and "temp_c" in top.columns:
            stack_html.append('<div class="kpi-label">기온</div>')
            stack_html.append(f'<div class="kpi-value">{float(top_row["temp_c"]):.1f} ℃</div>')
        if top_row is not None and "humidity_pct" in top.columns:
            stack_html.append('<div class="kpi-label">습도</div>')
            stack_html.append(f'<div class="kpi-value">{float(top_row["humidity_pct"]):.0f} %</div>')
        stack_html.append('<div class="kpi-label">평균 고도(m)</div>')
        stack_html.append(f'<div class="kpi-value">{elev_val if elev_val is not None else "-"}</div>')
        stack_html.append('<div class="kpi-label">하천 수위(m)</div>')
        stack_html.append(f'<div class="kpi-value">{river_val if river_val is not None else "-"}</div>')
        stack_html.append("</div>")
        st.markdown("".join(stack_html), unsafe_allow_html=True)

        st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
        st.markdown("<h4>위험 지역 알림 (상위 5개)</h4>", unsafe_allow_html=True)
        rows.clear()
        for i in range(min(5, len(top))):
            dn = str(top.loc[i, "district_name"]) if "district_name" in top.columns else str(i)
            sc = _score_10(float(top.loc[i, "risk_proba"]))
            rows.append((i + 1, dn, sc))
        if rows:
            df_rank = pd.DataFrame(rows, columns=["순위", "구", "점수(10점)"])
            st.dataframe(df_rank, use_container_width=True, hide_index=True)
            top5_names = [r[1] for r in rows]
            focus = st.selectbox(
                "지도에서 초점 맞출 구",
                options=[MAP_FOCUS_SEOUL_ALL] + top5_names,
                index=0,
                key="hud_map_focus_district",
                help="서울시 전체는 행정구역 전체가 보이도록 맞춥니다. 구를 고르면 해당 구 중심으로 확대됩니다.",
            )
        else:
            st.caption("표시할 데이터가 없습니다.")
            focus = None

        if top_score10 >= 8.0:
            st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
            st.markdown("<h4>대응 안내</h4>", unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                st.link_button(
                    "대피소·민방위 시설(서울시)",
                    "https://www.seoul.go.kr/citygm/gm.do",
                    help="행정 안내 페이지(실제 대피는 119·지자체 안내를 따르세요).",
                )
            with c2:
                st.link_button(
                    "교통·도로 통제(Seoul TOPIS)",
                    "https://topis.seoul.go.kr/",
                    help="실시간 교통정보 및 우천 시 도로 상황 확인.",
                )

        st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
        st.markdown("<h4>예측 모델</h4>", unsafe_allow_html=True)
        tm = st.session_state.get("train_metrics")
        if tm:
            st.markdown(f'<div class="muted">PR-AUC(valid): <b>{tm.get("pr_auc_valid", float("nan")):.4f}</b></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="muted">F1(valid): <b>{tm.get("f1_valid", float("nan")):.4f}</b></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="muted">임계값(F1 최적): <b>{tm.get("threshold_best_f1", 0.5):.3f}</b></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="muted">Baseline(로지스틱 회귀, class_weight=balanced)</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with center:
        st.markdown('<div class="card map-card-body"><h4 style="text-align:center;">서울시 위험도 지도</h4>', unsafe_allow_html=True)
        mfig = _seoul_gu_map(pred, focus_district=focus if len(rows) else None)
        if mfig is not None:
            st.plotly_chart(mfig, use_container_width=True, key="hud_map_chart")
        else:
            st.caption("지도 표시를 위해 `district_name`(예: 강남구) 매칭이 필요합니다.")

        st.markdown(
            """
<div class="risk-legend-bar">
  <div class="risk-legend-item"><span class="dot" style="background:#b1121a;"></span>매우 높음</div>
  <div class="risk-legend-item"><span class="dot" style="background:#ff7a18;"></span>높음</div>
  <div class="risk-legend-item"><span class="dot" style="background:#f7c948;"></span>보통</div>
  <div class="risk-legend-item"><span class="dot" style="background:#34c759;"></span>낮음</div>
</div>
            """.strip(),
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div style="height: 2.75rem;"></div>', unsafe_allow_html=True)
        with st.expander("동 단위(세부) 보기 — 로드맵", expanded=False):
            st.caption(
                "실제 대피·통제는 동·필지 단위가 중요합니다. 행정동 경계 GeoJSON과 결합해 줌인 레이어를 붙이면 "
                "구 내부 취약 지점을 표시할 수 있습니다. (데이터 계약·용량 확보 후 확장)"
            )
            st.link_button("서울시 스마트도시 지도(emap)", "https://map.seoul.go.kr/", help="행정·시설 참고용")

    with right:
        st.markdown('<div class="card"><h4>실시간 위험 추이</h4>', unsafe_allow_html=True)
        st.markdown(
            f"최고 위험 구 **{top_name}** 기준  \n - X축은 시각(데이터 1건이면 최근 6시간 전개 시뮬레이션)"
        )

        df_ts = pred.copy()
        if "base_datetime" in df_ts.columns:
            df_ts["base_datetime"] = pd.to_datetime(df_ts["base_datetime"], errors="coerce")
        sel = top_name if "district_name" in pred.columns else None
        if sel and "district_name" in df_ts.columns:
            df_sel = df_ts[df_ts["district_name"].astype(str).str.strip() == str(sel).strip()].copy()
        else:
            df_sel = df_ts.copy()

        if "base_datetime" in df_sel.columns and df_sel["base_datetime"].notna().sum() >= 2:
            df_plot = df_sel.sort_values("base_datetime").rename(columns={"risk_proba": "위험도(확률)", "base_datetime": "시각"})
            fig_line = px.line(df_plot, x="시각", y="위험도(확률)", markers=True)
            fig_line.update_layout(height=230, margin=dict(l=0, r=0, t=10, b=0), template="plotly_white")
            fig_line.update_xaxes(title_text="시각")
            fig_line.update_yaxes(range=[0, 1], title_text="위험도(확률)")
            st.plotly_chart(fig_line, use_container_width=True)
        else:
            if len(df_sel) and "base_datetime" in df_sel.columns:
                t0 = pd.to_datetime(df_sel["base_datetime"].iloc[0], errors="coerce")
                if pd.isna(t0):
                    t0 = pd.Timestamp.now()
            else:
                t0 = pd.Timestamp.now()
            rain3 = float(top_row["past_rain_3h_mm"]) if top_row is not None and "past_rain_3h_mm" in top.columns else 0.0
            tl = _synthetic_timeline_for_district(pd.Timestamp(t0), top_p, rain3)
            fig_line = px.line(tl, x="시각", y="위험도(확률)", markers=True)
            fig_line.update_layout(height=230, margin=dict(l=0, r=0, t=10, b=0), template="plotly_white")
            fig_line.update_xaxes(title_text="시각", tickformat="%H:%M")
            fig_line.update_yaxes(range=[0, 1], title_text="위험도(확률)")
            st.plotly_chart(fig_line, use_container_width=True)

        st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
        st.markdown("<h4>향후 시간대별 위험도 (시뮬레이션)</h4>", unsafe_allow_html=True)
        st.markdown(
            "현재 확률·과거 3h 강수 가중 단순 전개.  \n운영 시 +1h/+3h/+6h 다중 출력 모델로 교체 권장."
        )

        rain3 = float(top_row["past_rain_3h_mm"]) if top_row is not None and "past_rain_3h_mm" in top.columns else 0.0
        h_labels, h_vals = _horizon_forecast_probs(float(np.clip(top_p, 0, 1)), rain3)
        fig_bar = px.bar(
            pd.DataFrame({"예측 시점": h_labels, "위험도(확률)": h_vals}),
            x="예측 시점",
            y="위험도(확률)",
            color="위험도(확률)",
            color_continuous_scale=["#f7c948", "#ff7a18", "#b1121a"],
        )
        fig_bar.update_layout(height=250, margin=dict(l=0, r=0, t=10, b=0), template="plotly_white", showlegend=False)
        fig_bar.update_yaxes(range=[0, 1], title_text="위험도(확률)")
        fig_bar.update_coloraxes(showscale=False)
        st.plotly_chart(fig_bar, use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)


def main() -> None:
    st.set_page_config(page_title="서울 폭우 위험 관제 대시보드", layout="wide")
    _inject_css()

    st.sidebar.header("데이터/모델")
    mode = st.sidebar.radio("화면", ["대시보드(샘플)", "학습(라벨 포함 CSV)", "실시간 추론(라벨 없음 CSV)", "모델 파일 불러오기"], index=0)

    if "trained_model" not in st.session_state:
        st.session_state["trained_model"] = None
    if "train_metrics" not in st.session_state:
        st.session_state["train_metrics"] = None

    if mode == "대시보드(샘플)":
        train_df = pd.read_csv("data/sample_train.csv")
        rt_df = pd.read_csv("data/sample_realtime.csv")
        feats = _pick_feature_cols(train_df)
        model, metrics = _train_baseline(
            train_df,
            "label" if "label" in train_df.columns else "target_heavy_rain_flag",
            feats,
            0.2,
            42,
        )
        st.session_state["trained_model"] = model
        st.session_state["train_metrics"] = metrics
        pred = _predict(rt_df, model)
        _render_hud(pred, model)
        return

    if mode == "학습(라벨 포함 CSV)":
        st.markdown('<div class="hud-title">학습(라벨 포함 CSV)</div>', unsafe_allow_html=True)
        st.caption("라벨 컬럼: `label` 또는 `target_heavy_rain_flag` 중 하나가 필요합니다.")

        up = st.file_uploader("학습 CSV 업로드", type=["csv"])
        if not up:
            st.stop()
        df = _read_csv(up)

        y = _coerce_label(df)
        if y is None:
            st.error("라벨 컬럼(`label` 또는 `target_heavy_rain_flag`)을 찾지 못했습니다.")
            st.dataframe(df.head(30), use_container_width=True)
            st.stop()

        label_col = "label" if "label" in df.columns else "target_heavy_rain_flag"
        st.caption(f"라벨 컬럼: `{label_col}`")

        feats_auto = _pick_feature_cols(df)
        st.sidebar.subheader("학습 설정")
        test_size = st.sidebar.slider("검증 비율", 0.1, 0.5, 0.2, 0.05)
        random_state = st.sidebar.number_input("random_state", value=42, step=1)

        st.sidebar.subheader("피처 선택")
        selected_feats = st.sidebar.multiselect("사용할 피처(숫자형)", options=feats_auto, default=feats_auto)
        if len(selected_feats) < 2:
            st.warning("피처를 2개 이상 선택하세요.")
            st.stop()

        if st.button("학습 실행", type="primary"):
            model, metrics = _train_baseline(df, label_col, selected_feats, float(test_size), int(random_state))
            st.session_state["trained_model"] = model
            st.session_state["train_metrics"] = metrics

            st.success("학습 완료")
            st.json(metrics)

            # 저장
            st.divider()
            st.subheader("모델 저장")
            fname = st.text_input("파일명", value="heavyrain_model.joblib")
            if st.button("모델 파일로 저장"):
                joblib.dump(model, fname)
                st.success(f"저장 완료: `{fname}`")

        st.divider()
        st.subheader("데이터 미리보기")
        st.dataframe(df.head(50), use_container_width=True)
        return

    if mode == "모델 파일 불러오기":
        st.markdown('<div class="hud-title">모델 파일 불러오기</div>', unsafe_allow_html=True)
        upm = st.file_uploader("모델 파일 업로드", type=["joblib"])
        if not upm:
            st.stop()
        model = joblib.load(io.BytesIO(upm.getvalue()))
        if not isinstance(model, TrainedModel):
            st.error("이 대시보드에서 저장한 TrainedModel 형식이 아닙니다.")
            st.stop()
        st.session_state["trained_model"] = model
        st.success("모델 로드 완료")
        st.json({"feature_cols": model.feature_cols, "threshold": model.threshold, "meta": model.meta})
        return

    # 실시간 추론
    st.markdown('<div class="hud-title">실시간 추론(라벨 없음 CSV)</div>', unsafe_allow_html=True)
    model: Optional[TrainedModel] = st.session_state.get("trained_model")
    if model is None:
        st.warning("먼저 학습을 하거나 모델 파일을 불러오세요.")
        st.stop()

    uprt = st.file_uploader("실시간 CSV 업로드", type=["csv"])
    if not uprt:
        st.stop()
    df = _read_csv(uprt)

    try:
        pred = _predict(df, model)
    except Exception as e:
        st.error(str(e))
        st.dataframe(df.head(30), use_container_width=True)
        st.stop()

    _render_hud(pred, model)


if __name__ == "__main__":
    main()

