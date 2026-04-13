# 서울시 단기 폭우 예측 데이터 수집 프로젝트

서울시 `구 단위` 단기 폭우 예측 모델 구축을 위한 데이터 수집/적재 프로젝트입니다.

현재 기준으로 아래 데이터를 PostgreSQL/PostGIS에 적재하고 있습니다.

- `기상청 초단기실황`
- `기상청 초단기예보`
- `기상청 단기예보`
- `서울시 강우량 정보`
- `서울시 하천 수위 현황`
- `서울시 강우량계 위치데이터`
- `서울시 방재기상관측(AWS) 지역구별 데이터 (2020~2025)`
- `연도별 침수흔적도`
- `서울시 자연재해위험개선지구(침수지구) 현황`
- `서울시 건설공사 추진 현황` ([열린데이터광장 OA-2540 안내 페이지](https://data.seoul.go.kr/dataList/OA-2540/S/1/datasetView.do), 실제 OpenAPI 서비스명 `ListOnePMISBizInfo`)
- 서울시 자치구 단위 내국인 생활인구 proxy ([열린데이터광장 OA-15439 안내 페이지](https://data.seoul.go.kr/dataList/OA-15439/S/1/datasetView.do), 실제 OpenAPI 서비스명 `SPOP_LOCAL_RESD_JACHI`) — 외국인(장기·단기) 미포함, 공개 지연이 있는 as-of reference 용도
- 서울 자치구별 총종사자수 (사업체·종사자수 통계 CSV 수동 적재, 총종사자수 지표만)
- `HSR(레이더강수량) 행정구역별 조회`

참고: README의 `OA-15439`, `OA-2540` 링크는 모두 열린데이터광장 데이터셋 안내 페이지를 가리킵니다. 실제 수집기 호출 단위는 각각 OpenAPI 서비스명 `SPOP_LOCAL_RESD_JACHI`, `ListOnePMISBizInfo`를 기준으로 해석하면 됩니다.

## 1. 데이터 개요
| 데이터 | 성격 | 업데이트 유형 | 저장 위치 |
| --- | --- | --- | --- |
| KMA 초단기실황 | 실황 관측 | 실시간성, 10분 단위 | `raw/std/mart` |
| KMA 초단기예보 | 초단기 예측 | 실시간성, 10분 단위 발표 | `raw/std/mart` |
| KMA 단기예보 | 단기 예측 | 실시간성, 발표 주기 기반 | `raw/std/mart` |
| 서울시 강우량 정보 | 강우계 관측 | 실시간성, 10분 단위 | `raw/std/mart` |
| 서울시 하천 수위 현황 | 수위계 관측 | 실시간성, 10분 단위 | `raw/std/mart` |
| HSR(레이더강수량) 행정구역별 조회 | 레이더 구 단위 관측값 | 실시간성, 5~10분 단위 | `raw/std/mart` |
| 서울시 강우량계 위치데이터 | 관측소 위치/이력 | 정적/준정적 | `raw/ref` |
| 서울시 방재기상관측(AWS) 지역구별 데이터 | 지역구별 시간단위 과거 관측 | 비실시간, 2020~2025 이력 | `raw/std/mart` |
| 연도별 침수흔적도 | 침수 이력 공간데이터 | 비실시간, 연도별 | `raw/ref` |
| 자연재해위험개선지구 | 위험지구 속성데이터 | 비실시간, 수동 갱신형 | `raw/ref` |
| 서울시 건설공사 추진 현황 | 시설·일반공사 사업 속성(구·시공·발주·준공 등) | 비실시간, 원천 일 1회 갱신 | `raw/ref` |
| 서울시 자치구 단위 내국인 생활인구 proxy (OA-15439) | 포털 시계열(자치구×시간대), 내국인 지표만 | 비실시간, 공개 지연·일 단위 갱신 | `ref/mart` |
| 서울 자치구별 총종사자수 (사업체현황 CSV) | 자치구 단위 총종사자수만 (산업·성별 등 분해 없음) | 비실시간, 파일 교체 후 `ingest` 수동 실행 | `ref/mart` |

## 2. DB 구조
이 프로젝트는 아래 레이어로 데이터를 관리합니다.

- `raw`: API 원문 또는 파일 원문 적재
- `std`: 컬럼 정규화 후 관측소/격자 단위 저장
- `mart`: 구 단위 집계 결과
- `ref`: 참조/공간 데이터
- `meta`: 구-격자 매핑 등 메타데이터

주요 테이블/뷰:

- `raw.kma_ultra_now_raw`
- `std.kma_ultra_now_std`
- `mart.seoul_district_ultra_now`
- `raw.kma_ultra_fcst_raw`
- `std.kma_ultra_fcst_std`
- `mart.seoul_district_ultra_fcst`
- `raw.kma_short_fcst_raw`
- `std.kma_short_fcst_std`
- `mart.seoul_district_short_fcst`
- `raw.seoul_rainfall_raw`
- `std.seoul_rainfall_std`
- `mart.seoul_rainfall_district_latest`
- `raw.seoul_river_stage_raw`
- `std.seoul_river_stage_std`
- `mart.seoul_river_stage_district_latest`
- `raw.kma_hsr_area_raw`
- `std.kma_hsr_area_district_std`
- `mart.kma_hsr_area_district_latest`
- `raw.seoul_aws_district_raw`
- `std.seoul_aws_district_hourly`
- `mart.seoul_aws_district_timeline`
- `mart.seoul_aws_district_coverage`
- `ref.seoul_rain_gauge_station_current`
- `ref.seoul_flood_trace`
- `ref.seoul_disaster_risk_zone`
- `raw.seoul_construction_progress_raw`
- `ref.seoul_construction_progress`
- `ref.seoul_construction_progress_summary`
- `ref.seoul_living_population_korean_district_hourly`
- `mart.seoul_living_population_korean_district_latest`
- `ref.seoul_district_worker_stats`
- `mart.seoul_district_worker_features`
- `ref.seoul_vulnerable_population_district_snapshot`
- `mart.seoul_vulnerable_population_district_latest`
- `mart.seoul_district_realtime_features_latest` (`floating_pop_korean` 및 아래 보조 컬럼 — 내국인 생활인구 proxy 조인)
- `mart.seoul_district_weather_timeline`
- `mart.seoul_district_flood_features`
- `mart.seoul_district_model_features`

## 3. 주요 파일 구조
- `collectors/`: 실시간 API 수집기
- `core/`: 공통 설정, DB, API 클라이언트, 파서
- `ingest/`: 파일 기반 적재 스크립트
- `sql/`: 스키마/뷰 생성 SQL (`sql/028_operational_reliability.sql`: 외부 소스 상태 뷰 통합·mart 인덱스; trainset 성능은 `sql/016_seoul_district_heavyrain_datasets.sql` 최신본)
- `data/`: 구-격자 매핑 CSV

### `data/seoul_district_grids.csv` (단일 기준)

서울 25개 자치구 각각에 대해 대표 행정동·위경도·KMA 격자 `(nx, ny)` 한 줄씩을 둔다.  
소스 태그는 `representative_dong_kma_grid_v1`이며, 기존 `seoul_municipalities_geo_simple_centroid` 단일 중심점 방식은 폐기하고 이 파일이 수집·집계·포털 백필 시 선택할 동 이름의 기준이 된다.

- 컬럼: `district_name`, `representative_dong`, `nx`, `ny`, `weight`, `centroid_lat`, `centroid_lon`, `source`
- 동일 `(nx, ny)`를 쓰는 구가 여럿이어도 행은 구당 1행 유지 (예: 종로구·중구·성북구가 모두 `60_127`인 경우, 포털 CSV는 동일 격자이므로 파일 세트는 공유 가능).
- DB `meta.seoul_district_grid_map`과 맞출 때: `sql/017_seoul_district_grid_map_resync.sql` 실행 또는 동일 내용으로 UPSERT.

```bash
psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -f sql/017_seoul_district_grid_map_resync.sql
```

격자 변경 후에는 수집기가 요청하는 `target_grids`가 새 CSV에서 유도되므로, 과거 `std`에 쌓인 격자와 시계열이 끊길 수 있다. 백필·재적재 시 기간을 명시하는 것이 좋다.
- `launchd/`: macOS 자동수집 스케줄 설정

## 4. 환경 변수
`.env`에 최소 아래 값이 필요합니다.

```env
KMA_SERVICE_KEY=
KMA_BASE_URL=https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0

SEOUL_RAINFALL_API_KEY=
SEOUL_RIVER_API_KEY=
HSR_API_AUTH_KEY=
HSR_AREA_COMP_TYPE=CPP
HSR_AREA_DATA_TYPE_CD=CZ

# 선택: 서울시 건설공사 추진 현황(ListOnePMISBizInfo) 수집기용
SEOUL_CONSTRUCTION_API_KEY=

# 선택: OA-15439 내국인 생활인구 proxy 수집기용 (SEOUL_OPEN_API_KEY)
SEOUL_OPEN_API_KEY=

DB_HOST=localhost
DB_PORT=5432
DB_NAME=weather
DB_USER=postgres
DB_PASSWORD=postgres
```

기본 운영값은 `HSR_AREA_COMP_TYPE=CPP`, `HSR_AREA_DATA_TYPE_CD=CZ`입니다.

## 5. 주요 컬럼 설명
테이블과 뷰의 컬럼명이 대부분 영문이므로, 자주 보는 컬럼은 아래처럼 해석하면 됩니다.

### 공통 시간 컬럼
| 컬럼명 | 의미 |
| --- | --- |
| `requested_at` | 수집기가 API를 호출한 시각 |
| `observed_at` | 실제 관측 시각 |
| `base_datetime` | 예보 발표 기준 시각 |
| `target_datetime` | 예보가 가리키는 실제 시각 |
| `forecast_datetime` | 예보 대상 시각 |
| `lead_minutes` | 기준 시각 대비 몇 분 뒤 예보인지 |
| `lead_hours` | 기준 시각 대비 몇 시간 뒤 예보인지 |

### 기상/강수 공통 컬럼
| 컬럼명 | 의미 |
| --- | --- |
| `precip_mm` | 강수량(mm) |
| `rain_1h_mm` | 1시간 강수량(mm) |
| `rain_10m_mm` | 10분 강수량(mm) |
| `temp_c` | 기온(섭씨) |
| `humidity_pct` | 습도(%) |
| `pop_pct` | 강수확률(%) |
| `wind_speed_ms` | 풍속(m/s) |
| `wind_dir_deg` | 풍향(도) |
| `sky_code` | 하늘상태 코드 |
| `precip_type_code` | 강수형태 코드 |

### 서울시 강우량 정보 컬럼
| 컬럼명 | 의미 |
| --- | --- |
| `station_code` | 관측소 코드 |
| `station_name` | 관측소 이름 |
| `district_code` | 자치구 코드 |
| `district_name` | 자치구 이름 |
| `avg_rain_10m_mm` | 구 평균 10분 강수량 |
| `max_rain_10m_mm` | 구 최대 10분 강수량 |
| `station_count` | 해당 구에 포함된 관측소 수 |

### 서울시 하천 수위 컬럼
| 컬럼명 | 의미 |
| --- | --- |
| `river_name` | 하천명 |
| `water_level_m` | 현재 수위(m) |
| `embankment_height_m` | 제방고(m) |
| `plan_flood_level_m` | 계획홍수위 또는 계획수위(m) |
| `riverbed_height_m` | 하상고(m) |
| `control_level_m` | 통제수위(m) |
| `avg_water_level_m` | 구 평균 수위 |
| `max_water_level_m` | 구 최대 수위 |
| `max_control_level_m` | 구 내 최대 통제수위 |

### HSR 레이더강수량 컬럼
| 컬럼명 | 의미 |
| --- | --- |
| `district_code` | 자치구 행정코드 |
| `district_name` | 자치구 이름 |
| `comp_type` | 레이더 합성 방식 |
| `data_type_cd` | 조회 변수 코드 |
| `lon` | 구 대표 좌표 경도 |
| `lat` | 구 대표 좌표 위도 |
| `unit` | 단위 |
| `value_numeric` | 레이더 값 숫자형 |
| `raw_value_text` | 원문 값 |
| `is_no_echo` | `-250` 등 무에코 값 여부 |
| `hsr_observed_at` | 모델 feature에 붙은 최신 HSR 기준 시각 |
| `hsr_lag_minutes` | 모델 feature 기준시각과 HSR 시각 차이(분) |
| `hsr_value_numeric` | 모델 feature에 붙은 HSR 값 |
| `hsr_is_no_echo` | 모델 feature에 붙은 무에코 여부 |

### 모델 뷰 하천·AWS 해석 보조 컬럼 (`mart.seoul_district_model_features`)
| 컬럼명 | 의미 |
| --- | --- |
| `river_district_has_stations` | `std.seoul_river_stage_std`에 해당 구 관측 이력이 있으면 `true`. 수위계가 없는 구는 영원히 false일 수 있음(원천 coverage 한계). |
| `river_observation_present` | `base_datetime` 기준 as-of로 하천 슬라이스가 붙었으면 `true`. `has_stations=true`인데 false면 일시 공백 가능. |
| `aws_neighbor_imputed` | 종로구 등 인접 구 평균 보간으로 AWS가 채워졌으면 `true`. |
| `aws_operational_stale_flag` | AWS as-of가 있고 `aws_lag_minutes > 1440`(24시간)이면 `true`. 원천 이력이 끊긴 구간에서 즉시 경고용. `NULL`이면 AWS 관측 자체 없음. |

### 공간/침수 feature 컬럼
| 컬럼명 | 의미 |
| --- | --- |
| `rain_gauge_current_count` | 현재 운영 중인 강우계 수 |
| `flood_trace_count_2023` | 2023년 침수흔적도 건수 |
| `flood_trace_count_2024` | 2024년 침수흔적도 건수 |
| `flood_trace_count_2025` | 2025년 침수흔적도 건수 |
| `flood_trace_count_total` | 전체 침수흔적도 건수 합계 |
| `flooded_area_sqm_2023` | 2023년 침수면적 합계(㎡) |
| `flooded_area_sqm_2024` | 2024년 침수면적 합계(㎡) |
| `flooded_area_sqm_2025` | 2025년 침수면적 합계(㎡) |
| `flooded_area_sqm_total` | 전체 침수면적 합계(㎡) |
| `disaster_risk_zone_count` | 자연재해위험개선지구 수 |
| `disaster_risk_zone_in_progress_count` | 추진중인 위험개선지구 수 |
| `disaster_risk_zone_expired_count` | 고시실효 위험개선지구 수 |

### AWS 지역구별 과거관측 컬럼
| 컬럼명 | 의미 |
| --- | --- |
| `station_code` | AWS 지점 코드 |
| `observed_at` | 시간단위 관측 시각 |
| `temp_c` | 기온(섭씨) |
| `wind_dir_deg` | 풍향(도) |
| `wind_speed_ms` | 풍속(m/s) |
| `precip_mm` | 시간 강수량(mm) |
| `local_pressure_hpa` | 현지기압(hPa) |
| `sea_level_pressure_hpa` | 해면기압(hPa) |
| `humidity_pct` | 습도(%) |
| `solar_radiation_mj_m2` | 일사량(MJ/m^2) |
| `sunshine_hr` | 일조시간(hr) |
| `aws_observed_at` | 모델 feature에 붙은 최신 AWS 관측 시각 |
| `aws_precip_mm` | 모델 feature에 붙은 AWS 시간 강수량 |
| `aws_temp_c` | 모델 feature에 붙은 AWS 기온 |
| `aws_humidity_pct` | 모델 feature에 붙은 AWS 습도 |
| `aws_missing_flag` | AWS 데이터가 없으면 `1`, 있으면 `0` |

해석 주의: `ref.seoul_flood_trace`는 연도·레이어에 따라 25개 구 전부에 피처가 없을 수 있음(예: 특정 구는 원천에 레코드가 없음). `mart.seoul_district_flood_features`는 25구를 한 행으로 유지하며 누락 구는 집계값 `0`으로 채울 수 있어, 0이 “침수 없음”인지 “원천 미포함”인지 `ref` distinct 구 목록과 함께 본다. 자연재해위험개선지구(`ref.seoul_disaster_risk_zone`)도 일부 구에만 존재할 수 있으며, mart에서는 나머지 구가 0-fill일 수 있다.

### 코드/원문 보조 컬럼
| 컬럼명 | 의미 |
| --- | --- |
| `response_json` | API 원문 JSON |
| `row_json` | 파일 원문 행 JSON |
| `source_file_name` | 원본 파일명 |
| `source_year` | 원본 데이터 연도 |
| `geom` | PostGIS geometry 도형 |

### 서울시 건설공사 추진 현황 컬럼
원천 API 필드와의 대응은 아래와 같습니다. 적재 테이블은 `ref.seoul_construction_progress`입니다.

| 컬럼명 | 의미 |
| --- | --- |
| `biz_cd` | 사업(공사) 식별 코드. upsert·삭제 동기화의 기본 키 |
| `district_name` | 자치구명(서울 25개 구 표준명으로 정규화) |
| `contractor_name` | 시공사업체명(원천 `CNST_ENT`) |
| `ordering_agency_name` | 발주처기관명(원천 `INST_NM`) |
| `project_name` | 사업명(원천 `BIZ_NM`) |
| `completion_status` | 준공여부 요약(원천 `CMCN_YN2`·`CMCN_YN1` 기반, 예: `진행`, `준공`) |
| `raw_gu_cd` / `raw_gu_name` | 원천 자치구 코드·명(`GU_CD`, `GU_NM`) |
| `row_json` | API 행 전체(JSON) |
| `requested_at` | 해당 행이 반영된 수집 실행 시각 |

## 6. 수동 실행 예시
프로젝트 루트에서 실행합니다.

```bash
PYTHONPATH=. python collectors/ultra_now.py
PYTHONPATH=. python collectors/ultra_fcst.py
PYTHONPATH=. python collectors/short_fcst.py
PYTHONPATH=. python collectors/seoul_rainfall.py
PYTHONPATH=. python collectors/seoul_river_stage.py
PYTHONPATH=. python collectors/hsr_district.py
export SEOUL_CONSTRUCTION_API_KEY="<서울_Open_API_인증키>"
PYTHONPATH=. python collectors/seoul_construction_progress.py --api-key "$SEOUL_CONSTRUCTION_API_KEY"
PYTHONPATH=. python collectors/seoul_living_population_korean_district_hourly.py --mode daily --lookback-days 14
PYTHONPATH=. python collectors/seoul_living_population_korean_district_hourly.py --mode backfill --start-date "20180801" --end-date "20180801"

PYTHONPATH=. python ingest/seoul_rain_gauge_station.py
PYTHONPATH=. python ingest/seoul_aws_district.py
PYTHONPATH=. python ingest/portal_ultra_now_folder_loader.py --source-dir "서울 초단기실황"
PYTHONPATH=. python ingest/seoul_flood_trace.py
PYTHONPATH=. python ingest/seoul_disaster_risk_zone.py
PYTHONPATH=. python ingest/seoul_district_worker_stats.py
PYTHONPATH=. python ingest/seoul_vulnerable_population_district.py --zip "취약계층 밀집도 데이터.zip"
```

#### 서울 자치구별 취약계층 밀집도 (ZIP)

개요  
서울 25개 자치구의 취약계층 밀집도 관련 지표를 ZIP 파일에서 파싱하여 `ref.seoul_vulnerable_population_district_snapshot`에 적재한다. 이 데이터는 준정적(slow-changing) 참조 데이터로, `vulnerability_score` 입력 feature로 사용된다.

입력 파일 (ZIP 내 4개 CSV)  

| 파일명 | 헤더 구조 | 기준 시점 | 추출 컬럼 |
| --- | --- | --- | --- |
| `고령자현황_*.csv` | 4행 다중 헤더 | 2025년 4분기 | `total_population`, `elderly_population_total`, `elderly_population_korean_total`, `elderly_population_foreign_total` |
| `장애인+현황(장애유형별_동별)_*.csv` | 4행 다중 헤더 | 2024년 | `disabled_population_total`, `disabled_population_male`, `disabled_population_female` |
| `국민기초생활보장+수급자(2020+이후)_*.csv` | 4행 다중 헤더 | 2024년 | `basic_livelihood_recipient_total`, `basic_livelihood_household_count` |
| `자치구별_지하반지하주택_정리.csv` | 단순 헤더 1행 | 수집일 2026-04-03 (원천 날짜 미표기) | `basement_household_count`, `aged_basement_household_count`, `aged_basement_household_ratio` |

비율(ratio) 계산  
- 모든 비율은 소수(0.0~1.0) 로 저장한다.  
- `elderly_population_ratio` = `elderly_population_total` / `total_population` (동일 소스, 2025 Q4)  
- `disabled_population_ratio` = `disabled_population_total` / `total_population` (분모=고령자현황 2025 Q4, 분자 소스는 2024 — 소스 시점 상이)  
- `basic_livelihood_recipient_ratio` = `basic_livelihood_recipient_total` / `total_population` (분모=고령자현황 2025 Q4, 분자 소스는 2024 — 소스 시점 상이)  
- `aged_basement_household_ratio` = 원본 CSV 「노후 비율(%)」을 `/100` 한 값(0.0~1.0). 이론상 `aged_basement_household_count / basement_household_count`와 같아야 하나 원천 반올림으로 count로 재계산한 비율과 소수점이 어긋날 수 있다.  

교차 소스·시점 혼합 시 해석  
- `disabled_population_ratio`, `basic_livelihood_recipient_ratio`는 분자·분모의 통계 기준 연도가 다르다(분자 2024, 분모 인구 2025 Q4). 구 간 순위·상대 비교에는 쓸 수 있으나, 절대 수준(예: “실제 장애인 비율”)로 단정하지 말 것.  
- `aged_basement_household_ratio` 및 지하·반지하 가구 수는 고령/장애/기초생보와 별도 출처·미표기 시점이므로, 동일 스냅샷 내 서로 직접 비율을 나누어 새 지표를 만들지 말 것(승인된 composite 규칙 전까지).  

소스 시점 분리 저장  
공통 `base_date` 하나로 뭉개지 않고 컴포넌트별 소스 시점을 별도 컬럼에 저장:  
- `elderly_source_label` (예: `'2025 4/4'`), `elderly_source_year` (2025)  
- `disabled_source_year` (2024)  
- `basic_livelihood_source_year` (2024)  
- `basement_source_note` (예: `'출처일 미표기; 수집일 2026-04-03'`)  

스키마  

| 대상 | 역할 |
| --- | --- |
| `ref.seoul_vulnerable_population_district_snapshot` | 적재본. PK `district_name`. 25개 자치구 1행씩. |
| `mart.seoul_vulnerable_population_district_latest` | 조회·조인용 view. `ref` 스냅샷 그대로 노출. |

DDL: `sql/026_seoul_vulnerable_population_tables.sql`  
mart feature 조인 업데이트: `sql/027_seoul_district_model_features_v2.sql`  

`mart.seoul_district_model_features` 갱신 방식  
- `027`은 `CREATE OR REPLACE VIEW` 로만 갱신한다. `DROP VIEW ... CASCADE`를 쓰면 `mart.seoul_district_model_features`에 달린 `mart.seoul_district_realtime_features_latest`, `mart.seoul_district_heavyrain_trainset_base` 등이 연쇄 삭제될 수 있으므로 사용하지 않는다.  
- 의존 뷰 전체를 처음부터 다시 깔 때는 `sql/016_seoul_district_heavyrain_datasets.sql` 등 기존 배포 순서를 따른다.  

실행  
```bash
set -a && source .env && set +a
psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -f sql/026_seoul_vulnerable_population_tables.sql
PYTHONPATH=. python ingest/seoul_vulnerable_population_district.py --zip "취약계층 밀집도 데이터.zip"
psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -f sql/027_seoul_district_model_features_v2.sql
```
다른 경로의 ZIP을 쓴다면: `PYTHONPATH=. python ingest/seoul_vulnerable_population_district.py --zip /path/to/취약계층\ 밀집도\ 데이터.zip`

재실행  
`district_name` PK에 대한 upsert(`ON CONFLICT DO UPDATE`)이므로 중복 없이 idempotent 하게 동작한다. 재실행 시 기존 행이 덮어쓰이고 `updated_at`이 갱신된다.

검증  
- `sql/verify_seoul_vulnerable_population.sql` — 적재본·mart latest 기본 점검  
- `sql/verify_seoul_vulnerable_population_final_audit.sql` — 구명 정합성, model_features 조인·row explosion, ratio 재계산, 의존 뷰 존재 등 최종 검수  

주요 확인 항목:  
- `ref`: 행 수 25, `district_name` distinct 25, 핵심 컬럼 NULL 0건  
- 비율 범위 0.0~1.0 이탈 0건 (DB에는 퍼센트 포인트 단위 미저장; 원본 %는 지하반지하만 적재 시 /100)  
- `mart.seoul_vulnerable_population_district_latest`: 25행  
- source year 확인 (`elderly_source_year=2025`, `disabled_source_year=2024`, `basic_livelihood_source_year=2024`)  

composite vulnerability_score 미구현 안내  
현재는 feature를 적재·노출하는 데 집중한다. `vulnerability_score` 가중합 산식은 팀 내 별도 규칙이 확정된 뒤 `sql/027` 또는 새 파일에 추가한다. 관련 설계 배경은 §21 참고.

#### 서울 자치구별 총종사자수 (CSV)

개요  
통계 CSV에서 서울 25개 자치구의 총종사자수만 추출해 최소 스키마로 적재한다. 이 값은 자치구별 전체 종사 규모를 나타내는 기초 통계이며, 야외근로자·배달 종사자 등으로 직접 해석·대체하지 않는다.

입력  
- 파일명: `사업체현황+종사자수(산업대분류별_성별_동별)_20260403163145.csv` (기본은 프로젝트 루트, `--source`로 경로 지정 가능)  
- 헤더는 3줄: 1행 연도, 2행 분류, 3행 지표.  
- 로더는 `2024` / `합계` / `총종사자수`에 해당하는 열만 골라 운영 컬럼 `total_worker_count`로 저장한다. (스프레드시트 등에서 보이는 내부 열 이름을 DB 컬럼으로 쓰지 않는다.)

적재 대상 행  
- `동별(1) = 합계` 이고 `동별(2)`가 서울 25개 자치구명인 행만.

스키마  
| 대상 | 역할 |
| --- | --- |
| `ref.seoul_district_worker_stats` | 적재본. PK `(base_year, district_name)`. 컬럼: `base_year`, `district_name`, `total_worker_count`, `source_file_name`, `loaded_at` |
| `mart.seoul_district_worker_features` | 조회용. `base_year`, `district_name`, `total_worker_count` |

DDL: `sql/025_seoul_district_worker_stats.sql`

실행  
```bash
set -a && source .env && set +a
psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -f sql/025_seoul_district_worker_stats.sql
PYTHONPATH=. python ingest/seoul_district_worker_stats.py
```
다른 파일·인코딩이면 예: `PYTHONPATH=. python ingest/seoul_district_worker_stats.py --source /path/to/file.csv --encoding utf-8-sig`

재실행  
같은 `base_year`에 대해 스크립트를 다시 실행해도, 해당 연도 행을 삭제한 뒤 다시 넣는 방식으로 중복 없이 idempotent 하게 맞춘다.

검증  
`sql/verify_seoul_district_worker_stats.sql`을 실행한다. `base_year = 2024` 기준으로 다음을 확인할 수 있다.  
- `ref`: 행 수 25, `district_name` distinct 25, `total_worker_count` NULL 0·음수 0  
- `mart.seoul_district_worker_features`: 25행  

현재 적재 범위  
이 로더는 `total_worker_count`(구별 총종사자수) 만 `ref`/`mart`에 넣는다. 통계 원본에서 산업대분류별 종사자수를 파싱해 건설·운수·사업시설관리·배달 등으로 분해 적재하거나, DB 안에서 `outdoor_worker_exposure_score` 컬럼을 자동 생성하는 일은 하지 않는다.

설계 참고(폭우·침수 대응 점수)  
구별 옥외·외근 노출을 근사하는 `outdoor_worker_exposure_score` 1차 proxy 정의(산업별 종사자·진행 공사 수 가중)는 §21.3-1에 두었다. 해당 산입 데이터 대부분은 미적재 또는 mart·점수 파이프라인 미연결 상태이고, 점수 자체는 문서상 제안(planned) 이며 운영 DB 컬럼으로는 아직 없다(§22 Next steps).

`collectors/seoul_construction_progress.py`는 [OA-2540 데이터셋 안내 페이지](https://data.seoul.go.kr/dataList/OA-2540/S/1/datasetView.do)에 대응하는 OpenAPI 서비스 `ListOnePMISBizInfo`를 페이지 단위로 모두 가져와 `raw.seoul_construction_progress_raw`에 감사 로그를 쌓고, 서울 25개 자치구로 매핑되는 행만 `ref.seoul_construction_progress`에 upsert합니다. 최신 응답에 없는 `biz_cd`는 `ref`에서 삭제되어 스냅샷과 맞춥니다. 인증키는 `--api-key`로 직접 넘기면 됩니다(수집기 기본값이 있으면 생략 가능). 최초 적재 전 `sql/022_seoul_construction_progress_tables.sql`을 실행합니다. 런타임 래퍼를 쓰는 경우 `scripts/run_collector.sh seoul_construction_progress --api-key "$SEOUL_CONSTRUCTION_API_KEY"`처럼 인자를 넘길 수 있습니다.

`collectors/seoul_living_population_korean_district_hourly.py`는 [OA-15439 데이터셋 안내 페이지](https://data.seoul.go.kr/dataList/OA-15439/S/1/datasetView.do)에 대응하는 OpenAPI 서비스 `SPOP_LOCAL_RESD_JACHI`로 서울 자치구 단위 내국인 생활인구 proxy를 적재합니다.

#### Living population (Korean-only proxy)

- 데이터 정의: OA-15439 `SPOP_LOCAL_RESD_JACHI` 기반. API 필드 → 저장 매핑: `STDR_DE_ID` → `base_date`, `TMZON_PD_SE` → `base_hour`, `ADSTRD_CODE_SE` → `district_code`(5자리), `TOT_LVPOP_CO` → `korean_population` → `mart.seoul_district_realtime_features_latest`의 `floating_pop_korean`(아래 조인 규칙 적용 후).
- 범위: 이 값은 내국인 생활인구 proxy일 뿐이며, 내국인·외국인을 합산한 규모나 “행정 통계상 전체 생활인구”를 대체하는 지표가 아닙니다. 외국인(장기체류·단기체류)은 현재 파이프라인 범위에 포함하지 않습니다.

#### 적재 대상 및 스키마

| 대상 | 역할 |
| --- | --- |
| `ref.seoul_living_population_korean_district_hourly` | 자치구×시간대 원천 정규화 테이블(PK: `base_date`, `base_hour`, `district_code`) |
| `mart.seoul_living_population_korean_district_latest` | 구별 가장 최근 슬롯 1행 요약(대시보드·점검용). realtime 피처 조인과 항상 같은 의미는 아님 |
| `mart.seoul_district_realtime_features_latest` | 초단기실황 피처 행에 지연된 참조값으로 `floating_pop_korean` 조인 |

realtime 뷰의 보조 컬럼(조인 결과 추적·lag 점검):

- `floating_pop_korean_base_date`, `floating_pop_korean_base_hour`
- `floating_pop_korean_observed_at` — `(base_date + base_hour)`를 KST로 해석한 시각
- `floating_pop_korean_lag_hours` — 위 관측 시각과 해당 행 `base_datetime`의 시차(시간)

DDL·메타: `sql/023_seoul_living_population_korean_district_tables.sql`, `sql/024_seoul_living_population_korean_operational.sql`. 디버깅용 관측시각 뷰: `mart.seoul_living_population_korean_hourly_observed_at`(024).

#### 날짜·시각 필드 의미 (`ref`)

| 컬럼 | 의미 |
| --- | --- |
| `requested_date` | 수집 잡이 요청한 날짜(`daily`의 `--target-date`, 생략 시 KST 당일 / `backfill` 루프의 해당일) |
| `source_date` | 포털 API에서 이번 적재에 사용된 기준 캘린더 일(`STDR_DE_ID`)을 행 단위로 보존한 컬럼. OA-15439 JSON에는 “별도 공개일” 필드가 없어, 현재 구현에서는 행마다 `base_date`와 동일하게 적재된다. `daily` 모드에서 lookback으로 고른 “오늘 읽을 슬라이스의 날짜”는 로그상 `resolved_stdr_calendar_date` / `load_stdr_date`로 확인 가능. |
| `base_date`, `base_hour` | 원천이 의미하는 관측·집계 기준 시점(시간 버킷). 요청일을 임의로 `base_date`에 넣지 않는다. |

#### Data latency and as-of semantics

- 이 데이터는 공개 지연이 있어, 당일 잡을 돌려도 당일 STDR 슬라이스가 비어 있으면 lookback 범위 안에서 가장 최근에 열린 기준일을 읽는다. 따라서 공개 지연이 있는 as-of reference로만 쓰는 것이 맞다.
- `floating_pop_korean`은 realtime feature에 조인되는 지연된 참조값이다. 의사결정 시점(`base_datetime`) 기준으로 이미 공개되어 이용 가능한 범위 안에서 가장 최근 proxy를 붙인 것이지, 그 시각의 실제 거리 인구를 직접 계측한 값이 아니다.
- 모델 입력(예: exposure 관련 피처)으로 쓸 때는 확정·완성형 단일 진실이 아니라, lag와 공개 주기를 함께 해석해야 한다.

#### Realtime feature join rule

- `mart.seoul_district_realtime_features_latest`의 조인은 구별 `latest` 뷰를 그대로 붙이는 방식이 아니다.
- 각 구에 대해 `ref`에서 `floating_pop_korean_observed_at`(= KST 기준 시간 버킷 시작 시각)이 해당 행의 `base_datetime` 이하인 행만 고른 뒤, 그중 가장 최근 1행을 붙인다(as-of join, 방식 C).
- 같은 시각을 강제로 맞추는 exact match(방식 B)는 아니다. 공개 지연 때문에, 조인되는 값은 종종 며칠 전·수십~수백 시간 전 슬롯일 수 있다.
- `mart.seoul_living_population_korean_district_latest`는 요약·대시보드용 latest이며, 위 realtime 조인 semantics와 완전히 동일하지 않을 수 있다.

정리하면 `floating_pop_korean*`는 현재 `mart.seoul_district_realtime_features_latest`에만 붙는 지연된 as-of reference입니다. `mart.seoul_district_model_features` 본체나 `mart.seoul_district_heavyrain_trainset*`에 자동으로 포함된다고 해석하면 안 됩니다.

학습에 이 값을 쓰려면 `district_name + base_datetime` 기준으로 누수 없는 별도 as-of join 규칙을 설계해야 합니다. 단순히 `mart.seoul_living_population_korean_district_latest`를 붙이거나, realtime 뷰에 컬럼이 있다는 이유만으로 trainset 포함을 가정하지 않습니다.

#### 실행 방법

인증키는 `SEOUL_OPEN_API_KEY` 환경변수만 사용한다(코드·문서에 실키를 넣지 말 것). 로컬은 `.env`에 두고, 키 이름 예시는 `.env.example` 을 참고한다.

```bash
set -a && source .env && set +a   # 또는 export SEOUL_OPEN_API_KEY=...
PYTHONPATH=. python collectors/seoul_living_population_korean_district_hourly.py --mode daily --lookback-days 14
PYTHONPATH=. python collectors/seoul_living_population_korean_district_hourly.py --mode daily --target-date 2026-04-04 --lookback-days 14
PYTHONPATH=. python collectors/seoul_living_population_korean_district_hourly.py --mode backfill --start-date 20180801 --end-date 20180801
PYTHONPATH=. python collectors/seoul_living_population_korean_district_hourly.py --mode backfill --start-date 20180801 --end-date 20180802 --resolve-missing-by-lookback --lookback-days 7
```

- `--lookback-days`: `daily`(및 `backfill --resolve-missing-by-lookback`)에서 최근 며칠 안에서 데이터가 있는 STDR 일자를 찾을 때 사용한다.

#### Validation

점검용 SQL 묶음: `sql/verify_seoul_living_population_korean.sql`

```bash
psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -f sql/verify_seoul_living_population_korean.sql
```

권장 확인 항목(환경·적재 시점에 따라 수치는 달라짐):

- `ref`: 기준일×24시간 적재 시 행 수 = 600(25구×24), 자치구 수 = 25, 시간대 0–23
- `mart.seoul_living_population_korean_district_latest`: 행 수 = 25, 구 코드 중복 없음
- `mart.seoul_district_realtime_features_latest`: `floating_pop_korean` NULL 비율(ref 미적재·조인 실패 시 상승 가능)
- `floating_pop_korean_lag_hours`: 값이 클 수 있음 — 운영·분석 시 반드시 함께 해석

OA-15439는 데이터셋 페이지에 명시된 이용조건(공공누리 유형 등) 을 따릅니다. 모델·서비스 반영 전 해당 조항을 확인하세요.

표준 데이터셋 메타에 따르면 공사진행정보(OA-2540 안내 페이지 기준) 등 일부 데이터는 [공공누리 4유형](https://data.seoul.go.kr/dataList/OA-2540/S/1/datasetView.do)(출처표시·상업적 이용 금지·변경 금지)입니다. 모델 학습·서비스에 쓰기 전에 라이선스를 확인하세요.

```bash
psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -f sql/022_seoul_construction_progress_tables.sql
```

`ingest/portal_ultra_now_folder_loader.py`는 포털의 `서울 초단기실황` 폴더(연도/구/대표동 별로 분리된 CSV들)를 스캔해 `std.kma_ultra_now_std`에 적재하고, 이어서 `mart.seoul_district_ultra_now`까지 집계합니다.

이 포털 CSV들은 “헤더형(컬럼명 있는 형태)”이 아니라, 파일 1개가 변수 1개 시계열을 담는 포맷입니다.
- 파일 첫 줄 예: `format: day,hour,value location:nx_ny Start : YYYYMMDD`
- 데이터 줄: `day, hour(HHMM), value`

파일명 변수 키워드 → 컬럼 매핑:
- `강수`(또는 `강수*` 중 `강수형태` 제외) → `rain_1h_mm`
- `기온` → `temp_c`
- `습도` → `humidity_pct`
- `풍속` → `wind_speed_ms`
- `풍향` → `wind_dir_deg`
- `강수형태` → `precip_type_code`

### 포털 백필: 그룹 단위·스킵·격자 분리(변수가 여러 `nx,ny`에 흩어지는 경우)

`ingest/portal_ultra_now_folder_loader.py`는 파일명과 첫 줄 헤더로 한 건을 분류합니다.

- 구 이름: 상위 폴더명에서 `…구 YYYY년 초단기실황` 형태를 파싱합니다.
- 격자·연도: 헤더의 `location:nx_ny`, `Start : YYYYMMDD`에서 `(nx, ny)`와 연도를 뽑습니다.
- 그룹 키: `(district_name, nx, ny, 연도)` 단위로 묶습니다. 같은 구·같은 연도라도 헤더 격자가 다르멀로 별도 그룹입니다.
- 한글 파일명: macOS 등에서 파일명 한글이 NFD로 들어올 수 있어, 변수명 매핑 전 NFC 정규화를 합니다.

한 그룹 안에서 아래 6개 슬롯이 모두 있어야 `std.kma_ultra_now_std`에 upsert하고 `mart.seoul_district_ultra_now`까지 집계합니다. 하나라도 없으면 해당 그룹은 스킵하고 로그에 `missing=[...]`가 찍힙니다.

- `rain`, `temp`, `humidity`, `wind_speed`, `wind_dir`, `precip_type`

“원본에 파일이 있는데 스킵된다”처럼 보이는 대표 원인은, 사용자가 기대한 “구·연도당 한 세트”가 아니라 변수별로 헤더 `location` 격자가 갈라진 경우입니다. 이 경우 다른 격자 그룹에는 해당 변수 파일이 0개가 맞고, 현재 로더 정책상 스킵이 됩니다.

구체적인 사례(로컬 데이터 기준):

| 구·연도 | 스킵 로그에 나온 격자 | 실제로 비어 있는 슬롯 | 같은 구·연도 안 다른 격자에만 있는 변수(요약) |
| --- | --- | --- | --- |
| 관악구 2024 | (59,125) | `wind_speed`, `wind_dir` | (97,74)에는 풍속·풍향만 있고, 강수·기온·습도·강수형태는 없음 |
| 관악구 2024 | (97,74) | `rain`, `temp`, `humidity`, `precip_type` | (59,125)에는 위 변수만 있고 풍속·풍향 파일 없음 |
| 서대문구 2025 | (55,126) | 비어 있음(6개 중 5개) | `강수형태`만 이 격자에 있음 |
| 서대문구 2025 | (59,127) | `precip_type` | 나머지 5변수는 이 격자, `강수형태`만 (55,126) |

정책 선택(문서화용):

- A안(현재 구현): `(district_name, nx, ny, 연도)`마다 6슬롯 완비된 경우만 적재. 격자가 쪼개진 원본에서는 일부 구간이 스킵될 수 있음.
- B안(미구현): 같은 `district_name + 연도` 안에서 서로 다른 `(nx,ny)`에 흩어진 슬롯을 병합한 뒤, 대표 격자(예: `data/seoul_district_grids.csv`의 `nx,ny`)에 맞춰 한 행으로 적재. 스킵은 줄지만, 물리적으로 다른 격자 값을 한 행에 합치는 해석이 필요하므로 모델·검증 규칙에 명시할 것.

실행 시 `PYTHONPATH=.`를 함께 두는 것을 권장합니다(프로젝트 루트가 `sys.path`에 잡혀야 `core` 모듈을 읽습니다).

적재 검증(예시 SQL):

```sql
SELECT MIN(base_datetime), MAX(base_datetime), COUNT(*)
FROM std.kma_ultra_now_std;

SELECT MIN(base_datetime), MAX(base_datetime), COUNT(*)
FROM mart.seoul_district_ultra_now;
```

## 7. 자동수집
현재 자동수집은 macOS `launchd` 기준입니다.

- `com.jaemin.kma.ultra_now.plist`
- `com.jaemin.kma.ultra_fcst.plist`
- `com.jaemin.kma.short_fcst.plist`
- `com.jaemin.kma.seoul_rainfall.plist`
- `com.jaemin.kma.seoul_river_stage.plist`
- `com.jaemin.kma.hsr_district.plist`

현재 등록 완료된 자동수집 작업:

- `com.jaemin.kma.ultra_now`
- `com.jaemin.kma.ultra_fcst`
- `com.jaemin.kma.short_fcst`
- `com.jaemin.kma.seoul_rainfall`
- `com.jaemin.kma.seoul_river_stage`
- `com.jaemin.kma.hsr_district`

현재 `HSR`은 `08, 18, 28, 38, 48, 58분`에 자동수집되며 로그는 런타임 `logs/hsr_district.log`에 생성됩니다.
`서울시 강우량`, `서울시 하천 수위`, `HSR`는 자동수집이 실제 등록되어 있습니다.
`서울시 건설공사 추진 현황`은 현재 `launchd`에 등록되어 있지 않으며, 필요 시 수동 실행 또는 `scripts/run_collector.sh`로 돌립니다.

주의:

- 현재 자동수집은 로컬 macOS 경로에 의존합니다.
- 팀 공유 시에는 우선 `수동 실행 기준`으로 맞추고, 이후 공통 실행환경을 따로 정리하는 것이 안전합니다.
- `requested_at`와 `observed_at`는 다를 수 있습니다.
  - `requested_at`: 수집기가 API를 호출한 시각
  - `observed_at`: 기관 API가 제공한 실제 관측 시각
  - 서울시 실시간 API는 최신 관측이 수집 시각보다 몇 분 늦게 들어오는 경우가 정상적으로 발생할 수 있습니다.

## 8. 예시 스냅샷과 검증 기준
아래 값은 특정 시점에 확인한 예시 스냅샷입니다. 최신 행 수·최신 시각은 시간이 지나면 바뀌므로, 운영 상태 판단은 이 절의 고정 숫자보다 §9 기본 확인 SQL과 각 검증 SQL을 우선 기준으로 삼습니다.

### KMA 적재 상태
- `ultra_now raw`: `10288`
- `ultra_now std`: `362`
- `ultra_now mart`: `450`
- `ultra_fcst raw`: `45600`
- `ultra_fcst std`: `1932`
- `ultra_fcst mart`: `2406`
- `short_fcst raw`: `167660`
- `short_fcst std`: `10500`
- `short_fcst mart`: `13125`

### 서울시/참조 데이터 적재 상태
- `서울시 강우량 std`: `47`행, 최신 수집시각 `2026-03-24 16:11+09`, 최신 관측시각 `2026-03-24 15:59+09`
- `서울시 하천 수위 std`: `21`행, 최신 수집시각 `2026-03-24 16:10+09`, 최신 관측시각 `2026-03-24 16:06+09`
- `HSR 구단위 std`: `50`행, 최신 수집시각 `2026-03-26 16:32+09`, 최신 기준시각 `2026-03-26 16:10+09`
- `서울시 AWS 지역구별 std`: `1,257,671`행, `2020-01-01 00:00+09 ~ 2025-12-31 23:00+09` 범위. AWS 원천 적재본만 `24개 구`이며 `종로구` 원본은 없음
- `서울시 AWS 종로구`: 원본 부재로 `0행`, 다만 운영 `mart`/서빙 관점의 district universe는 25개 구를 유지하고 종로구 AWS 값은 뷰에서 인접 구 평균 보간으로 처리
- `강우량계 현재 관측소`: `29`개
- `침수흔적도`: `1536`개 (`2023=278`, `2024=121`, `2025=1137`)
- `자연재해위험개선지구`: `5`행
- `서울시 건설공사 추진 현황`: `ref.seoul_construction_progress`는 서울 25개 구 행만 유지(원천에 `서울지역외` 등 비서울 공사 포함). 실행마다 전체 건수·필터·적재·제외 건수와 제외 사유는 수집기 표준 출력 로그에 남습니다. `raw`는 실행마다 누적됩니다.
- `서울 자치구별 총종사자수`: `ref.seoul_district_worker_stats`에서 `base_year=2024` 기준 `25`행, `district_name` distinct `25`, `mart.seoul_district_worker_features` `25`행 (`sql/verify_seoul_district_worker_stats.sql`로 동일 점검 가능)
- `서울 자치구별 취약계층 밀집도`: `ref.seoul_vulnerable_population_district_snapshot` `25`행, `mart.seoul_vulnerable_population_district_latest` `25`행. 고령자 소스 2025 Q4, 장애인·기초생보 소스 2024, 지하반지하 수집일 2026-04-03. (`sql/verify_seoul_vulnerable_population.sql`로 점검)
- `모델 feature view`: `25개 구 기준 지속 갱신 중`

## 9. 기본 확인 SQL
### 전체 상태 확인
```sql
SELECT *
FROM mart.kma_collection_status
ORDER BY product_type, data_layer;

SELECT *
FROM mart.external_source_collection_status
ORDER BY source_name;
```

`mart.external_source_collection_status`에는 강우·하천·HSR(요청/파일인벤토리/구단위 area raw·std), 건설공사 raw/ref, 내국인 생활인구 `ref` 시계열 등이 포함됩니다. 구단위 HSR 적재 여부는 `kma_hsr_area_district_std` 행을 보면 됩니다(`kma_hsr_file_inventory_std`만으로 판단하면 안 됨).

통합 운영 점검: `psql ... -f sql/verify_operational_health.sql`

### 서울시 실시간 API 수집시각과 관측시각 차이 확인
```sql
SELECT MAX(requested_at) AS rainfall_requested_at,
       MAX(observed_at) AS rainfall_observed_at
FROM std.seoul_rainfall_std;

SELECT MAX(requested_at) AS river_requested_at,
       MAX(observed_at) AS river_observed_at
FROM std.seoul_river_stage_std;

SELECT MAX(requested_at) AS hsr_requested_at,
       MAX(base_datetime) AS hsr_base_datetime
FROM std.kma_hsr_area_district_std;
```

### AWS 지역구별 과거관측 확인
```sql
SELECT district_name, observed_at, temp_c, precip_mm, humidity_pct
FROM mart.seoul_aws_district_timeline
WHERE district_name = '강남구'
ORDER BY observed_at DESC
LIMIT 50;

SELECT district_name, row_count, min_observed_at, max_observed_at
FROM mart.seoul_aws_district_coverage
ORDER BY district_name;
```

### KMA 구별 통합 날씨 확인
```sql
SELECT *
FROM mart.seoul_district_weather_timeline
ORDER BY base_datetime DESC, target_datetime DESC, district_name
LIMIT 50;
```

### 서울시 강우량 확인
```sql
SELECT observed_at, station_code, station_name, district_name, rain_10m_mm
FROM std.seoul_rainfall_std
ORDER BY observed_at DESC, district_name, station_code;
```

### 서울시 하천 수위 확인
```sql
SELECT observed_at, station_code, station_name, river_name, district_name,
       water_level_m, control_level_m
FROM std.seoul_river_stage_std
ORDER BY observed_at DESC, district_name, station_code;
```

### HSR 구 단위 레이더값 확인
```sql
SELECT base_datetime, district_name, district_code, value_numeric, unit, is_no_echo
FROM std.kma_hsr_area_district_std
ORDER BY base_datetime DESC, district_code;
```

### 강우량계 위치 확인
```sql
SELECT station_code, station_name, station_address, latitude, longitude
FROM ref.seoul_rain_gauge_station_current
ORDER BY station_code;
```

### 침수흔적도 확인
```sql
SELECT source_year, district_name, flood_zone_name, flooded_area_sqm, inundation_depth_m
FROM ref.seoul_flood_trace
ORDER BY source_year DESC, district_name
LIMIT 100;
```

### 서울 자치구별 총종사자수 확인
```sql
-- 요약 점검 (예: base_year = 2024)
SELECT COUNT(*) AS row_count
FROM ref.seoul_district_worker_stats
WHERE base_year = 2024;

SELECT COUNT(DISTINCT district_name) AS district_count
FROM ref.seoul_district_worker_stats
WHERE base_year = 2024;

SELECT COUNT(*) AS mart_row_count
FROM mart.seoul_district_worker_features
WHERE base_year = 2024;
```

전체 검증은 `psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -f sql/verify_seoul_district_worker_stats.sql`

### 서울 자치구별 취약계층 밀집도 확인
```sql
-- row count / district count
SELECT COUNT(*) AS row_count, COUNT(DISTINCT district_name) AS district_count
FROM ref.seoul_vulnerable_population_district_snapshot;

-- 샘플 10행 (비율 소수점 4자리)
SELECT
    district_name,
    total_population,
    elderly_population_total,
    ROUND(elderly_population_ratio::numeric, 4) AS elderly_ratio,
    disabled_population_total,
    ROUND(disabled_population_ratio::numeric, 4) AS disabled_ratio,
    basic_livelihood_recipient_total,
    basement_household_count,
    ROUND(aged_basement_household_ratio::numeric, 4) AS aged_basement_ratio,
    elderly_source_label,
    disabled_source_year
FROM mart.seoul_vulnerable_population_district_latest
ORDER BY district_name
LIMIT 10;
```

전체 검증은 `psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -f sql/verify_seoul_vulnerable_population.sql`

### 서울시 건설공사 추진 현황 확인
```sql
SELECT COUNT(*) AS ref_rows, COUNT(DISTINCT district_name) AS district_count
FROM ref.seoul_construction_progress;

SELECT district_name, COUNT(*) AS project_count
FROM ref.seoul_construction_progress
GROUP BY district_name
ORDER BY district_name;

SELECT exclusion_reason, COUNT(*) AS row_count
FROM raw.seoul_construction_progress_raw
WHERE requested_at = (SELECT MAX(requested_at) FROM raw.seoul_construction_progress_raw)
GROUP BY exclusion_reason
ORDER BY exclusion_reason;
```

### 자연재해위험개선지구 확인
```sql
SELECT serial_no, zone_name, district_name, progress_status, facility_type, designated_date
FROM ref.seoul_disaster_risk_zone
ORDER BY serial_no;
```

## 10. 구 단위 확인 SQL
### 구별 강우량 최신값
```sql
SELECT observed_at, district_name, station_count, avg_rain_10m_mm, max_rain_10m_mm
FROM mart.seoul_rainfall_district_latest
ORDER BY observed_at DESC, district_name;
```

### 구별 하천 수위 최신값
```sql
SELECT observed_minute, district_name, station_count,
       avg_water_level_m, max_water_level_m, max_control_level_m
FROM mart.seoul_river_stage_district_latest
ORDER BY observed_minute DESC, district_name;
```

### 구별 HSR 최신값
```sql
SELECT district_name, district_code, base_datetime, value_numeric, unit, is_no_echo
FROM mart.kma_hsr_area_district_latest
ORDER BY district_code;
```

### 구별 정적 침수 feature 확인
```sql
SELECT *
FROM mart.seoul_district_flood_features
ORDER BY district_name;
```

### 특정 구의 모델 입력 feature 확인
```sql
SELECT *
FROM mart.seoul_district_model_features
WHERE district_name = '강남구'
ORDER BY base_datetime DESC, target_datetime DESC
LIMIT 50;
```

### 특정 구의 AWS 결측 여부 확인
```sql
SELECT district_name, base_datetime, aws_observed_at, aws_precip_mm, aws_missing_flag
FROM mart.seoul_district_model_features
WHERE district_name IN ('종로구', '중구', '강남구')
ORDER BY district_name, base_datetime DESC
LIMIT 100;
```

### 전체 구 모델 feature 확인
```sql
SELECT product_type, district_name, base_datetime, target_datetime, lead_minutes,
       precip_mm, temp_c,
       avg_rain_10m_mm, max_rain_10m_mm,
       avg_water_level_m, max_water_level_m,
       hsr_observed_at, hsr_value_numeric, hsr_is_no_echo,
       flood_trace_count_total, disaster_risk_zone_count
FROM mart.seoul_district_model_features
ORDER BY base_datetime DESC, target_datetime DESC, district_name
LIMIT 100;
```

## 11. 모델 입력용 뷰 설명
`mart.seoul_district_model_features`는 다음을 한 행에 합칩니다.

- KMA 구별 실황/예보
- `base_datetime` 시점까지 관측 가능한 서울시 강우량
- `base_datetime` 시점까지 관측 가능한 서울시 하천 수위(원천상 수위계가 없는 구는 값이 비거나 관측이 없음. `river_district_has_stations`·`river_observation_present`로 구분)
- `base_datetime` 시점까지 관측 가능한 HSR 레이더 구 단위 값
- `base_datetime` 시점까지 관측 가능한 AWS 지역구별 과거관측
- 자치구 단위 정적/준정적 feature
  - `rain_gauge_current_count`
  - 침수흔적도 집계: `flood_trace_count_2023`, `flood_trace_count_2024`, `flood_trace_count_2025`, `flood_trace_count_total`, `flooded_area_sqm_*`
  - 자연재해위험개선지구 집계: `disaster_risk_zone_count`, `disaster_risk_zone_in_progress_count`, `disaster_risk_zone_expired_count`
  - 취약계층 밀집도 9개 컬럼: `elderly_population_total`, `elderly_population_ratio`, `disabled_population_total`, `disabled_population_ratio`, `basic_livelihood_recipient_total`, `basic_livelihood_recipient_ratio`, `basement_household_count`, `aged_basement_household_count`, `aged_basement_household_ratio`

현재 구현 기준으로 보면 `mart.seoul_district_model_features`에는 침수흔적도, 위험개선지구, 강우계 수, 취약계층 밀집도 9개 컬럼이 포함됩니다. 반면 `total_worker_count` 같은 worker feature는 아직 포함되지 않고, OA-15439 기반 `floating_pop_korean*`도 이 뷰가 아니라 `mart.seoul_district_realtime_features_latest`에만 노출됩니다.

즉, 이 뷰는 시점별 모델 입력과 학습 데이터셋 구성의 출발점으로는 적합하지만, 생활인구 proxy나 총종사자수까지 이미 한데 합쳐진 "완성형 feature store"로 보지는 않는 것이 맞습니다.

## 12. 종로구 AWS 결측 처리 원칙

운영 `DB`/`mart`/서빙 기준 district universe는 서울 25개 자치구입니다. 다만 현재 프로젝트 폴더에 제공된 AWS 원본 파일셋만 `24개 구`를 포함하고 있으며, `종로구` 폴더/파일은 없습니다.

따라서 `종로구 AWS 결측`은 적재 오류가 아니라 `원본 부재`입니다.

### 자동 보간 (sql/012_district_model_features.sql)

`mart.seoul_district_model_features` 뷰에서 종로구의 AWS 컬럼은 인접 구 평균으로 자동 보간됩니다.

- 보간 기준: `meta.seoul_district_grid_map`에 등록된 종로구 `(nx, ny)`를 기준으로, 같은 메타에서 종로구를 제외한 다른 구 중 Chebyshev 거리 ≤ 1인 구들이 이웃이다. 이웃 집합은 격자표(`data/seoul_district_grids.csv` → `017` 적용)가 바뀌면 자동으로 따라간다(고정 9개 목록 아님).
- 보간 방식: 이웃 구마다 `std.seoul_aws_district_hourly`에서 `base_datetime` 이전 최신 1건을 뽑은 뒤, 그 값들의 평균 (NULL 제외).
- 식별 컬럼: `aws_neighbor_imputed = true`
- `aws_missing_flag = 0` + `aws_neighbor_imputed = true` → 인접 구 평균으로 채워진 값
- `aws_missing_flag = 1` → 본 구 데이터도 없고 인접 구 보간도 실패한 경우 (현재 발생 없음)

### 모델 학습 시 권장 처리

- 종로구를 전체 학습에서 제거하지 않아도 됨
- `aws_neighbor_imputed` 컬럼을 보조 feature 또는 샘플 weight 기준으로 활용 가능
- 보간값의 신뢰도가 낮다고 판단할 경우, 해당 행에 낮은 weight를 부여하는 방식이 안전

### 참고: 보간 전 원칙 (archived)

이전에는 아래 원칙을 사용했으나, 현재는 뷰에서 자동 처리합니다.

- `DB 전체에서 종로구를 제외하지는 않음`
- `모델 feature에서는 종로구를 유지`
- `AWS 관련 컬럼만 NULL + aws_missing_flag = 1`로 관리

## 13. DB 데이터 활용 가이드
이 프로젝트의 DB는 `수집 -> 정규화 -> 구 단위 집계 -> 모델 입력용 뷰` 순서로 활용하면 됩니다.

### 1) 원본 확인이 필요할 때
- API 원문이나 파일 원문을 보고 싶으면 `raw` 테이블을 확인합니다.
- 예:
  - `raw.kma_ultra_now_raw`
  - `raw.seoul_rainfall_raw`
  - `raw.seoul_aws_district_raw`

### 2) 관측소/격자 단위 분석이 필요할 때
- 전처리된 시계열을 확인하려면 `std` 테이블을 사용합니다.
- 예:
  - `std.kma_ultra_now_std`
  - `std.seoul_rainfall_std`
  - `std.seoul_river_stage_std`
  - `std.seoul_aws_district_hourly`

### 3) 구 단위 비교가 필요할 때
- 지역구별 비교나 대시보드에는 `mart` 뷰/테이블을 사용합니다.
- 예:
  - `mart.seoul_district_weather_timeline`
  - `mart.seoul_rainfall_district_latest`
  - `mart.seoul_river_stage_district_latest`
  - `mart.seoul_aws_district_timeline`
  - `mart.seoul_district_flood_features`

### 4) 모델 입력용 데이터셋을 만들 때
- 시작점은 `mart.seoul_district_model_features`를 우선 사용합니다.
- 이 뷰에는:
  - KMA 구별 실황/예보
  - 서울시 강우량
  - 서울시 하천 수위
  - HSR 레이더강수량
  - AWS 과거관측
  - 강우계 수, 침수흔적도, 위험개선지구, 취약계층 밀집도 9개 컬럼
  가 같이 붙어 있습니다.
- 다만 `total_worker_count`와 `floating_pop_korean*`는 현재 이 뷰에 없습니다.

- `HSR 레이더강수량`은 `mart.seoul_district_model_features`와 별도 조회용 뷰 `mart.kma_hsr_area_district_latest` 둘 다에서 확인할 수 있습니다.

### 5) 추천 활용 방식
- `시점별 모델 입력/학습용 시작점`: `mart.seoul_district_model_features`
- `실시간 최신 서빙 입력`: `mart.seoul_district_realtime_features_latest`
- `과거 기후 패턴 분석`: `std.seoul_aws_district_hourly`
- `구별 취약도 분석`: `mart.seoul_district_flood_features`, `mart.seoul_vulnerable_population_district_latest`
- `서울시 실시간 상황판`: `mart.seoul_rainfall_district_latest`, `mart.seoul_river_stage_district_latest`
- `예보와 관측 비교`: `mart.seoul_district_weather_timeline` + `mart.seoul_aws_district_timeline`
- `총종사자수 참조`: `mart.seoul_district_worker_features`

### 6) 시간 정렬 시 주의사항
- `requested_at`는 수집 시각이고, `observed_at`/`base_datetime`는 데이터 시각입니다.
- 모델링이나 분석에서는 보통 `requested_at`보다 `observed_at`, `base_datetime`, `target_datetime`를 기준으로 맞추는 것이 더 중요합니다.
- 미래 정보를 섞지 않으려면:
  - 관측값은 `base_datetime 이전 또는 같은 시각`
  - 예보값은 `base_datetime 기준 미래 target_datetime`
  구조로 맞추는 것이 좋습니다.

### 7) 종로구 처리
- 종로구는 AWS만 비어 있고, 다른 데이터는 존재합니다.
- 현재 `mart.seoul_district_model_features` 뷰에서 인접 구 평균 보간이 자동 적용됩니다.
- `aws_neighbor_imputed = true` 컬럼으로 보간 행을 식별할 수 있습니다.
- 종로구를 전체 분석 대상에서 제거할 필요 없습니다.

## 14. 공유 시 주의사항
- `.env` 실제 키는 저장소에 올리지 않습니다.
- 로컬 원본 파일은 팀원도 동일하게 받아야 합니다.
- 자동수집은 경로 의존성이 있으므로 팀 공유 시 먼저 수동 실행 기준으로 맞추는 것이 좋습니다.
- GitHub 업로드 전에는 `.env`, 로그, 로컬 DB 파일 포함 여부를 반드시 다시 확인해야 합니다.

## 14-1. 팀원 원격 접속 (SSH 터널)

### 1) 개요
- 로컬 PostgreSQL/PostGIS를 팀원이 사용할 때는 DB 포트를 직접 여는 대신 SSH 터널 방식으로 접속합니다.
- 팀원 입장에서는 “SSH 연결 1개 + localhost 포트 접속”만 하면 됩니다.

### 2) SSH 터널 여는 방법
아래 명령으로 로컬 `5433` 포트를 열고, SSH를 통해 호스트의 `5432`로 전달합니다.

```bash
ssh -L 5433:localhost:5432 <호스트맥사용자명>@<호스트접속주소>
```

예시:

```bash
ssh -L 5433:localhost:5432 jaemin@192.168.0.10
```

설명:
* 팀원 PC의 `localhost:5433` 으로 접속하면
* SSH를 통해
* 호스트 맥의 `localhost:5432` PostgreSQL로 전달됨
* 따라서 팀원은 DB 접속 시 `localhost:5433`을 사용하면 됨

### 3) psql 접속 예시
```bash
psql "host=localhost port=5433 dbname=weather user=teammate"
```
비밀번호는 별도로 전달받은 팀원용 DB 계정을 사용합니다.

### 4) GUI 툴 접속 예시
다음 값으로 접속하면 됩니다.

* Host: `localhost`
* Port: `5433`
* Database: `weather`
* User: `teammate`
* Password: 전달받은 팀원용 비밀번호

추가로, DBeaver / TablePlus / DataGrip 등에서 SSH 기능을 따로 쓰기보다, 먼저 터미널에서 SSH 터널을 연 뒤 `localhost:5433`으로 붙는 방식이 가장 단순합니다.

### 5) 팀원용 `.env` 예시
```env
DB_HOST=localhost
DB_PORT=5433
DB_NAME=weather
DB_USER=teammate
DB_PASSWORD=TEAMMATE_PASSWORD
```

설명:
* SSH 터널을 쓰므로 `DB_HOST`는 여전히 `localhost` 입니다.
* 비밀번호는 실제 발급받은 값으로 교체합니다.

### 6) 연결 확인 SQL
```sql
SELECT current_database(), current_user;

SELECT table_schema, table_name
FROM information_schema.tables
WHERE table_schema IN ('raw', 'std', 'mart', 'ref', 'meta')
ORDER BY table_schema, table_name
LIMIT 50;
```

프로젝트 상태 확인은 README의 기본 확인 SQL을 그대로 사용하면 됩니다.

예시:
```sql
SELECT *
FROM mart.kma_collection_status
ORDER BY product_type, data_layer;

SELECT *
FROM mart.external_source_collection_status
ORDER BY source_name;
```

### 7) 간단한 주의사항
* SSH 터널 세션이 종료되면 DB 접속도 끊길 수 있습니다.
* 비밀번호가 들어간 `.env`는 저장소에 커밋하지 않습니다.
* 자동수집보다는 우선 조회/분석/수동 실행 기준으로 사용하는 것이 안전합니다.

## 15. 실시간 예측용 feature와 학습용 데이터셋 분리
운영용 실시간 입력과 학습/평가용 데이터셋은 같은 출발점에서 만들되, DB 객체는 분리해서 관리합니다.
본 섹션은 모델링 및 분석 담당자가 데이터셋을 해석하고 추출할 때의 기준 문서로 사용합니다.

- 실시간 입력 베이스: `mart.seoul_district_model_features`
- 실시간 최신 입력 뷰: `mart.seoul_district_realtime_features_latest`
- 학습셋 내부 베이스 뷰: `mart.seoul_district_heavyrain_trainset_base`
- 라벨 대기 뷰: `mart.seoul_district_heavyrain_trainset_pending`
- 라벨 확정 학습 뷰: `mart.seoul_district_heavyrain_trainset`

역할 요약:

- `mart.seoul_district_realtime_features_latest`
  - 각 구의 최신 입력 feature `1행`만 바로 조회하기 위한 뷰입니다.
  - `product_type = 'ultra_now'`와 `target_datetime = base_datetime`만 사용합니다.
  - OA-15439 내국인 생활인구 proxy `floating_pop_korean*`는 현재 이 뷰에만 as-of 조인됩니다.
- `mart.seoul_district_heavyrain_trainset_base`
  - `district_name + base_datetime` 단위의 내부 학습셋 베이스입니다.
  - 타깃, 라벨 준비 시각, split 메타를 같이 계산합니다.
  - 현재 `floating_pop_korean*`는 자동 포함되지 않습니다.
- `mart.seoul_district_heavyrain_trainset_pending`
  - 아직 `future 3h`가 지나지 않아 라벨이 확정되지 않은 최신 행만 구별 `1행`씩 보여줍니다.
  - pending 상태에서는 타깃 컬럼을 `NULL`로 둡니다.
- `mart.seoul_district_heavyrain_trainset`
  - `dataset_status = 'labeled'`인 행만 포함합니다.
  - 학습/검증/테스트 분할은 `split_type`으로 바로 사용할 수 있습니다.

## 16. 학습 행 단위와 타깃 정의
### 1) 1행 기준
현재 `mart.seoul_district_model_features`는 `product_type`, `target_datetime` 때문에 한 `base_datetime`에 여러 행이 존재할 수 있습니다.

이번 v1 학습셋은 중복과 누수를 피하기 위해 아래 기준으로 `1행`을 고정합니다.

- 행 단위: `district_name + base_datetime`
- 사용 행: `product_type = 'ultra_now'`
- 해석: `base_datetime` 시점에 실제로 알고 있던 입력만으로 3시간 뒤 위험을 맞히는 데이터셋

즉, 예보 리드타임별 다중 행을 그대로 학습셋에 쓰지 않고, `의사결정 시점(nowcast)` 행만 남깁니다.
예보 리드 feature를 함께 사용할 경우 이후 버전에서 `lead_minutes`별 pivot 또는 집약 feature를 별도로 추가하는 방식을 권장합니다.

### 2) 라벨 원천 데이터 선택
기본 라벨 원천은 `서울시 강우량 정보`를 사용합니다.

구체적으로는:

- 원천 뷰: `mart.seoul_rainfall_district_latest`
- 사용 컬럼: `max_rain_10m_mm`
- 이유:
  - 현재 `mart.seoul_district_model_features`의 운영 구간과 직접 시간적으로 이어집니다.
  - 구 단위 집계가 이미 되어 있어 바로 결합할 수 있습니다.
  - `종로구`까지 포함한 `25개 구` 전체를 유지할 수 있습니다.
  - `10분 단위`라서 `future 3h` 누적 강수 계산이 더 세밀합니다.

`AWS 지역구별 과거관측`은 장기 이력은 좋지만 현재 저장된 운영 구간과 직접 이어지지 않고, `종로구` 원본이 비어 있습니다.
따라서 현재 구조에서는 `AWS`를 기본 라벨로 사용하지 않고, 향후 백필 또는 별도 검증용 보조 라벨로 두는 방식이 더 안전합니다.

### 3) 타깃 정의
- `label_window_end = base_datetime + interval '3 hours'`
- `label_ready_at = base_datetime + interval '3 hours 20 minutes'`
  - 서울시 실시간 강우량 관측이 수 분 늦게 들어오는 경우를 고려해 `20분` 버퍼를 둡니다.
- `target_rain_3h_mm`
  - 정의: `(base_datetime, base_datetime + 3h]` 구간의 `max_rain_10m_mm` 합계
- `target_rain_1h_mm`
  - 정의: `(base_datetime, base_datetime + 1h]` 구간의 `max_rain_10m_mm` 합계
- `target_heavy_rain_flag`
  - 정의: 아래 조건 중 하나라도 만족하면 `1`, 아니면 `0`
    - `target_rain_1h_mm >= 20`
    - `lead(+1h, +2h, +3h)`의 `target_rain_1h_mm` 중 하나 이상이 `>= 20`
    - `target_rain_3h_mm >= 40`
    - `lead(+1h, +2h, +3h)`의 `target_rain_3h_mm` 중 하나 이상이 `>= 40`

현재 v1은 `구 전체 평균 강수`보다 `구 내 국지적 위험`을 더 보수적으로 포착하기 위해 `max_rain_10m_mm` 합계를 기본안으로 사용합니다.

### 4) 파생 feature 컬럼 (2026-04 업데이트)
학습 뷰 `mart.seoul_district_heavyrain_trainset` 및 pending 뷰에 아래 파생 컬럼을 포함합니다.

- `dew_point_c`: 이슬점(섭씨), `temp_c`/`humidity_pct` 기반 계산값
- `past_rain_3h_mm`: 과거 3시간 누적 강수량(`현재 + 1시간 전 + 2시간 전`)
- `temp_change_3h_c`: 3시간 기온 변화량(`현재 - 3시간 전`)
- `humidity_change_3h_pct`: 3시간 습도 변화량(`현재 - 3시간 전`)
- `moist_energy`: `(temp_c * humidity_pct) / 100`
- `label`: 협업 편의용 alias(`target_heavy_rain_flag`와 동일)

중요: `target_rain_3h_mm`는 미래 3시간 누적 강수 타깃이고,  
`past_rain_3h_mm`는 과거 3시간 입력 feature입니다. 둘을 혼용하면 누수가 발생합니다.

## 17. 시간 정렬 규칙과 데이터 누수 방지
핵심 원칙은 `base_datetime 시점에 실제로 알 수 있었던 입력만 feature에 남기고`, 라벨은 반드시 그 이후 3시간 창에서 계산하는 것입니다.

- feature는 `base_datetime` 이전 또는 같은 시각의 관측만 사용합니다.
- 타깃은 반드시 `base_datetime` 초과, `base_datetime + 3h` 이하 구간만 사용합니다.
- pending 행은 `label_ready_at` 이전까지 `target_*`를 `NULL`로 둡니다.
- 학습셋과 실시간 최신 입력은 서로 다른 뷰로 분리합니다.
- split도 랜덤이 아니라 시간순으로만 자릅니다.

즉, `현재 입력`과 `미래 3시간 결과`를 명확히 분리해서 leakage를 막는 구조입니다.

## 18. split 기준과 현재 검증 결과
현재 DB에서 `labeled` 구간이 며칠 수준이므로, 월 단위가 아니라 `최근 24시간/12시간 hold-out` 규칙을 적용했습니다.

- `train`: `latest_labeled_base - 24h` 이전
- `valid`: `latest_labeled_base - 24h` 이상, `latest_labeled_base - 12h` 미만
- `test`: `latest_labeled_base - 12h` 이상
- `pending`: 아직 `label_ready_at` 미도래

현재 검증 시점 기준:

- `latest_labeled_base`: `2026-03-27 13:00+09`
- `train`: `905`행, 이 중 `is_trainable = true` `392`행
- `valid`: `75`행, 이 중 `is_trainable = true` `75`행
- `test`: `300`행, 이 중 `is_trainable = true` `300`행
- `pending`: `25`행

`is_trainable`은 시간상 라벨이 확정되었더라도 실제 미래 3시간 창에서 강우 라벨 원천 관측이 `1건도 없으면 false`로 둡니다.
즉, `dataset_status`와 `is_trainable`을 분리하여 `시간상 확정`과 `실제 학습 사용 가능`을 구분합니다.

검증 SQL:

```sql
SELECT COUNT(*) AS realtime_rows,
       COUNT(DISTINCT district_name) AS realtime_districts
FROM mart.seoul_district_realtime_features_latest;

SELECT split_type,
       COUNT(*) AS row_count,
       COUNT(*) FILTER (WHERE is_trainable) AS trainable_row_count,
       MIN(base_datetime) AS min_base,
       MAX(base_datetime) AS max_base
FROM mart.seoul_district_heavyrain_trainset
GROUP BY split_type
ORDER BY CASE split_type
             WHEN 'train' THEN 1
             WHEN 'valid' THEN 2
             WHEN 'test' THEN 3
             ELSE 4
         END;

SELECT COUNT(*) AS pending_rows,
       COUNT(DISTINCT district_name) AS pending_districts
FROM mart.seoul_district_heavyrain_trainset_pending;
```

## 19. 예외 데이터 처리 원칙
### 1) HSR `no-echo(-250)`
- `HSR`는 `-250` 같은 무에코 값을 가질 수 있으므로 수치 자체와 별도로 `hsr_is_no_echo` 플래그를 유지합니다.
- 현재 데이터에서는 최근 적재 구간이 사실상 전부 `no-echo`로 들어와 있으므로, 학습 시에는:
  - `hsr_is_no_echo`를 별도 feature로 사용하고
  - `hsr_value_numeric`는 그대로 두거나, 모델 입력 전에 `0 또는 NULL` 처리 규칙을 명시적으로 정하는 방식을 권장합니다.

### 2) 종로구 AWS 결측 → 인접 구 평균 자동 보간
- `종로구 AWS`는 적재 실패가 아니라 `원본 부재`입니다.
- `mart.seoul_district_model_features` 뷰에서 종로구의 AWS 값은
  `meta.seoul_district_grid_map` 기준 Chebyshev ≤ 1 이웃 구들의 최신값 평균으로 자동 보간됩니다.
- `aws_neighbor_imputed = true`로 보간 여부를 식별합니다.
- 현재 2026 운영 구간에서는 AWS 원천이 `2025-12-31`까지여서, `aws_lag_minutes`가 매우 크게 나타납니다.
- 즉, 현재 v1 학습셋에서 AWS 컬럼은 `stale historical feature`로 취급해야 하며, 실제 학습 시에는 `aws_lag_minutes` 기준으로 gating하는 방식을 권장합니다.

### 3) 지연 관측치 처리
- 서울시 실시간 강우량은 `requested_at`과 `observed_at`가 다를 수 있습니다.
- 그래서 라벨 확정 시각을 `base + 3h`가 아니라 `base + 3h + 20m`로 두었습니다.
- pending 뷰는 이 지연을 흡수하기 위한 운영용 대기 큐 역할을 합니다.

## 20. 학습용 CSV 추출 산출물

> 추출 원천 뷰: `mart.seoul_district_heavyrain_trainset`
>
> 저장 경로: `data/trainset/`

이 프로젝트의 학습용 CSV는 DB 기준으로 언제든 재생성 가능한 스냅샷입니다.
라벨 기준이 변경될 수 있으므로, `data/trainset/` 내 기존 CSV들은 구버전 기준 스냅샷으로 간주하고 최신 기준이 필요하면 반드시 재추출하세요.

### CSV 재생성 방법 (권장)

```bash
./scripts/export_trainset.sh
```

실행 시 `data/trainset/` 아래에 `train_YYYY-MM-DD_HHMM.csv`, `valid_...`, `test_...` 3개 파일이 생성됩니다.

### 추출 기준 SQL

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

### 각 파일 설명

- train: 시간 기준 hold-out 학습 구간. `latest_labeled_base - 24h` 이전의 라벨 확정 행.
- valid: 학습/테스트 중간 검증 구간. `latest_labeled_base - 24h` 이상, `latest_labeled_base - 12h` 미만.
- test: 최신 구간 성능 평가용. `latest_labeled_base - 12h` 이상의 라벨 확정 행.

모든 파일은 `dataset_status = 'labeled'`, `is_trainable = true`인 행만 포함하며, `split_type`이 단일 값으로 고정되어 있다.

### realtime / pending CSV와의 구분

| 구분 | 이번 추출 CSV | realtime | pending |
| --- | --- | --- | --- |
| 원천 뷰 | `mart.seoul_district_heavyrain_trainset` | `mart.seoul_district_realtime_features_latest` | `mart.seoul_district_heavyrain_trainset_pending` |
| 라벨 확정 여부 | 확정 (`labeled`) | 없음 | 미확정 (`pending`) |
| 시간 기준 | 과거 시점 스냅샷 | 현재 최신 시점 | 현재 최신 시점 |
| 학습 사용 가능 | O | X | X |

### 주의사항

- AWS는 현재 2026 운영 구간에서 stale 가능 (`aws_lag_minutes` 확인 필수)
- 종로구 AWS는 원천 부재 → `aws_missing_flag = 1` 기준으로 처리
- HSR는 no-echo(`-250`) 값이 많음 → `hsr_is_no_echo` 플래그 병용 권장

### 4) v5.1 AWS 장기 학습셋 (최종 권장본)

위의 `mart.seoul_district_heavyrain_trainset` 기반 CSV는 2026 운영 구간 중심의 기존 trainset 설명입니다.  
`2020~2025` 장기 학습, 고정 split, leakage-free export, train/serve preprocessing 일치가 필요한 경우에는 아래 v5.1 AWS 장기 학습셋을 사용하세요.

#### 개요

- 버전명: `seoul_district_heavyrain_v5_1_aws_final`
- 라벨 기준: `1h >= 20mm OR 3h >= 40mm`, 리드 `+0h ~ +3h` OR 확장
- 원천 소스: `std.seoul_aws_district_hourly`
- 대상 구: 24개 구
  - 이 AWS 장기 학습셋 v5.1 버전 한정으로 `종로구` 제외
- split:
  - `train`: `2020-01-01 00:00:00+09 ~ 2023-12-31 23:00:00+09`
  - `valid`: `2024-01-01 00:00:00+09 ~ 2024-12-31 23:00:00+09`
  - `test`: `2025-01-01 00:00:00+09 ~ 2025-12-31 20:00:00+09`

#### 왜 v5.1이 최종 권장본인가

- `train/valid/test` 전체 기간이 모두 채워져 있습니다.
- 이 학습셋 버전에서는 split별 district universe가 모두 동일한 24개 구로 고정되어 있습니다.
- feature-only / label / audit CSV가 분리되어 있고, `(district_name, base_datetime)` 기준으로 `1:1` 정합입니다.
- feature-only에는 미래 정답 컬럼이 들어가지 않습니다.
- 학습용 전처리와 운영 추론용 전처리를 같은 SQL 규칙으로 재현할 수 있도록 inference view가 함께 제공됩니다.

#### 전처리 규칙

v5.1은 AWS 원천의 결측을 아래처럼 학습/서빙 공통 규칙으로 처리합니다.

- `precip_mm`
  - 원시 강수(`precip_mm_observed`)가 `NULL`이면 `0.0`으로 대체
- `humidity_pct`
  - 구별 시계열 기준 `LOCF(last observation carried forward)`
  - LOCF조차 불가능하면 `65.0` 기본값 사용
- 파생 컬럼
  - `dew_point_c`
  - `past_rain_3h_mm`
  - `temp_change_3h_c`
  - `humidity_change_3h_pct`
  - `moist_energy`
- 학습 가능 여부
  - 위 파생 컬럼까지 모두 계산 가능한 행만 `is_model_input_ready = true`

#### 생성 테이블 / 뷰

- 최종 snapshot
  - `mart.hrain_v5_1_aws_snapshot_20260402`
- split별 audit
  - `mart.hrain_v5_1_aws_train_audit_20260402`
  - `mart.hrain_v5_1_aws_valid_audit_20260402`
  - `mart.hrain_v5_1_aws_test_audit_20260402`
- split별 feature-only
  - `mart.hrain_v5_1_aws_train_features_20260402`
  - `mart.hrain_v5_1_aws_valid_features_20260402`
  - `mart.hrain_v5_1_aws_test_features_20260402`
- split별 label
  - `mart.hrain_v5_1_aws_train_labels_20260402`
  - `mart.hrain_v5_1_aws_valid_labels_20260402`
  - `mart.hrain_v5_1_aws_test_labels_20260402`
- 모델 입력용 가공 테이블
  - `mart.hrain_v5_1_aws_train_model_input_20260402`
  - `mart.hrain_v5_1_aws_valid_model_input_20260402`
  - `mart.hrain_v5_1_aws_test_model_input_20260402`
- 운영 추론용 최신 view
  - `mart.hrain_v5_1_aws_inference_audit_latest_20260402`
  - `mart.hrain_v5_1_aws_inference_features_latest_20260402`
  - `mart.hrain_v5_1_aws_inference_model_input_latest_20260402`

#### CSV 산출물

저장 경로: `data/trainset/`

- feature-only
  - `seoul_train_features_only_v5_1_aws_20260402.csv`
  - `seoul_valid_features_only_v5_1_aws_20260402.csv`
  - `seoul_test_features_only_v5_1_aws_20260402.csv`
- inference latest
  - `seoul_inference_features_latest_v5_1_aws_20260402.csv`
- label
  - `seoul_train_labels_v5_1_aws_20260402.csv`
  - `seoul_valid_labels_v5_1_aws_20260402.csv`
  - `seoul_test_labels_v5_1_aws_20260402.csv`
- audit
  - `seoul_train_audit_v5_1_aws_20260402.csv`
  - `seoul_valid_audit_v5_1_aws_20260402.csv`
  - `seoul_test_audit_v5_1_aws_20260402.csv`

#### CSV별 컬럼 역할

- feature-only CSV
  - 컬럼: `district_name`, `base_datetime`, `temp_c`, `precip_mm`, `humidity_pct`, `dew_point_c`, `past_rain_3h_mm`, `temp_change_3h_c`, `humidity_change_3h_pct`, `moist_energy`
  - 용도: 최소 학습 입력 export
- label CSV
  - 컬럼: `district_name`, `base_datetime`, `label`
  - 용도: feature-only와 조인하여 감독학습 라벨 사용
- audit CSV
  - 용도: 원시 관측값, 결측 대체 여부, 라벨 계산 메타데이터, provenance 추적

#### 최종 모델 입력 권장안

feature-only CSV는 바로 학습에 쓸 수 있지만, 최종 모델 입력은 `model_input` 테이블 기준을 권장합니다.

- 조인 키
  - `district_name`, `base_datetime`
- 모델 raw input에서 제외 권장
  - `district_name`
  - `base_datetime`
- 대신 사용할 파생 입력
  - `district_id`
  - `base_hour`
  - `base_month`
  - `day_of_week`
  - `is_monsoon_season_flag`
  - `hour_sin`, `hour_cos`
  - `month_sin`, `month_cos`
  - 기본 기상 feature 8종

#### 재생성 / 검증 스크립트

- 생성 SQL
  - `sql/021_heavyrain_modelready_aws_v5_1_final.sql`
- 진단 SQL
  - `sql/021_heavyrain_modelready_aws_v5_1_diagnostics.sql`
- 승인 게이트
  - `sql/021_heavyrain_modelready_aws_v5_1_validation_gates.sql`
- export 스크립트
  - `scripts/export_seoul_district_heavyrain_modelready_v5_1_aws.py`

```bash
psql -h localhost -U postgres -d weather -f sql/021_heavyrain_modelready_aws_v5_1_final.sql
psql -h localhost -U postgres -d weather -f sql/021_heavyrain_modelready_aws_v5_1_validation_gates.sql
PYTHONPATH=. python scripts/export_seoul_district_heavyrain_modelready_v5_1_aws.py
```

#### 최종 승인 요약 (v5.1 AWS 장기 학습셋 한정)

- district universe: 24개 구
- 종로구 포함 여부: 제외 (`v5.1 AWS 장기 학습셋` 범위)
- label 정책: `20/40` 최종 확정
- train/serve preprocessing consistency: 보장
- leakage-free feature export: 보장
- feature-label 1:1 정합: 보장

장기 모델 학습, 실험 재현, 운영 추론 스키마 일치가 필요하면 기본 선택지는 v5.1로 보면 됩니다.

## 21. 추천 학습/검증 방식과 대응 점수 확장 방향
### 1) 추천 1차 베이스라인
- 모델은 먼저 `LightGBM` 또는 `XGBoost` 같은 트리 기반 모델을 추천합니다.
- 이유:
  - 결측과 이질적 feature를 다루기 쉽고
  - 상대적으로 적은 행 수에서도 빠르게 baseline을 만들 수 있으며
  - feature importance 해석이 비교적 쉽습니다.

### 2) 추천 검증 방식
- 랜덤 분할은 사용하지 않습니다.
- 반드시 `시간 기준 split(train/valid/test)`을 유지합니다.
- 추후 데이터가 충분히 쌓이면 `rolling origin` 또는 `walk-forward validation`으로 확장하는 것이 좋습니다.

### 3) 최종 대응 점수 설계 방향
이번 작업에서는 전체 점수 계산을 구현하지 않았지만, 최종 의사결정 계층은 아래처럼 확장하는 것이 자연스럽습니다.

- `hazard_score`
  - 실시간 강우, 3시간 위험 예측값, HSR, 하천수위 기반 위험도
- `vulnerability_score`
  - 침수흔적도, 위험개선지구, 취약계층 밀집도 기반 취약도
  - 취약계층 밀집도 feature 적재 완료 (`ref.seoul_vulnerable_population_district_snapshot` / `mart.seoul_vulnerable_population_district_latest`). 고령자 비율·장애인 비율·기초생활수급자 비율·노후 지하반지하 비율 포함.
  - composite `vulnerability_score` 가중합 산식은 미확정 — feature 노출 완료, 가중치 확정 후 §22 기준으로 추가 예정. (`mart.seoul_district_model_features`에 취약계층 컬럼 조인 반영: `sql/027_seoul_district_model_features_v2.sql`)
- `exposure_score`
  - 정책·운영용 노출 근사를 여러 축으로 쌓는 설계를 가정한다. 예: (i) 아래 §3-1 `outdoor_worker_exposure_score` — 옥외·외근 성격 노동 노출 proxy, (ii) OA-15439 내국인 생활인구 proxy(`floating_pop_korean*`) — 현재 `mart.seoul_district_realtime_features_latest`에만 붙는 인구 활동 관련 지연 as-of 참조(학습용 trainset에는 없음; 본 README §6 Living population 절, `MODELING_HANDOFF.md` §8 참고).  
  - `exposure_score`와 모델 라벨 `target_*`·예측 산출물을 혼동하지 말 것. 점수층은 의사결정·우선순위용이고, 폭우 이진/회귀 타깃 정의와는 별개다.
- `priority_score`
  - `hazard_score * vulnerability_score * exposure_score` 또는 가중합 기반 우선순위

### 3-1) `outdoor_worker_exposure_score` (1차 proxy 정의 · planned)

확정된 구현이 아니라, 침수·호우 위험노출 근사를 위해 팀이 참고할 운영용 1차 proxy 정의다. DB나 API에 `outdoor_worker_exposure_score`라는 단일 컬럼이 이미 있다고 가정하지 않는다.

#### 정의

- `outdoor_worker_exposure_score`는 실측 야외근로자 수가 아니다. 자치구별 옥외·외근 성격 노동에 노출된 규모를 z-score 가중으로 근사한 지표다.
- 이 값은 정책·운영용 위험노출 근사치이지, 실제 현장 인원 추정치가 아니다.

#### 1차 버전 산입(의도)

| 산입 | 역할 |
| --- | --- |
| 건설업 종사자수 | 옥외 현장 노동 비중이 큰 업종 proxy |
| 운수 및 창고업 종사자수 | 이동·물류 노동 proxy(배달과 중복 가능성 있음, 아래 가중치 참고) |
| 사업시설관리·사업 지원 종사자수 | 시설·외근 관리 성격 proxy |
| 배달업 종사자수 | 폭우·침수 시 도로 노출 가능성이 커 별도 항목으로 둔다 |
| 진행중 공사 수 | 건설계열 현장 활동성 보정용 proxy |

가중치·중복 관련: `운수 및 창고업 종사자수`에는 배달 관련 인력이 일부 포함될 수 있다. 배달업 종사자수를 별도 반영할 경우 이중 계상을 줄이기 위해, 운수·창고업 항목의 가중치를 상대적으로 낮춘다(아래 산식의 `0.4`).

공사 현황: 진행중 공사 수는 야외근로자 직접 관측 데이터가 아니다. 시설·현장 활동성을 보정하는 proxy로만 쓴다.

택배 물동량 등: 전체 야외근로자를 직접 나타내지 않으므로, 현재 1차안에서는 핵심 입력이 아니라 보조 후보로만 본다(소스·정의 확정 시 §22에서 재검토).

#### 제안 산식 (운영 1차안)

`z(·)`는 자치구 단위 원시 값을 서울 25개 구 횡단면에서 표준화한 z-score(평균 0, 표준편차 1)로 둔다고 가정한다.

```
outdoor_worker_base =
    1.0 * z(건설업 종사자수)
  + 0.4 * z(운수 및 창고업 종사자수)
  + 0.6 * z(사업시설관리/지원 종사자수)
  + 1.0 * z(배달업 종사자수)

outdoor_worker_exposure_score =
    0.8 * outdoor_worker_base
  + 0.2 * z(진행중 공사 수)
```

주의

- 위 산식은 운영용 1차 proxy 정의이며, 추후 실제 배달 activity 데이터나 야외근로자 직접 관측치를 확보하면 고도화·대체될 수 있다.
- 진행중 공사 수는 건설계열 외부활동 보정용 proxy이며, 야외근로자 수 자체를 의미하지 않는다.

#### 데이터·파이프라인 상태 (`exposure_score` 산출 관점)

아래는 이 README 시점 기준으로, 위 proxy를 채우기 위한 자산을 네 가지로 구분한 것이다.

| 상태 | 의미 |
| --- | --- |
| AVAILABLE | 적재·조회 가능하고, 원하면 분석·피처에 바로 쓸 수 있음 |
| PRESENT_BUT_UNWIRED | 원천 또는 ref에 있으나, exposure용 mart 컬럼·점수 파이프라인에 아직 연결되지 않음 |
| MISSING | 소스 미확보 또는 미적재 |
| DERIVED_PROXY | 위 산식처럼 정의만 있고, DB에 단일 컬럼으로 구현되지 않음(planned) |

| 대상 | 상태 | 비고 |
| --- | --- | --- |
| 산업별 종사자수(건설·운수·사업시설관리 등) | MISSING | `ref.seoul_district_worker_stats`는 총종사자수만 보유(§6 CSV 절). 업종 분해 적재는 후속. |
| 배달업 종사자수 | MISSING | 소스 확보·적재·연결 필요. 폭우 시 노출 proxy로 1차 정의에 포함 의도. |
| 야외근로자 직접 관측 데이터 | MISSING | 대체 불가 시 위 통계·공사 proxy로만 근사. |
| 공사 현황(진행중 공사 수 등) | PRESENT_BUT_UNWIRED | `ref.seoul_construction_progress` 및 `ref.seoul_construction_progress_summary`에서 구·준공상태별 집계 가능. `mart.seoul_district_flood_features` 등 폭우 모델용 mart에는 자동 미포함(별도 조인·집계 필요). |
| `outdoor_worker_exposure_score` | DERIVED_PROXY | 본 절 산식은 문서 정의; 운영 테이블/뷰 컬럼 없음. |
| 택배 물동량 등 | MISSING / 보조 후보 | 1차 핵심 입력에서 제외, 향후 보조 변수 후보. |

대체안(현재 쓸 수 있는 것)  
- 구별 총종사자수: `ref.seoul_district_worker_stats` / `mart.seoul_district_worker_features` (AVAILABLE) — 다만 업종 분해 없이 노출을 대표하지 못하므로, `outdoor_worker_exposure_score` 공식의 직접 대체로 쓰기엔 해석 한계가 크다.  
- 진행 공사 규모 proxy: `ref.seoul_construction_progress` 기반 집계(PRESENT_BUT_UNWIRED → 분석 시 SQL로 추출 가능).

## 22. Next steps (exposure·flood / risk scoring)

향후 개선·작업 예정이다. 아래는 §21.3-1 proxy를 실제 파이프라인에 붙이기 위한 체크리스트로 쓴다.

확정 구현과의 구분: 이 절은 TODO·계획이며, `target_*` 라벨이나 현재 학습 export 스키마에 자동 반영되지 않는다.

### 데이터

- 배달업 종사자수 데이터 소스 확보 및 적재(MISSING 해소).
- 공사 현황 mart 연결 여부 확인·구현(`ref.seoul_construction_progress` → 구별 진행 공사 수를 exposure·취약도용 mart 또는 배치 테이블로 노출할지 결정).
- 향후 인구·활동 proxy(예: 공개 activity·물동량) 검토 — 전면 대체가 아니라 보조·검증부터.

### 모델링

- §21.3-1 proxy 정의를 피처 스펙에 반영(train/serve 동일 as-of·누수 규칙 유지).
- 가중치 민감도 검토(특히 운수·배달 중복 구간).
- feature importance 및 설명력 점검(`target_*` 라벨과의 혼동 금지).

### 분석

- 자치구별 분포·이상치 확인.
- 과거 호우·침수 사례와의 상관·교차표 검토.
- 배달업 종사자수 추가 전후 스코어·모델 성능 비교(데이터 확보 후).

즉, 이번 v1 데이터셋은 향후 `위험도 예측`과 `대응 우선순위 산정`을 분리된 계층으로 확장하기 위한 최소 운영 기반입니다. §21.3-1·§22에 적은 exposure proxy·Next steps는 그 확장선상의 문서화된 1차안·후속 과제이다.

## 23. 데이터 출처 (원문·다운로드)

링크가 바뀌면 해당 사이트에서 데이터셋명·서비스명으로 검색한다.

기상청 초단기실황·초단기예보·단기예보 (수집기·공공데이터포털 API): [https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0](https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0) (공공데이터포털 · VilageFcstInfoService_2.0)

기상청 초단기실황 (포털 CSV 백필): [https://data.kma.go.kr/data/rmt/rmtList.do?code=400&pgmNo=570](https://data.kma.go.kr/data/rmt/rmtList.do?code=400&pgmNo=570) (기상청 기상자료개방포털)

서울시 강우량 정보 (OpenAPI · ListRainfallService): [https://data.seoul.go.kr/tec/index.do](https://data.seoul.go.kr/tec/index.do) (서울 열린데이터광장)

서울시 하천 수위 현황 (OpenAPI · ListRiverStageService): [https://data.seoul.go.kr/tec/index.do](https://data.seoul.go.kr/tec/index.do) (서울 열린데이터광장)

HSR(레이더) 행정구역별 조회: [https://apihub.kma.go.kr](https://apihub.kma.go.kr) (기상청 API허브 · 상세 URL은 `core/config.py`의 `HSR_FILE_LIST_URL`, `HSR_AREA_URL` 참고)

서울시 건설공사 추진 현황 (OA-2540 · ListOnePMISBizInfo): [https://data.seoul.go.kr/dataList/OA-2540/S/1/datasetView.do](https://data.seoul.go.kr/dataList/OA-2540/S/1/datasetView.do) (서울 열린데이터광장)

서울시 내국인 생활인구 proxy (OA-15439 · SPOP_LOCAL_RESD_JACHI): [https://data.seoul.go.kr/dataList/OA-15439/S/1/datasetView.do](https://data.seoul.go.kr/dataList/OA-15439/S/1/datasetView.do) (서울 열린데이터광장)

연도별 침수흔적도: [https://data.seoul.go.kr/dataList/OA-15636/F/1/datasetView.do](https://data.seoul.go.kr/dataList/OA-15636/F/1/datasetView.do) (서울 열린데이터광장)

자연재해위험개선지구(침수지구) 현황 CSV: [https://data.seoul.go.kr/dataList/OA-21693/S/1/datasetView.do](https://data.seoul.go.kr/dataList/OA-21693/S/1/datasetView.do) (서울 열린데이터광장)

서울시 강우량계 위치데이터: [https://data.seoul.go.kr/dataList/OA-22824/F/1/datasetView.do](https://data.seoul.go.kr/dataList/OA-22824/F/1/datasetView.do) (서울 열린데이터광장)

서울시 방재기상관측(AWS) 지역구별 과거 자료: [https://data.kma.go.kr/data/grnd/selectAwsRltmList.do](https://data.kma.go.kr/data/grnd/selectAwsRltmList.do) (기상청 기상자료개방포털)

서울 자치구별 총종사자수 · 사업체현황(산업대분류별/동별) 통계: [https://data.seoul.go.kr/dataList/104/S/2/datasetView.do](https://data.seoul.go.kr/dataList/104/S/2/datasetView.do) (서울 열린데이터광장 통계)

취약계층 ZIP 구성 참고 — 고령자현황: [https://data.seoul.go.kr/dataList/10730/S/2/datasetView.do](https://data.seoul.go.kr/dataList/10730/S/2/datasetView.do) (서울 열린데이터광장 통계)

취약계층 ZIP 구성 참고 — 국민기초생활보장 수급자: [https://data.seoul.go.kr/dataList/1/S/2/datasetView.do](https://data.seoul.go.kr/dataList/1/S/2/datasetView.do) (서울 열린데이터광장 통계)

취약계층 ZIP 구성 참고 — 장애인 현황(장애유형별/동별): [https://data.seoul.go.kr/dataList/10577/S/2/datasetView.do](https://data.seoul.go.kr/dataList/10577/S/2/datasetView.do) (서울 열린데이터광장 통계)

취약계층 ZIP 구성 참고 — 지하·반지하 주택(자치구별 정리 등): [https://www.si.re.kr/bbs/view.do?key=2024100042&pstSn=2209130001](https://www.si.re.kr/bbs/view.do?key=2024100042&pstSn=2209130001) (서울연구원 인포그래픽+ · 건축물대장·열린데이터 기반 해설)
