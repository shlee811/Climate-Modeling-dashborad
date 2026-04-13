# 데이터 수집 및 전처리 정리 (프로젝트 전체)

본 문서는 이 프로젝트 폴더에 포함된 **데이터 수집(collect)** 및 **전처리/정규화/집계(preprocess)** 관련 정보를 한 곳에 모아 정리한 것입니다.  
소스별 수집 스크립트(`collectors/`), 파일 적재 스크립트(`ingest/`), DB 레이어/뷰 정의(`sql/`), 검증 쿼리(`sql/verify_*.sql`), 산출물(export 스크립트) 기준으로 구성했습니다.

> 보안/라이선스 주의  
> - `.env`, `.postgres-data/`, 로그(`logs/`), 실키(API 키), DB 비밀번호 등 **민감정보는 저장소/공유 문서에 포함하지 않습니다.**  
> - 일부 서울 열린데이터광장 데이터는 이용조건(예: 공공누리 유형)이 제한적일 수 있으니 **모델 학습/서비스 반영 전 데이터셋 페이지의 라이선스**를 확인합니다.

---

## 1. 한 줄 요약: 파이프라인 구조

이 프로젝트의 기본 흐름은 아래 레이어를 따릅니다.

- **`raw`**: API 원문(JSON) 또는 파일 원문(행 JSON/파일 메타) 보관
- **`std`**: 컬럼/타입 정규화, 관측소·격자·자치구 단위의 표준 테이블
- **`mart`**: 자치구 단위 집계/서빙 뷰(최신값/타임라인/학습 뷰 포함)
- **`ref`**: 참조/정적·준정적 데이터(침수흔적도, 위험개선지구, 취약계층, 건설공사 등)
- **`meta`**: 구–격자 매핑 등 메타데이터

핵심 기준 문서(프로젝트 내):
- `modeling handoff/README.md`: 전체 데이터 구조/컬럼/실행/라벨·학습 전처리까지 가장 자세함
- `modeling handoff/MODELING_HANDOFF.md`: 모델링 관점에서의 “학습 계약(뷰/라벨/split/누수 방지)” 요약

---

## 2. 데이터 소스(수집 대상) 요약

프로젝트가 다루는 주요 소스는 다음과 같습니다(세부는 `modeling handoff/README.md` 참고).

### 2.1 기상청(KMA) 공공데이터포털 API
- **초단기실황**: `collectors/ultra_now.py`
- **초단기예보**: `collectors/ultra_fcst.py`
- **단기예보**: `collectors/short_fcst.py`
- 공통: `core/api_client.py`, `core/parser.py`, `core/kma_time.py`, `core/config.py`

### 2.2 서울시 실시간 OpenAPI(열린데이터광장 계열)
- **서울시 강우량**: `collectors/seoul_rainfall.py` (서비스명 `ListRainfallService`)
- **서울시 하천 수위**: `collectors/seoul_river_stage.py` (서비스명 `ListRiverStageService`)

### 2.3 HSR(레이더 강수량) – KMA API Hub
- 파일 목록 조회: `collectors/hsr_file_list.py`
- 구 단위(행정구역별) 조회/적재: `collectors/hsr_district.py`
- 공통: `core/hsr_api.py`, `core/config.py`

### 2.4 서울 열린데이터광장 OA-2540 (건설공사 추진 현황)
- 수집기: `collectors/seoul_construction_progress.py`
- 특징: 실행마다 전체 스냅샷을 `ref`에 맞추도록 upsert/삭제 동기화(최신 응답에 없는 키는 제거)

### 2.5 서울 열린데이터광장 OA-15439 (내국인 생활인구 proxy, 지연 공개)
- 수집기: `collectors/seoul_living_population_korean_district_hourly.py`
- 특징: 공개 지연이 있어 **as-of reference**로만 해석(실시간 “현재 인구”로 단정 금지)
- 현재 구조: `floating_pop_korean*`는 **`mart.seoul_district_realtime_features_latest`에만 as-of 조인**됨(학습 뷰 자동 포함 아님)

### 2.6 파일 기반(수동/백필/참조) 적재
- 강우량계 위치(참조): `ingest/seoul_rain_gauge_station.py`
- AWS 지역구별 과거관측(2020~2025): `ingest/seoul_aws_district.py`
- 침수흔적도(공간): `ingest/seoul_flood_trace.py`
- 자연재해위험개선지구: `ingest/seoul_disaster_risk_zone.py`
- 자치구 총종사자수(통계 CSV): `ingest/seoul_district_worker_stats.py`
- 취약계층 밀집도(ZIP 내 4개 CSV): `ingest/seoul_vulnerable_population_district.py`
- KMA 포털 CSV 백필(“서울 초단기실황” 폴더): `ingest/portal_ultra_now_folder_loader.py` (+ 보조: `ingest/portal_ultra_now_representative_dong.py`)

