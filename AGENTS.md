# AGENTS.md

## 1) 프로젝트 목적/범위
- 이 프로젝트는 `SQLAlchemy` 트랜잭션 동작을 예측 가능하게 제공하는 것을 목표로 한다.
- 구현 편의보다 `testability(테스트 용이성)`를 우선한다.
- 기능 추가/수정 시, 동작을 설명할 수 있는 테스트를 함께 유지한다.
- 이 프로젝트는 FastAPI + SQLAlchemy async를 실무에서 사용하는 개발자를 대상으로 하며, Python/FastAPI/SQLAlchemy 입문 튜토리얼은 제공하지 않는다.

## 2) 내부 구조 규약
- 내부 구현은 `internal/` 폴더로 분리한다.
- `internal/`은 import 가능한 경로로 유지해 테스트 용이성을 확보한다.
- `internal/`을 제외한 나머지 경로는 `public API`로 본다.
- `internal_*` 같은 접두사 네이밍은 사용하지 않는다.
- 내부 로직이 커지면 `internal/` 아래 파일을 분리해 책임을 나눈다.
- `internal/*`는 테스트 가능한 공개 경로이지만, 안정 API로 간주하지 않는다.

## 3) 코딩 규약
- 함수는 작게 만든다.
- 한 함수는 한 가지 책임만 가진다.
- 분기(`if/elif`)가 길어지면 작은 함수로 분리한다.
- 테스트가 어려운 큰 함수보다, 테스트 쉬운 작은 함수를 선호한다.

## 4) 테스트 규약
- 버그 수정/기능 추가 시 테스트를 반드시 추가하거나 갱신한다.
- 테스트는 가능한 한 public 경로를 우선 검증한다.
- 커버리지 채우기만 위한 테스트보다, 동작 보장을 위한 테스트를 작성한다.
- 커버리지 기준은 `pyproject.toml` 설정을 따른다.
- Quick Start 보장은 README 문자열 비교가 아니라, 예제와 동등한 시나리오를 실행 테스트로 검증한다.

## 5) README/퀵스타트 규약
- README는 PyPI 독자 관점에서 빠르게 이해되도록 작성한다.
- README는 사용자에게 필요한 사용법 중심으로 간결하게 작성한다.
- Quick Start는 "요청 경계 설정 -> 서비스 계층 트랜잭션 선언 -> 라우트 호출" 흐름으로 보여준다.
- README에는 내부 테스트/검증 방식 설명을 넣지 않는다(필요 시 기여 문서에서만 다룬다).

## 6) 작업/검증 규약
- 검증 명령은 직접 복제하지 말고 `scripts/` 스크립트만 사용한다.
- 일반 변경 검증 순서:
1. `scripts/check.sh`
2. `scripts/test.sh`
- 테스트 축은 `RUN_MIN_SQLALCHEMY_TEST` 환경변수로 제어한다.
- 로컬 기본값은 `RUN_MIN_SQLALCHEMY_TEST=0`, CI는 `RUN_MIN_SQLALCHEMY_TEST=1`로 고정한다.
- 배포 직전 빌드/검증은 `scripts/build-dist.sh`를 사용한다.
- `scripts/build-dist.sh`는 인자 없이 실행하며 항상 클린 빌드(`uv build --clear`)를 수행한다.

## 7) 릴리즈 규약
- 릴리즈 버전업/커밋/태깅은 `scripts/release-commit.sh`로만 수행한다.
- `scripts/release-commit.sh`는 인자 없이 실행한다(기본 동작: patch bump).
- 특정 버전 릴리즈는 `RELEASE_VERSION` 환경변수로만 지정한다.
- 예: `RELEASE_VERSION=1.0.0 scripts/release-commit.sh`
- `scripts/release-commit.sh`는 `pyproject.toml` 버전 갱신 후 `uv lock`을 실행하고, `pyproject.toml`/`uv.lock` 릴리즈 커밋과 `vX.Y.Z` 태그 생성까지 수행한다.
- 푸시(`git push`, `git push --tags`)는 자동 실행하지 않고 사람이 최종 확인 후 수동 실행한다.

## 8) 커밋 규약
- 커밋은 작고 명확하게 나눈다.
- 커밋 메시지는 변경 의도를 드러내게 작성한다.
- 동작 변경이 있으면 테스트와 문서를 같이 업데이트한다.

## 9) 문서 동기화 규약
- 프로젝트 방향/구조/규약이 바뀌면 `AGENTS.md`를 같은 변경에서 함께 업데이트한다.
