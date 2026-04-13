# 모델링 및 분석 담당자 안내

본 문서는 서울시 구 단위 폭우 대응 프로젝트의 모델링 및 분석 담당자를 위한 안내 문서입니다.

## 1. 문서 목적
본 문서의 목적은 `수집/전처리 완료된 데이터 구조`를 기준으로,

- 학습용 데이터셋
- 검증/테스트 분할 기준
- 실시간 추론 입력 구조
- 라벨 정의와 예외 처리 원칙

을 혼동 없이 바로 사용할 수 있게 하는 것입니다.

중요한 점은 `운영용 실시간 feature`와 `학습용 데이터셋`이 이미 분리되어 있다는 점입니다.

## 2. 제공 파일
데이터 구조와 사용 규칙은 아래만 맞춰 전달해도 된다.

외부 전달본에 넣을 것(권장)

- 본 문서(`MODELING_HANDOFF.md`)
- `README.md`
- `trainset` / `realtime` / `pending` 샘플 CSV

SQL(`sql/*.sql`)

- 모델링 담당자에게 SQL 파일을 같이 줄 필요는 없다. 뷰 이름·컬럼·split·라벨 등 계약은 README·본 문서·샘플 CSV로 전달하는 것으로 충분하다.
- 뷰/DDL 원문이 필요하면 내부 저장소 접근 또는 운영·데이터 담당에게 요청한다. (참고로 정의 위치를 짚을 때 쓰는 파일 예: `sql/016_seoul_district_heavyrain_datasets.sql`, `sql/027_seoul_district_model_features_v2.sql`, `sql/022_seoul_construction_progress_tables.sql` 등 — 아래 §3에도 경로가 나온다.)

참고 대상에서 제외 가능한 파일

- `collectors/`, `launchd/`, `scripts/run_collector.sh`, `.env`, raw/std 적재용 스크립트 전반

즉, 외부 번들은 `학습에 필요한 데이터 계약`만 포함하면 되고, SQL은 선택·내부용이다.

## 3. 각 파일의 의미
### `README.md`
- 전체 데이터 구조 설명
- 레이어 구조(`raw -> std -> mart -> ref/meta`)
- 라벨 정의
- split 기준
- 예외 데이터 처리 원칙
- 추천 학습/검증 방향
- 서울시 건설공사 추진 현황 등 trainset과 분리된 참조 적재(`ref.seoul_construction_progress`) 요약

### `data/seoul_district_grids.csv` 및 `sql/017_seoul_district_grid_map_resync.sql`
- 구별 대표 행정동·위경도·KMA `(nx, ny)` 단일 기준(`representative_dong_kma_grid_v1`).
- `meta.seoul_district_grid_map`은 위 CSV와 동기화되어야 하며, 격자 변경 시 `017` 스크립트로 재적재한다.
- 기상청 포털 백필(`서울 초단기실황` CSV)을 쓸 때는 아래를 구분해 두는 것이 안전합니다.
  - 운영·API 수집 격자: `seoul_district_grids.csv`의 `(nx, ny)` 한 쌍이 “그 구의 대표 격자”입니다.
  - 포털 원본 헤더 격자: 각 CSV 첫 줄의 `location:nx_ny`는 파일마다 다를 수 있고, 같은 구·같은 연도라도 변수(강수·기온·풍속 등)별로 서로 다른 `(nx, ny)`에 흩어진 배포가 있습니다. 이 경우 `representative_dong` 행의 `(nx, ny)`와 일치하지 않아도 원본이 그렇게 나온 것일 수 있습니다.
- `ingest/portal_ultra_now_folder_loader.py`의 현재 정책(A안)은 `(district_name, nx, ny, 연도)` 그룹마다 6개 변수 슬롯이 모두 그 격자에 존재할 때만 `std.kma_ultra_now_std` / `mart.seoul_district_ultra_now`에 넣습니다. 격자가 변수별로 쪼개지면 해당 그룹은 스킵되며, “파일은 있는데 로그에는 missing”인 현상은 다른 격자 그룹에는 그 슬롯 파일이 없기 때문인 경우가 많습니다.
- README §6 `포털 백필: 그룹 단위·스킵·격자 분리`에 구체 사례(관악구 2024, 서대문구 2025)와 B안(같은 구·연도에서 격자 병합, 미구현) 설명을 적어 두었습니다. 학습 데이터에 포털 백필 구간을 넣을 때는 어느 정책으로 적재했는지를 스냅샷과 함께 남기는 것을 권장합니다.

### `sql/016_seoul_district_heavyrain_datasets.sql`
- 모델링에 직접 사용할 뷰 정의
- 실시간/학습/pending 데이터셋 분리 구조
- 타깃과 메타 컬럼 정의
- 시간 기준 split 로직