---

## 3. 실행 진입점(수집/적재)

### 3.1 수집기(실시간 API)

수동 실행 예시는 `modeling handoff/README.md`의 “수동 실행 예시” 절을 따릅니다. 일반적으로:

- 프로젝트 루트에서 `PYTHONPATH=.`를 설정해 `core/` 모듈을 import 가능하게 함
- `collectors/*.py`가 `raw → std → (있으면) mart` 순으로 적재

예: `collectors/ultra_now.py`는
- KMA API 호출(`core.api_client.call_kma`)
- `raw` 저장 → `std` pivot → 구 단위 집계(`core.district_agg.aggregate_ultra_now_by_district`) 후 `mart` upsert

### 3.2 런타임 래퍼(운영 경로 기준)

- `scripts/run_collector.sh`
  - 운영 환경(로컬 경로)에서 `.env` 로딩
  - Postgres가 안 떠 있으면 `pg_ctl`로 기동 시도
  - `collectors/<name>.py` 실행

주의: 위 스크립트는 특정 로컬 경로(`~/Library/Application Support/...`)에 의존하므로, 팀 공유 시에는 우선 “프로젝트 루트에서의 수동 실행 기준”으로 맞추는 것이 안전합니다.

### 3.3 자동수집(launchd, macOS)

`launchd/*.plist`에 수집 주기 정의가 들어 있습니다. (등록 여부/주기는 `modeling handoff/README.md` “자동수집” 절 참고)

---

## 4. 입력 메타: “구–격자” 기준과 타깃 격자 목록

### 4.1 기준 파일
- `data/seoul_district_grids.csv`: 서울 25개 자치구에 대해 대표 행정동 및 KMA 격자 `(nx, ny)`를 1행씩 관리

### 4.2 코드에서의 사용
- `core/config.py`에서 `DISTRICT_GRID_MAPPING_PATH`(기본값 `data/seoul_district_grids.csv`)를 읽어
  - `target_grids`를 **CSV 기반으로 dedupe**하여 수집 대상 격자를 결정합니다.

### 4.3 DB 메타 동기화
- `sql/017_seoul_district_grid_map_resync.sql`: `meta.seoul_district_grid_map` 동기화(upsert)

격자를 바꾸면 이후 수집/집계 기준이 바뀌어 시계열이 끊길 수 있으므로, **백필/재적재 구간을 명시**하는 운영이 권장됩니다.

---

## 5. 소스별 전처리/정규화 규칙(핵심만)

아래는 “어떤 값을 어떻게 표준화해서 어떤 테이블로 넣는지” 중심의 요약입니다. 테이블/컬럼 상세는 `modeling handoff/README.md`의 “주요 컬럼 설명” 절이 정본입니다.

### 5.1 KMA 초단기실황(예: `collectors/ultra_now.py`)

- **시간 기준**: `requested_at`(수집 시각)과 별개로, KMA의 `base_date/base_time`을 `base_datetime`으로 해석  
  - `core/kma_time.get_latest_ultra_base_datetime()`는 `lag_minutes`(기본 10분, `ULTRA_NOW_LAG_MINUTES`)를 반영해 “안전한 최신 base”를 선택합니다.
- **raw 적재**: 응답 아이템 단위로 `raw.*_raw`에 `response_json` 포함 저장
- **std 정규화**: `core.parser.pivot_ultra_now()`가 category별 값을 wide 컬럼으로 pivot
- **구 단위 집계**: `core.district_agg.aggregate_ultra_now_by_district()` + 구–격자 매핑으로 집계하여 `mart` upsert

### 5.2 서울시 강우량(예: `collectors/seoul_rainfall.py`)

- **원천**: `ListRainfallService`
- **관측 시각 파싱**: `DATA_CLCT_TM`을 `observed_at`(KST tzinfo 포함)으로 변환
- **최신 슬라이스만 적재**: 응답 중 `DATA_CLCT_TM`이 가장 최신인 행들만 골라 처리
- **정규화(std)**:
  - `station_code`, `station_name`, `district_code`, `district_name`, `rain_10m_mm`, `requested_at`
- **구 집계(mart 최신)**:
  - 동일 `observed_at` + `district_name` 기준으로
  - `avg_rain_10m_mm`, `max_rain_10m_mm`, `station_count`

### 5.3 HSR(레이더 강수량)

