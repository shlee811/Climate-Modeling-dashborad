# 🌧️ 폭우 위험 예측 대시보드 (프로토타입)

기상 관측/파생 데이터를 기반으로 **향후 3시간 내 폭우(20/40 기준) 위험도**를 예측·시각화하는 로컬 대시보드입니다.

## 배경 (실제 사례)
- 2022년 8월 서울 강남권 중심의 **국지성 집중호우**로 대규모 침수·교통 마비 등 피해가 발생했습니다.
- 단시간 강수는 “수치”로는 제공되지만, 현장에서 바로 쓰기 쉬운 **직관적인 위험 판단(구별 위험도)** 및 **대응 지원 화면**은 부족합니다.

## 주요 기능
- CSV 업로드(학습/실시간) 기반
- 간단 Baseline 모델 학습(로지스틱 회귀) 및 임계값(Threshold) 튜닝
- 구(`district_name`)별 **위험도(확률)** 랭킹, 분포, 시계열(가능 시) 시각화
- 모델 파일 저장/불러오기(`.joblib`)

## 입력 데이터 (권장 스키마)
`MODELING_HANDOFF.md` 기준 권장 컬럼 예시:
- 키: `district_name`, `base_datetime`
- 피처(예): `temp_c`, `humidity_pct`, `dew_point_c`, `past_rain_3h_mm`, `temp_change_3h_c`, `humidity_change_3h_pct`, `moist_energy`
- 라벨: `label` (또는 `target_heavy_rain_flag`)

> 주의: `target_rain_3h_mm` 등 “미래 누적 강수량”은 라벨 원천이므로 **피처로 쓰지 않도록** 대시보드에서 기본 제외합니다.

## 실행 방법

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## 샘플로 바로 보기
- `data/sample_train.csv`: 학습 예시(라벨 포함)
- `data/sample_realtime.csv`: 실시간 추론 예시(라벨 없음)

## 확장 아이디어
- XGBoost/LightGBM 모델 연결
- DB(예: `mart.seoul_district_realtime_features_latest`)와 직접 연동
- 알림(임계값 초과 시 Slack/문자), 대응 매뉴얼(우선순위/체크리스트)까지 포함

# Climate-Modeling-dashborad