### `sql/012_district_model_features.sql` / `sql/027_seoul_district_model_features_v2.sql`
- 학습셋의 원천 feature가 어떻게 구성되는지 보여주는 참고 파일(027이 최신 컬럼 세트를 반영)
- 어떤 실시간/정적 feature가 붙는지 확인하는 용도

### 샘플 CSV
- 실제 컬럼명 확인
- NULL/결측/lag 컬럼 확인
- 모델 입력 파이프라인 빠른 시작

## 4. 작업 전 확인해야 할 핵심 사항
아래 항목은 모델링 및 분석 작업 전에 반드시 확인해야 합니다.

### 기본 trainset과 권장 장기 학습셋(v5.1) — 역할 분리
- 운영·실시간 파이프라인과 같은 라벨·뷰 계약으로 이해·디버깅할 때의 기본 학습 뷰는 `mart.seoul_district_heavyrain_trainset`(및 `..._pending`)입니다. 라벨 원천은 서울시 강우량 구단위 집계이며, 운영 DB·서빙 관점 district universe는 서울 25개 구입니다(종로구 AWS는 원천 부재이나 뷰에서 인접 구 보간).
- `2020~2025` 장기 이력, AWS-only 전처리, 고정 split, train/serve 동일 규칙이 필요할 때의 권장 canonical 산출물은 `mart.hrain_v5_1_aws_*` 테이블·뷰 및 `data/trainset/`의 v5.1 CSV입니다. 이 경로만 district universe 24개 구·종로구 제외로 고정됩니다(README·본 문서 §14).

두 축을 혼동하지 말 것: “지금 당장 heavyrain_trainset으로 프로토타입”과 “논문·재현용으로 v5.1로 시작”은 서로 다른 데이터 계약입니다.

### `mart.seoul_district_model_features` — trainset에 들어가는 입력 계약(정적·준정적)
`heavyrain_trainset` 행의 feature는 이 뷰(및 016 정의)를 중심으로 붙습니다. 현재 구현 기준 포함·미포함은 다음과 같습니다.

| 구분 | 내용 |
| --- | --- |
| 포함 | 침수흔적도 집계, 자연재해위험개선지구 집계, `rain_gauge_current_count`, 취약계층 밀집도 9컬럼(`elderly_*`, `disabled_*`, `basic_livelihood_*`, `basement_*`, `aged_basement_*`) — 뷰 정의 `sql/027_seoul_district_model_features_v2.sql` |
| 미포함 | `floating_pop_korean*`(OA-15439), worker(`total_worker_count` 등), OA-2540 건설공사(`ref.seoul_construction_progress`) — 필요 시 별도 as-of·시점 정의 후 조인 |

### 학습 데이터와 실시간 추론 데이터의 차이
| 구분 | 사용 뷰/파일 | 시간 기준 | 라벨 여부 | 주요 목적 |
| --- | --- | --- | --- | --- |
| 학습/검증/테스트 데이터 | `mart.seoul_district_heavyrain_trainset` | 과거 시점 | 라벨 확정 | 모델 학습, 검증, 테스트 |
| 실시간 추론 데이터 | `mart.seoul_district_realtime_features_latest` | 현재 최신 시점 | 라벨 없음 | 운영 중 현재 위험 추론 |
| pending 데이터 | `mart.seoul_district_heavyrain_trainset_pending` | 현재 최신 시점 | 아직 미확정 | 향후 labeled 데이터로 편입될 후보 확인 |

즉, `train/valid/test`는 과거 라벨 확정 데이터이고, `realtime`은 모델 완성 후 현재 시점 위험도를 추론하기 위한 입력 데이터입니다.

### 1) 학습 행 단위
- 학습용 1행은 `district_name + base_datetime` 기준입니다.
- 현재 버전에서는 `product_type = 'ultra_now'`만 사용합니다.
- 즉, `base_datetime` 시점에 실제로 알고 있던 정보로 `미래 3시간`을 예측하는 구조입니다.

### 2) 어떤 뷰를 써야 하는지
- 실시간 추론 입력: `mart.seoul_district_realtime_features_latest`
- 학습/검증/테스트 입력: `mart.seoul_district_heavyrain_trainset`
- 아직 라벨 미확정인 최신 행 확인: `mart.seoul_district_heavyrain_trainset_pending`

### 3) 라벨 정의
- `target_rain_3h_mm`
  - `base_datetime` 이후 `3시간 누적 강수량`
- `target_rain_1h_mm`
  - `base_datetime` 이후 `1시간 누적 강수량`