- **lookback/lag**: 설정값(`HSR_LAG_MINUTES`, `HSR_AREA_LOOKBACK_STEPS`)으로 최신 기준시각 탐색 및 지연을 반영
- **무에코(no-echo) 처리**:
  - `-250` 같은 값이 의미상 “0강수”가 아닐 수 있어
  - 수치(`value_numeric`)와 별도로 `is_no_echo` 같은 플래그를 유지(학습/서빙 시 함께 해석 권장)

### 5.4 OA-15439 내국인 생활인구 proxy (지연 공개)

핵심 전처리 개념은 **as-of join(시점 이하 최신값)** 입니다.

- `ref.seoul_living_population_korean_district_hourly`: 자치구×시간대 원천 정규화
- `mart.seoul_district_realtime_features_latest`: 각 구의 실시간 입력 행(`base_datetime`)에 대해
  - `floating_pop_korean_observed_at <= base_datetime` 인 값 중 **가장 최근 1건**을 붙임
  - 결과 추적용으로 `floating_pop_korean_lag_hours` 등 보조 컬럼을 둠

중요: 이 값은 지연 공개 데이터이므로 “그 시각의 실제 거리 인구”가 아니라, **그 시점까지 공개되어 이용 가능한 최신 proxy**입니다.

### 5.5 파일 기반 전처리(발췌)

#### 5.5.1 취약계층 밀집도 ZIP (`ingest/seoul_vulnerable_population_district.py`)
- 입력: ZIP 내부 4개 CSV(고령자/장애인/기초생보/지하반지하)
- 공통:
  - 자치구명 정규화(공백 제거, `서울시/서울특별시` 접두 제거, 25개 구만 허용)
  - 비율(ratio)은 **0.0~1.0 소수**로 저장
- 산출: `ref.seoul_vulnerable_population_district_snapshot` (구당 1행, upsert)
  - 일부 ratio는 분모·분자 출처 시점이 다를 수 있어 해석 시 주의(문서/코드에 명시)

#### 5.5.2 총종사자수 통계 CSV (`ingest/seoul_district_worker_stats.py`)
- 3줄 헤더 구조에서 `2024/합계/총종사자수`에 해당하는 열만 추출하여 `total_worker_count`로 저장
- 산출: `ref.seoul_district_worker_stats` 및 조회용 `mart.seoul_district_worker_features`

#### 5.5.3 KMA 포털 CSV 백필 (`ingest/portal_ultra_now_folder_loader.py`)
포털 폴더 구조(구/대표동/변수별 파일)에서 초단기실황 시계열을 읽어 `std.kma_ultra_now_std`로 적재하고 `mart`까지 집계합니다.

- **파일 포맷**: “헤더+데이터”가 아니라 “파일 1개가 변수 1개 시계열”
  - 첫 줄 헤더에서 `location:nx_ny`, `Start : YYYYMMDD` 파싱
  - 데이터 줄은 `day, hour(HHMM), value`
- **인코딩/파일명 이슈 대응**:
  - `utf-8-sig / cp949 / euc-kr` 폴백 디코딩
  - macOS 한글 파일명 NFD → NFC 정규화 후 변수 매핑
- **변수 매핑(표준 슬롯)**:
  - 강수 → `rain`
  - 기온 → `temp`
  - 습도 → `humidity`
  - 풍속 → `wind_speed`
  - 풍향 → `wind_dir`
  - 강수형태 → `precip_type`
- **그룹 키(중요)**: `(district_name, nx, ny, 연도)` 단위  
  같은 구·같은 연도라도 변수별로 `(nx,ny)`가 갈라져 있을 수 있습니다.
- **현재 정책(A안)**:
  - 한 그룹에서 위 6슬롯이 모두 있어야 적재/집계
  - 하나라도 없으면 해당 그룹은 스킵(로그에 `missing=[...]`)
- **대안(B안, 문서화만 / 미구현)**:
  - 같은 구·연도 내 서로 다른 격자에 흩어진 슬롯을 병합 후 대표 격자에 맞추는 방식(해석/검증 규칙 필요)

---

## 6. 모델/학습 전처리(라벨, 누수 방지, 파생 변수)

학습 관련 핵심 계약은 `modeling handoff/README.md` 및 `modeling handoff/MODELING_HANDOFF.md`에 정리되어 있으며, DB 뷰 정의는 `sql/016_seoul_district_heavyrain_datasets.sql` 중심입니다.

### 6.1 학습 행 단위
- 기준 키: `district_name + base_datetime`
- 사용 행: `product_type = 'ultra_now'` (v1)

