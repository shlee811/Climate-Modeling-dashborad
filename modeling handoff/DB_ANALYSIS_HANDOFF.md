# DB Analysis Handoff

학습용 데이터셋은 별도 전달본을 본다. 여기서는 **접속 정보·핵심 객체·해석 주의**만 정리한다.

## 참고: 호스트 공인 IP (인터넷에서 직접 TCP로 붙을 때 `DB_HOST` 후보)

문서에 반영한 시점에 조회한 값: **`220.65.183.139`**  
통신사·공유기·VPN에 따라 바뀔 수 있다. 같은 망(사설 IP)으로 붙을 때는 이 주소가 아니라 맥의 사설 IP를 쓴다.

## 팀원이 접속한다고 연락 오면, 호스트가 알려줄 것

1. 접속 방식: 같은 Wi‑Fi(사설 IP) / SSH 터널 / 공인 IP 직접 TCP 중 무엇인지.
2. `DB_HOST`·`DB_PORT`·(SSH 시) 터널 명령 한 줄. IP는 변할 수 있으니 필요 시 호스트가 다시 확인.
3. `DB_NAME` `weather`, 사용자 `BK`, 비밀번호 `smu2026`(내부용·외부 유출 금지).
4. 외부에서 직접 붙는 경우: 맥/공유기에서 Postgres 포트가 열려 있는지 등 **네트워크 쪽은 호스트에게 확인**.

팀원은 접속 직전에 위를 호스트에게 확인한다. 위 공인 IP는 참고용이며, 안 붙거나 오래 지났으면 호스트가 다시 알려 준다.

## 계정·DB 이름

- 사용자: `BK` (대소문자 그대로)
- 비밀번호: `smu2026`
- 데이터베이스: `weather`
- 포트: 직접 접속 시 보통 `5432`

## 연결 방법

로컬에서 `.env`를 쓸 때는 `set -a`, `source .env`, `set +a` 후 `psql`을 쓴다.

호스트 PC에서 본인만 쓸 때:

```bash
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME"
```

SSH 터널(팀원이 호스트 맥의 Postgres에 붙을 때). 터널을 연 터미널은 끊지 않는다.

```bash
ssh -L 5433:localhost:5432 호스트사용자명@호스트주소
```

팀원 `.env` 예: `DB_HOST=localhost`, `DB_PORT=5433`, `DB_NAME=weather`, `DB_USER=BK`, `DB_PASSWORD=smu2026`.

직접 TCP로 인터넷에서 붙을 때 `.env` 예: `DB_HOST=220.65.183.139`, `DB_PORT=5432`, `DB_NAME=weather`, `DB_USER=BK`, `DB_PASSWORD=smu2026`. (주소는 위 참고 절과 동일·변동 가능.) `listen_addresses`, `pg_hba`, 방화벽·포트 개방은 호스트가 맞춘다. 가능하면 SSH나 VPN을 우선한다.

공용 RDS 등이면 인프라에서 받은 호스트·포트·계정을 쓴다. 대문자 역할은 `CREATE ROLE "BK" ...`처럼 따옴표로 만든다. (역할·권한 예시는 README 14-1절.)

## 연결 확인

```sql
SELECT current_database(), current_user, inet_server_addr(), inet_server_port();
```

## 자주 막히는 경우

- Connection refused: Postgres 기동, 호스트/포트, 터널 유지 여부.
- password authentication failed: 사용자 `BK` 철자, 비밀번호.
- 외부에서 안 됨: 호스트·공유기·방화벽·포트 설정을 호스트에게 확인.

Windows는 WSL·Git Bash에서 동일하게 쓴다.

## 스키마 흐름 (한 줄)

`raw` → `std` → `mart`(구 단위 집계·뷰), `ref`(참조·준정적), `meta`(구–격자 등). KMA·강우·하천·HSR·AWS 등은 같은 패턴으로 적재된다.

## 지금 바로 보면 되는 객체