- `target_heavy_rain_flag`
  - 아래 조건 중 하나라도 만족하면 `1`, 아니면 `0`
    - `target_rain_1h_mm >= 20`
    - `lead(+1h, +2h, +3h)`의 `target_rain_1h_mm` 중 하나 이상이 `>= 20`
    - `target_rain_3h_mm >= 40`
    - `lead(+1h, +2h, +3h)`의 `target_rain_3h_mm` 중 하나 이상이 `>= 40`

### 4) 라벨 원천
- 기본 라벨 원천은 `AWS`가 아니라 `서울시 강우량 정보`입니다.
- 사용 원천 뷰는 `mart.seoul_rainfall_district_latest`입니다.
- 현재는 `max_rain_10m_mm`를 미래 3시간 창에서 합산해 라벨을 만듭니다.

### 5) 데이터 누수 방지 원칙
- feature는 반드시 `base_datetime` 시점까지의 값만 사용합니다.
- 타깃은 반드시 그 이후 미래 3시간으로 계산합니다.
- 랜덤 분할은 사용하지 않고, 시간 기준 split만 사용합니다.

### 6) 파생 변수 통일 (모델링 요청 반영)
`mart.seoul_district_heavyrain_trainset` / `..._pending`에 아래 파생 컬럼을 추가했습니다.

- `dew_point_c`
  - 이슬점(섭씨). `temp_c`, `humidity_pct`로 Magnus 공식 계산
  - `humidity_pct <= 0` 또는 입력 결측이면 `NULL`
- `past_rain_3h_mm`
  - 과거 3시간 누적 강수량(`현재 + 1시간 전 + 2시간 전`)
  - 미래 라벨(`target_rain_3h_mm`)과 구분되는 feature
- `temp_change_3h_c`
  - `temp_c - 3시간 전 temp_c`
- `humidity_change_3h_pct`
  - `humidity_pct - 3시간 전 humidity_pct`
- `moist_energy`
  - `(temp_c * humidity_pct) / 100`
- `label`
  - 협업 편의용 alias. 값은 `target_heavy_rain_flag`와 동일(20/40 + lead 3스텝 규칙)

주의: `target_rain_3h_mm`는 미래 3시간 라벨 원천이므로 feature로 직접 사용하면 안 됩니다.  
모델 입력용 3시간 강수는 `past_rain_3h_mm`를 사용하세요.

### OA-2540 건설공사 추진 현황 — 건설·인프라 맥락(노출 해석 보조) 참조 데이터