### 6.2 라벨(타깃) 정의
- 기본 라벨 원천: `서울시 강우량`의 구 단위 집계(`mart.seoul_rainfall_district_latest`) 중 `max_rain_10m_mm`
- 미래 창:
  - `target_rain_1h_mm`: \( (base, base+1h] \) 합
  - `target_rain_3h_mm`: \( (base, base+3h] \) 합
- 이진 라벨: `target_heavy_rain_flag` (20/40 규칙 + 리드 확장)
- 지연 관측 버퍼: 라벨 확정 시각을 `base + 3h + 20m`으로 둬 관측 지연을 흡수

### 6.3 누수 방지 원칙
- feature는 `base_datetime` 시점까지 관측 가능한 값만
- 타깃은 반드시 이후 미래 창에서 계산
- split은 랜덤이 아니라 시간 기준

### 6.4 파생 feature(공통)
`mart.seoul_district_heavyrain_trainset`(및 pending)에 파생 컬럼이 포함될 수 있습니다(정의는 handoff 문서 참조).
- `dew_point_c`, `past_rain_3h_mm`, `temp_change_3h_c`, `humidity_change_3h_pct`, `moist_energy`, `label`(alias)

---

## 7. 예외/결측/커버리지 처리 규칙(운영상 중요)

- **AWS 종로구 원천 부재**
  - “적재 오류”가 아니라 “원본 제공 없음”
  - `mart.seoul_district_model_features`에서 인접 구 평균 보간이 적용될 수 있으며, `aws_neighbor_imputed` 같은 플래그로 식별
- **AWS stale**
  - 운영 구간(2026)에서 AWS가 과거(2025)까지만 있어 `aws_lag_minutes`가 커질 수 있음
  - stale 플래그/lag를 보고 gating하거나 학습 입력에서 제외하는 정책이 필요
- **HSR no-echo(-250)**
  - 수치만 쓰면 오해 가능 → 플래그 병행
- **하천 수위 구 커버리지**
  - 수위계가 없는 구가 존재할 수 있음(coverage 한계)
  - “원천 부재 vs 일시 공백”을 구분하는 보조 컬럼(뷰에 포함)
- **ref 집계 0의 의미**
  - `0`이 “실제로 없음”인지 “원천에 미포함”인지 구분이 필요할 수 있음(특히 침수흔적도/위험지구)

---

## 8. 검증(Validation)과 운영 점검 SQL

프로젝트에는 소스별 검증 SQL이 준비되어 있습니다.

- 운영 상태 통합 점검: `sql/verify_operational_health.sql`
- 생활인구 proxy 점검: `sql/verify_seoul_living_population_korean.sql`
- 총종사자수 점검: `sql/verify_seoul_district_worker_stats.sql`
- 취약계층 점검: `sql/verify_seoul_vulnerable_population.sql`, `sql/verify_seoul_vulnerable_population_final_audit.sql`

또한 `sql/028_operational_reliability.sql` 등에서 외부 소스 수집 상태를 뷰로 모아보는 목적의 객체가 정의됩니다.

---

## 9. 산출물(Export)과 재현성

### 9.1 기본 train/valid/test export
- `scripts/export_trainset.sh`: `mart.seoul_district_heavyrain_trainset` 기반 CSV export(시간 기준 split)

### 9.2 장기 학습용(v5.1 AWS canonical)
장기(2020~2025) 고정 split 및 train/serve 전처리 일치가 필요한 경우:
- 생성 SQL: `sql/021_heavyrain_modelready_aws_v5_1_final.sql`
- 진단/게이트: `sql/021_heavyrain_modelready_aws_v5_1_diagnostics.sql`, `sql/021_heavyrain_modelready_aws_v5_1_validation_gates.sql`
- export: `scripts/export_seoul_district_heavyrain_modelready_v5_1_aws.py`

이 경로는 **district universe가 24개 구(종로구 제외)로 고정**되는 별도 계약이므로, 운영(25구) 뷰와 혼동하지 않습니다.

---

## 10. “어디를 보면 되나” 체크리스트

- **수집기 목록/실행**: `collectors/*.py`, `scripts/run_collector.sh`, `launchd/*.plist`
- **파일 적재/백필**: `ingest/*.py`
- **구–격자 기준**: `data/seoul_district_grids.csv`, `core/grid_map.py`, `sql/017_seoul_district_grid_map_resync.sql`
- **DB 레이어/뷰 정의**: `sql/*.sql` (특히 `016`, `027`, `028`)
- **검증**: `sql/verify_*.sql`
- **export**: `scripts/export_*.py`, `scripts/export_trainset.sh`