| 객체 | 용도 |
|------|------|
| `mart.seoul_district_model_features` | 시점별 와이드 입력(침수·위험지구·강우계 수·취약계층 9컬럼 등) |
| `mart.seoul_district_realtime_features_latest` | 구별 최신 서빙용. `floating_pop_korean*`만 여기에 붙음 |
| `mart.seoul_vulnerable_population_district_latest` | 취약계층 구 단위 최신 스냅 |
| `mart.seoul_district_worker_features` | 총종사자수 등 worker 쪽 피처 |
| `ref.seoul_construction_progress_summary` | 건설 OA-2540 요약(모델 와이드에는 컬럼으로 안 붙음) |
| `mart.kma_hsr_area_district_latest` | HSR 구 단위 최신 등(운영 점검·조인 시) |

25구가 universe. AWS 원천은 24구(종로 원본 없음)이고 모델 뷰에서 이웃 보간이 들어갈 수 있다.

학습 뷰 `mart.seoul_district_heavyrain_trainset` 등은 운영·디버깅 참고용이고, 학습 계약은 별도 전달본을 본다.

## `model_features`에 들어 있고, 안 들어 있는 것

| 들어 있음 | 안 들어 있음 |
|-----------|----------------|
| 침수흔적·위험개선지구 집계, `rain_gauge_current_count`, 취약계층 9컬럼 | `floating_pop_korean*`(realtime만), `total_worker_count` → `mart.seoul_district_worker_features`, 건설공사 컬럼 → `ref` 별도 |

## 해석 주의

- **하천 수위**는 구 full coverage가 아니다. 침수·위험지구도 원천이 비어 있으면 집계 0과 “없음”을 혼동하지 말 것.
- **AWS**는 stale 가능(`aws_lag_minutes`, `aws_operational_stale_flag`).
- **생활인구 proxy**는 공개 지연·as-of(`floating_pop_korean_lag_hours`).
- **취약계층** 일부 ratio는 출처 연도가 섞여 있다.
- **`vulnerability_score`** 합성 컬럼은 미구현.

## 컬럼 정본

README.md 5절(주요 컬럼 설명). 뷰 정의는 `sql/027_seoul_district_model_features_v2.sql`, `sql/016_seoul_district_heavyrain_datasets.sql` 등.

DB에서 메타데이터만 볼 때:

```sql
SELECT table_schema, table_name, ordinal_position, column_name, data_type
FROM information_schema.columns
WHERE table_schema IN ('raw', 'std', 'mart', 'ref', 'meta')
  AND table_name IN (
    'seoul_district_model_features',
    'seoul_district_realtime_features_latest',
    'seoul_district_heavyrain_trainset'
  )
ORDER BY table_schema, table_name, ordinal_position;
```

## 샘플 쿼리 (복붙 시 빨리 끝나는 것만)

`mart.seoul_district_model_features`는 행 수가 크므로, **최신 `base_datetime`은 적재 테이블 `mart.seoul_district_ultra_now`에서만** 가져온 뒤 `model_features`를 좁힌다. (`ultra_now`가 비어 있으면 0행이 나올 수 있음 → 호스트에게 적재 상태 확인.)

```sql
-- 구별 최신 서빙 뷰(대략 25행)
SELECT district_name, base_datetime, precip_mm, floating_pop_korean
FROM mart.seoul_district_realtime_features_latest
ORDER BY district_name;

-- model_features 맛보기: ultra_now의 최신 시각 1개만 기준으로 제한
SELECT m.district_name, m.base_datetime, m.target_datetime, m.precip_mm
FROM mart.seoul_district_model_features m
WHERE m.base_datetime = (SELECT MAX(base_datetime) FROM mart.seoul_district_ultra_now)
ORDER BY m.district_name
LIMIT 30;

SELECT * FROM mart.seoul_vulnerable_population_district_latest ORDER BY district_name LIMIT 15;

SELECT district_name, base_year, total_worker_count
FROM mart.seoul_district_worker_features
ORDER BY district_name;

SELECT * FROM ref.seoul_construction_progress_summary LIMIT 20;
```

적재·coverage 빠른 확인(`ultra_now`는 시각×구 단위로 행 수가 작다):

```sql
SELECT MAX(base_datetime) AS latest_ultra_now FROM mart.seoul_district_ultra_now;

SELECT COUNT(*) AS rows_at_latest
FROM mart.seoul_district_ultra_now
WHERE base_datetime = (SELECT MAX(base_datetime) FROM mart.seoul_district_ultra_now);
```

## 공유 시

`.env` 실키와 본 문서를 공개 저장소·공개 채널에 올리지 말 것.