이 항은 [열린데이터광장 OA-2540 데이터셋 안내 페이지](https://data.seoul.go.kr/dataList/OA-2540/S/1/datasetView.do)(OpenAPI 서비스 `ListOnePMISBizInfo`) 건설공사 추진 현황만 다룹니다. 아래 OA-15439 내국인 생활인구 proxy와는 별개이며, “노출”을 말할 때도 여기서는 공사·시설·인프라 맥락을 의미합니다(OA-15439 인구 proxy 아님).

- 원천: Open API `ListOnePMISBizInfo`, 스키마 `sql/022_seoul_construction_progress_tables.sql`.
- OA-2540 건설 데이터는 `mart.seoul_district_model_features`·`mart.seoul_district_heavyrain_trainset`·`mart.seoul_district_realtime_features_latest` 어디에도 컬럼으로 자동 포함되지 않습니다. 노출·인프라 맥락 피처가 필요하면 `ref.seoul_construction_progress` 등에서 별도 조인·시점 정의가 필요합니다.
- 적재: `raw.seoul_construction_progress_raw`, `ref.seoul_construction_progress`, `ref.seoul_construction_progress_summary`.
- 자치구명은 서울 25개 구 표준명으로 정규화된 행만 `ref`에 남고, `서울지역외` 등은 제외. 키는 `biz_cd`, 수집마다 전체 스냅샷 upsert·미수신 `biz_cd` 삭제.
- 시계열 키가 `base_datetime`이 아니라 수집 시점 스냅샷이므로 학습에 넣을 때는 조인 시점(예: `requested_at`)과 누수 검토가 필요합니다.
- 라이선스: 공공누리 4유형 안내. README·데이터셋 페이지에서 사용 범위 확인.

### OA-15439 내국인 생활인구 proxy — realtime 서빙 뷰 전용 as-of 참조

이 항은 [열린데이터광장 OA-15439 데이터셋 안내 페이지](https://data.seoul.go.kr/dataList/OA-15439/S/1/datasetView.do)(OpenAPI 서비스 `SPOP_LOCAL_RESD_JACHI`) 기반 내국인 생활인구 proxy만 다룹니다. 위 OA-2540 건설공사와 혼동하지 말 것.

적재·스키마·운영 해석은 `sql/023_seoul_living_population_korean_district_tables.sql`, `sql/024_seoul_living_population_korean_operational.sql`, README Living population 절, `sql/verify_seoul_living_population_korean.sql`을 참고합니다.

계약 요약: `floating_pop_korean*`는 `mart.seoul_district_realtime_features_latest`에만 as-of로 붙습니다. `mart.seoul_district_model_features`와 `mart.seoul_district_heavyrain_trainset`(및 `..._pending`)에는 자동 포함되지 않습니다. realtime에 컬럼이 있다고 trainset에도 있다고 단정하면 안 됩니다.

- Realtime 서빙(`mart.seoul_district_realtime_features_latest`)  
  - `floating_pop_korean`, `floating_pop_korean_base_date`, `floating_pop_korean_base_hour`, `floating_pop_korean_observed_at`, `floating_pop_korean_lag_hours` 등.  
  - 조인: `floating_pop_korean_observed_at <= base_datetime`인 행 중 최신 1건(as-of) (구별 단순 latest 고정 아님).
- 학습에 넣을 때  
  - `ref.seoul_living_population_korean_district_hourly`(또는 `mart.seoul_living_population_korean_hourly_observed_at`)를 행별 `base_datetime` 기준 as-of 조인으로 파이프라인에서 별도 추가.
- 취약계층 9컬럼은 반대로 `mart.seoul_district_model_features`에 이미 포함되어 trainset 쪽으로 전달됩니다(위 표 참고).
- 해석: 내국인 proxy만 해당, 외국인 미포함, 공개 지연·lag 병행 해석. 확정형 단일 진실로 가정하지 말 것.

## 5. 공유용 설명 문구
아래 문구는 협업 채널에서 그대로 공유해도 됩니다.

```text
이번 모델링은 운영용 실시간 feature와 학습용 데이터셋을 분리한 구조로 진행합니다.

학습용 1행은 district_name + base_datetime 기준이며, 현재는 product_type='ultra_now'만 사용합니다.
즉, 어떤 시점(base_datetime)에 실제로 알고 있던 입력으로 미래 3시간 내 폭우를 예측하는 문제로 정의했습니다.

실시간 추론 입력은 mart.seoul_district_realtime_features_latest 를 사용하면 되고,
학습/검증/테스트 데이터는 mart.seoul_district_heavyrain_trainset 를 사용하면 됩니다.
아직 미래 3시간이 지나지 않은 최신 행은 mart.seoul_district_heavyrain_trainset_pending 에 따로 분리되어 있습니다.

OA-15439 floating_pop_korean* 는 realtime 뷰에만 있고 model_features·heavyrain_trainset 컬럼에는 없다.
학습에 쓰려면 별도 as-of 조인을 설계한다(본 문서 4절 OA-15439 항·README Living population).

타깃은 두 개입니다.
- target_rain_3h_mm: base_datetime 이후 3시간 누적 강수량
- target_rain_1h_mm: base_datetime 이후 1시간 누적 강수량
- target_heavy_rain_flag: 아래 중 하나라도 만족하면 1, 아니면 0
  - target_rain_1h_mm >= 20
  - lead(+1h,+2h,+3h) target_rain_1h_mm 중 하나 >= 20
  - target_rain_3h_mm >= 40
  - lead(+1h,+2h,+3h) target_rain_3h_mm 중 하나 >= 40

라벨 원천은 현재 AWS가 아니라 서울시 강우량 구단위 데이터이며,
구체적으로 mart.seoul_rainfall_district_latest 의 max_rain_10m_mm 를 3시간 창으로 합산합니다.

중요한 점은 leakage 방지입니다.
feature는 base_datetime 시점까지의 정보만 포함하고,
label은 반드시 그 이후 3시간으로 계산했습니다.
split도 랜덤 분할이 아니라 시간 기준 train/valid/test 로 나눴습니다.

종로구 AWS는 원천 부재이나, `meta.seoul_district_grid_map`에서 종로 격자 대비 Chebyshev ≤ 1인 타 구(자기 제외)의 시간 기준 최신값 평균으로 자동 보간된다. 이웃 개수·목록은 격자 메타와 동기화된다.
보간 여부는 aws_neighbor_imputed 컬럼으로 식별하며, 보간된 행은 aws_missing_flag = 0 으로 처리됩니다.

AWS는 2026 운영 구간에서 stale 할 수 있어 aws_lag_minutes 확인이 필수입니다.
HSR는 no-echo(-250) 구간이 많아서 hsr_value_numeric 자체보다 hsr_is_no_echo 플래그를 같이 해석하는 것이 좋습니다.
```

## 6. 현재 프로젝트 기준 사용 방법
### 실시간 예측
- 입력 뷰: `mart.seoul_district_realtime_features_latest`
- 용도: 구별 최신 예측 입력 1행

### 학습
- 입력 뷰: `mart.seoul_district_heavyrain_trainset`(운영 구간·강우량 라벨 계약)
- 장기·고정 split·AWS canonical 학습: §14 v5.1 (`hrain_v5_1_aws_*`)
- 권장 필터: `WHERE is_trainable = true`

예시:

```sql
SELECT *
FROM mart.seoul_district_heavyrain_trainset
WHERE is_trainable = true;
```

### pending 확인
- 입력 뷰: `mart.seoul_district_heavyrain_trainset_pending`
- 용도: 아직 미래 3시간이 지나지 않아 라벨이 확정되지 않은 최신 행 확인

## 7. split 기준
현재 구현은 시간 기준 hold-out입니다.

- `train`: `latest_labeled_base - 24h` 이전
- `valid`: `latest_labeled_base - 24h` 이상, `latest_labeled_base - 12h` 미만
- `test`: `latest_labeled_base - 12h` 이상
- `pending`: `label_ready_at` 이전

즉, 랜덤 분할이 아니라 `시간 순서`를 유지합니다.

## 8. 예외 데이터와 주의사항
### 1) 종로구 AWS 결측 → 인접 구 평균 보간 적용
- `종로구 AWS`는 적재 누락이 아니라 `원본 부재`입니다.
- `mart.seoul_district_model_features` 뷰에서 종로구의 AWS 컬럼은
  `meta.seoul_district_grid_map` 기준 종로 격자와 Chebyshev 거리 ≤ 1인 타 구들의
  시간 기준 최신값 평균으로 자동 보간됩니다(고정 9개 구 하드코딩 아님).
- 보간 적용 여부는 `aws_neighbor_imputed = true`로 식별합니다.
- `aws_missing_flag = 0` + `aws_neighbor_imputed = true`이면 "인접 구 평균으로 채워진 값"입니다.
- `aws_missing_flag = 1`은 본 구 데이터도 없고 인접 구 보간도 실패한 경우(현재 발생 없음)입니다.
- 따라서 학습 시 종로구를 전체 제외하지 않아도 됩니다.
  다만 `aws_neighbor_imputed` 컬럼을 feature 또는 보정 weight로 함께 활용하는 방식을 권장합니다.

### 2) AWS stale 문제
- 현재 2026 운영 구간에서는 AWS 이력이 `2025-12-31`까지입니다.
- 따라서 `aws_lag_minutes`가 매우 크게 나타날 수 있습니다.
- 현재 버전에서는 AWS 컬럼을 바로 핵심 feature로 쓰기보다, 제외하거나 lag 기준으로 gating하는 것이 안전합니다.
- `mart.seoul_district_model_features.aws_operational_stale_flag`: AWS as-of가 존재하고 `aws_lag_minutes > 1440`(24h)이면 `true`. 대시보드·알림에서 빠르게 걸러낼 때 사용.

### 3) HSR no-echo
- `HSR`에는 `-250` 같은 무에코 값이 존재합니다.
- 현재는 `hsr_value_numeric`와 별도로 `hsr_is_no_echo` 플래그를 유지합니다.
- 실제 모델링에서는 `hsr_is_no_echo`를 함께 쓰는 것을 권장합니다.

### 4) 하천 수위 구 커버리지
- `std.seoul_river_stage_std`에 관측소가 매핑된 구만 수위 feature가 의미 있음. 수위계가 없는 구는 `mart.seoul_district_model_features`에서 하천 컬럼이 비는 것이 정상에 가깝다.
- `river_district_has_stations`(해당 구에 std 이력 존재)와 `river_observation_present`(해당 시점 as-of 슬라이스 존재)로 원천 부재 vs 일시 공백을 구분한다.

### 5) 지연 관측치
- 서울시 강우량 관측은 약간 늦게 들어올 수 있습니다.
- 그래서 `label_ready_at = base_datetime + 3h + 20m`으로 잡았습니다.
- pending 데이터와 labeled 데이터를 혼용하지 않도록 주의해야 합니다.

## 9. 첨부된 계획서 기준 보정 포인트
첨부된 계획 방향은 전반적으로 유효하지만, 현재 프로젝트 구조에서는 아래 기준으로 해석하는 것이 적절합니다.

### 맞는 방향
- `3시간 내 폭우 발생` 예측
- `XGBoost/RandomForest/로지스틱` 비교
- `PR-AUC`, `Recall`, `Precision` 중심 평가
- 시간 기준 검증 필요

### 보정이 필요한 부분
- `DB 없이 파이썬 버퍼 저장`
  - 현재 프로젝트는 PostgreSQL이 source of truth이므로 권장하지 않습니다.
  - 실시간도 DB 뷰에서 읽는 구조로 맞추는 것이 좋습니다.
- `20~23 학습 / 24~25 검증`
  - 현재 즉시 사용 가능한 기본 trainset은 2026 운영 구간 중심입니다.
  - 2020~2025 장기 학습·고정 split은 §14 v5.1 산출물을 사용합니다.
- `0강수 행 대량 제거`
  - 시계열 데이터에서는 무작위 제거보다 먼저 `class_weight`나 split 내부 downsampling을 검토하는 것이 안전합니다.

## 10. 권장 문서 묶음 구성
아래 순서로 문서를 확인하면 전체 구조를 가장 빠르게 이해할 수 있습니다.

1. `MODELING_HANDOFF.md`
2. `README.md`
3. 샘플 CSV 3종
4. (선택) 내부에서 `sql/016`, `sql/027` 등을 열어볼 수 있으면 뷰 정의를 원문으로 확인할 수 있다. SQL을 전달하지 않는 경우 이 단계는 생략한다.

## 11. 추출 예시 SQL
아래 SQL 예시는 바로 사용 가능합니다.

### 1) 학습용 데이터셋 조회
```sql
SELECT *
FROM mart.seoul_district_heavyrain_trainset
WHERE is_trainable = true;
```

### 2) split별 학습 데이터 확인
```sql
SELECT split_type, COUNT(*) AS row_count
FROM mart.seoul_district_heavyrain_trainset
WHERE is_trainable = true
GROUP BY split_type
ORDER BY CASE split_type
             WHEN 'train' THEN 1
             WHEN 'valid' THEN 2
             WHEN 'test' THEN 3
             ELSE 4
         END;
```

### 3) 실시간 추론 입력 조회
```sql
SELECT *
FROM mart.seoul_district_realtime_features_latest
ORDER BY district_name;
```

### 4) pending 최신 행 확인
```sql
SELECT *
FROM mart.seoul_district_heavyrain_trainset_pending
ORDER BY district_name;
```

### 5) CSV 추출 예시
`psql` 환경이라면 아래처럼 CSV로 저장할 수 있습니다.

```sql
\copy (
    SELECT *
    FROM mart.seoul_district_heavyrain_trainset
    WHERE is_trainable = true
) TO 'seoul_district_heavyrain_trainset.csv' CSV HEADER;
```

## 12. 한 줄 요약
본 문서는 아래 한 줄로 요약할 수 있습니다.

`학습은 mart.seoul_district_heavyrain_trainset, 실시간 추론은 mart.seoul_district_realtime_features_latest, 라벨 미확정 최신 데이터는 mart.seoul_district_heavyrain_trainset_pending 을 사용하면 됩니다.`

장기·고정 split·AWS canonical 재현은 §14 `hrain_v5_1_aws_*`를 별도 계약으로 취급합니다.

## 13. 학습용 CSV 추출 결과

> 추출 원천: `mart.seoul_district_heavyrain_trainset`
>
> 저장 경로: `data/trainset/`
>
> 추출 조건: `is_trainable = true`, `dataset_status = 'labeled'`

이 프로젝트의 학습용 CSV는 DB 기준으로 재생성 가능한 스냅샷입니다.
라벨 기준이 바뀌면 과거에 만들어 둔 `data/trainset/*.csv`는 구버전 스냅샷이 될 수 있으므로, 최신 기준이 필요하면 아래 스크립트로 재추출하세요.

```bash
./scripts/export_trainset.sh
```

### 각 파일의 의미

- train: 시간 기준 hold-out의 학습 구간. `latest_labeled_base - 24h` 이전의 라벨 확정 행.
- valid: 학습/테스트 중간 구간. `latest_labeled_base - 24h` 이상, `latest_labeled_base - 12h` 미만.
- test: 가장 최신 구간. `latest_labeled_base - 12h` 이상의 라벨 확정 행. 최종 성능 평가용.

이 세 파일은 모두 `dataset_status = 'labeled'`인 과거 라벨 확정 스냅샷이며, 실시간 데이터 또는 pending 데이터와는 완전히 분리되어 있다.

### 사용한 SQL

```sql
-- train
SELECT *
FROM mart.seoul_district_heavyrain_trainset
WHERE split_type = 'train'
  AND is_trainable = true;

-- valid
SELECT *
FROM mart.seoul_district_heavyrain_trainset
WHERE split_type = 'valid'
  AND is_trainable = true;

-- test
SELECT *
FROM mart.seoul_district_heavyrain_trainset
WHERE split_type = 'test'
  AND is_trainable = true;
```

### realtime / pending CSV와의 차이

| 구분 | 이번 추출 CSV | realtime | pending |
| --- | --- | --- | --- |
| 원천 뷰 | `mart.seoul_district_heavyrain_trainset` | `mart.seoul_district_realtime_features_latest` | `mart.seoul_district_heavyrain_trainset_pending` |
| 라벨 확정 여부 | 확정 (`dataset_status = 'labeled'`) | 없음 (라벨 없음) | 미확정 (`dataset_status = 'pending'`) |
| 시간 기준 | 과거 시점 | 현재 최신 시점 | 현재 최신 시점 |
| 학습 사용 가능 | O | X | X (향후 편입 후보) |

### 검증 결과

- `trainset(is_trainable=true) ∩ pending` 중복 행: 0건
- `trainset(is_trainable=true) ∩ realtime_latest` 중복 행: 0건
- 전체 추출 행의 `dataset_status`: `labeled` 100%
- split 고유값: train 파일에는 `train`만, valid 파일에는 `valid`만, test 파일에는 `test`만 포함

### 주의사항

- AWS는 현재 2026 운영 구간에서 stale 가능 (`aws_lag_minutes` 확인 필수)
- 종로구 AWS는 원천 부재 → `aws_missing_flag` 컬럼 기준으로 처리
- HSR는 no-echo(`-250`) 값이 많음 → `hsr_is_no_echo` 플래그 병용 권장

## 14. v5.1 최종 장기 학습셋 안내

§4에서 구분한 대로, 본 절은 장기 학습용 canonical(`hrain_v5_1_aws_*`)만 다룹니다. 앞선 `heavyrain_trainset`·§13 CSV는 운영 구간 이해용 기본 trainset 계약입니다.

### 14-1. 한 줄 요약

`장기 모델 학습은 hrain_v5_1_aws_* 테이블/CSV를 쓰고, 운영 추론은 hrain_v5_1_aws_inference_* view를 쓰면 됩니다.`

### 14-2. 이 버전이 필요한 이유

- `train/valid/test`가 각각 `2020~2023 / 2024 / 2025` 전체 기간을 커버합니다.
- split 간 district universe가 동일한 24개 구로 고정됩니다(본 v5.1 버전 한정; 운영·`model_features`는 25구).
- `feature-only / label / audit` export가 분리되어 있습니다.
- feature-only와 label은 `(district_name, base_datetime)` 기준 `1:1` 정합입니다.
- 학습용 preprocessing과 운영 추론용 preprocessing이 동일 SQL 규칙으로 제공됩니다.

### 14-3. 최종 정책

- 라벨 기준: `1h >= 20mm OR 3h >= 40mm`
- 라벨 원천: `std.seoul_aws_district_hourly`
- 대상 구: 24개 구(v5.1 한정)
  - `종로구` 제외
- split:
  - `train`: `2020-01-01 00:00:00+09 ~ 2023-12-31 23:00:00+09`
  - `valid`: `2024-01-01 00:00:00+09 ~ 2024-12-31 23:00:00+09`
  - `test`: `2025-01-01 00:00:00+09 ~ 2025-12-31 20:00:00+09`

### 14-4. preprocessing 규칙

학습과 추론에서 아래 규칙을 동일하게 사용합니다.

- `precip_mm`
  - 원시 AWS 강수(`precip_mm_observed`)가 `NULL`이면 `0.0`
- `humidity_pct`
  - 구별 시계열 기준 `LOCF`
  - LOCF조차 불가능하면 `65.0`
- 파생 컬럼
  - `dew_point_c`
  - `past_rain_3h_mm`
  - `temp_change_3h_c`
  - `humidity_change_3h_pct`
  - `moist_energy`
- readiness
  - 위 feature들이 모두 계산 가능한 행만 `is_model_input_ready = true`

### 14-5. 사용해야 할 테이블 / 뷰

학습용 snapshot / split 테이블

- `mart.hrain_v5_1_aws_snapshot_20260402`
- `mart.hrain_v5_1_aws_train_audit_20260402`
- `mart.hrain_v5_1_aws_valid_audit_20260402`
- `mart.hrain_v5_1_aws_test_audit_20260402`
- `mart.hrain_v5_1_aws_train_features_20260402`
- `mart.hrain_v5_1_aws_valid_features_20260402`
- `mart.hrain_v5_1_aws_test_features_20260402`
- `mart.hrain_v5_1_aws_train_labels_20260402`
- `mart.hrain_v5_1_aws_valid_labels_20260402`
- `mart.hrain_v5_1_aws_test_labels_20260402`

운영 추론용 view

- `mart.hrain_v5_1_aws_inference_audit_latest_20260402`
- `mart.hrain_v5_1_aws_inference_features_latest_20260402`
- `mart.hrain_v5_1_aws_inference_model_input_latest_20260402`

최종 모델 입력용 가공 테이블

- `mart.hrain_v5_1_aws_train_model_input_20260402`
- `mart.hrain_v5_1_aws_valid_model_input_20260402`
- `mart.hrain_v5_1_aws_test_model_input_20260402`

### 14-6. CSV 산출물

저장 경로: `data/trainset/`

feature-only

- `seoul_train_features_only_v5_1_aws_20260402.csv`
- `seoul_valid_features_only_v5_1_aws_20260402.csv`
- `seoul_test_features_only_v5_1_aws_20260402.csv`

컬럼:

- `district_name`
- `base_datetime`
- `temp_c`
- `precip_mm`
- `humidity_pct`
- `dew_point_c`
- `past_rain_3h_mm`
- `temp_change_3h_c`
- `humidity_change_3h_pct`
- `moist_energy`

inference latest feature

- `seoul_inference_features_latest_v5_1_aws_20260402.csv`

feature-only와 동일 스키마이며, 각 구 최신 1행만 담습니다.

label

- `seoul_train_labels_v5_1_aws_20260402.csv`
- `seoul_valid_labels_v5_1_aws_20260402.csv`
- `seoul_test_labels_v5_1_aws_20260402.csv`

컬럼:

- `district_name`
- `base_datetime`
- `label`

audit

- `seoul_train_audit_v5_1_aws_20260402.csv`
- `seoul_valid_audit_v5_1_aws_20260402.csv`
- `seoul_test_audit_v5_1_aws_20260402.csv`

audit에는 다음이 추가로 들어갑니다.

- 원시 관측값 / 대체값
  - `precip_mm_observed`, `precip_mm_eff`, `precip_raw_was_null`
  - `humidity_pct_observed`, `humidity_locf_raw`, `humidity_imputed_pct`
  - `humidity_used_default_prior`, `humidity_raw_was_null`
- 라벨 메타
  - `label_window_end`, `label_ready_at`, `label_source_point_count`
  - `target_rain_1h_mm`, `target_rain_3h_mm`
- provenance
  - `label_source_name`, `label_rule_name`, `preprocessing_rule_name`, `data_version`

### 14-7. 모델 입력 스키마 권장안

join key

- `district_name`
- `base_datetime`

label

- `label`

raw feature로 직접 넣지 않는 컬럼

- `district_name`
- `base_datetime`

대신 권장하는 최종 모델 입력

- `district_id`
- `base_hour`
- `base_month`
- `day_of_week`
- `is_monsoon_season_flag`
- `hour_sin`
- `hour_cos`
- `month_sin`
- `month_cos`
- `temp_c`
- `precip_mm`
- `humidity_pct`
- `dew_point_c`
- `past_rain_3h_mm`
- `temp_change_3h_c`
- `humidity_change_3h_pct`
- `moist_energy`

즉, 모델 학습은 가능하면 `feature-only CSV`보다 `hrain_v5_1_aws_*_model_input_20260402`를 기준으로 시작하는 편이 안전합니다.

### 14-8. 생성 / 검증 / export 스크립트

- 생성 SQL
  - `sql/021_heavyrain_modelready_aws_v5_1_final.sql`
- 진단 SQL
  - `sql/021_heavyrain_modelready_aws_v5_1_diagnostics.sql`
- 승인 게이트
  - `sql/021_heavyrain_modelready_aws_v5_1_validation_gates.sql`
- export 스크립트
  - `scripts/export_seoul_district_heavyrain_modelready_v5_1_aws.py`

실행 순서:

```bash
psql -h localhost -U postgres -d weather -f sql/021_heavyrain_modelready_aws_v5_1_final.sql
psql -h localhost -U postgres -d weather -f sql/021_heavyrain_modelready_aws_v5_1_validation_gates.sql
PYTHONPATH=. python scripts/export_seoul_district_heavyrain_modelready_v5_1_aws.py
```

### 14-9. 승인 상태

v5.1은 아래 조건을 기준으로 최종 승인되었습니다.

- 전체 기간 커버
- split 간 district universe 일치
- 종로구 제외(v5.1 장기 학습셋 범위에서만; 운영 DB 25구와 혼동 금지)
- 라벨 기준 `20/40` 고정
- positive label 존재
- feature-only leakage 없음
- feature-label `1:1` 정합
- drop row 비율 통제 가능
- train/serve preprocessing consistency 보장

모델링 담당자는 특별한 이유가 없다면 장기 학습은 v5.1 기준으로 시작하면 됩니다.
