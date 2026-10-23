# 수업 코드와 연결해서 읽기

## 읽는 순서

1. `static/index.html`: 작성 폼과 목록 영역을 찾습니다.
2. `EntryIn`: 이름과 내용의 자료형·길이 검증을 읽습니다.
3. `initialize()`: SQLite 테이블 생성문을 읽습니다.
4. `add_entry()`: 검증된 입력을 INSERT하고 201 응답을 돌려줍니다.
5. `list_entries()`: LIMIT/OFFSET으로 일부 글만 가져옵니다.
6. `static/app.js`: fetch 결과를 DOM에 표시하는 흐름을 봅니다.
7. `test_guestbook.py`: 20/21자, 500/501자, 정상/오류의 기대값을 비교합니다.

## 실제 참고한 학습 내용

| 수업 | 기존 코드/개념 | 방명록 적용 |
| --- | --- | --- |
| Day1 | `day1_practice.py`, 변수·조건·반복·함수 | 글 목록, 입력 조건, 함수 분리 |
| Day2 | 오전/오후의 Python 실습 | 자료형과 기본 제어 흐름 복습 |
| Day3 | `오후/day3-3-fixed.py` | 유효한 입력 범위 명시, 잘못된 입력 거절 |
| Day4 | `day4-1.py`의 오류 확인 연습 | 오류를 재현하고 경계값으로 확인 |
| Day6 | `ch08_project/app.py`, `models.py` | FastAPI, BaseModel, Field, HTTPException, 응답 모델 |
| Day7 | `02/main.py`의 HTTP 호출 | 브라우저 fetch 요청/응답 이해. SQLite는 동기 함수로 처리 |
| Day8 | `lesson_04_ai_test_cases`, `lesson_08_final_verification` | pytest, TestClient, 경계값, 상태 변화, 응답 검증 |

현재 저장소에는 Day5 폴더가 없습니다. SQLite와 브라우저 화면은 위 수업을 연결하기 위해 추가한 내용입니다. 수업 예제의 의도된 오류는 가져오지 않았습니다.

## 테이블은 정확히 하나

```sql
CREATE TABLE entries (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL CHECK(length(name) BETWEEN 1 AND 20),
    message TEXT NOT NULL CHECK(length(message) BETWEEN 1 AND 500),
    created_at TEXT NOT NULL,
    delete_token_hash TEXT NOT NULL
);
```

외래 키, 회원/댓글 테이블, 조인, 관계가 없습니다. `AUTOINCREMENT`를 사용하지 않아 별도의 `sqlite_sequence` 테이블도 만들지 않습니다. `id`는 삭제 뒤 재사용될 수 있지만 삭제 권한은 각 글마다 새로 만드는 무작위 키로 검사합니다. 시각은 UTC ISO 8601로 저장하고 화면에서는 접속한 브라우저의 현지 시각으로 보여 줍니다.

`sqlite3.connect()`는 서버에 접속하는 대신 파일을 엽니다. `?`는 SQL의 값 자리입니다. 사용자가 적은 내용을 SQL 문자열에 직접 붙이지 않습니다. 요청마다 연결을 만들고 닫아 스레드 사이에서 연결을 공유하지 않습니다.

## API 계약

| 메서드 | 경로 | 결과 |
| --- | --- | --- |
| GET | `/` | 방명록 HTML |
| GET | `/api/entries?page=1&page_size=10` | 200: items, total, page, page_size, capacity |
| POST | `/api/entries` | 201: id, name, message, created_at, delete_token |
| DELETE | `/api/entries/1` | 본인의 삭제 키가 맞으면 204 |
| GET | `/health` | 200: 서버 프로세스 응답 확인. DB 정상 여부까지 보장하지 않음 |

등록 본문 예:

```json
{"name": "방문자", "message": "오늘도 반갑습니다!"}
```

삭제 요청에는 `Authorization: Bearer 등록응답의_delete_token` 헤더가 필요합니다. 목록에는 삭제 키나 해시가 나오지 않습니다. 서버는 키 원문을 저장하지 않으므로 복구할 수 없습니다.

주요 오류: 입력 검증 422, 요청 크기 413, 등록 간격 429, 용량 409, 삭제 권한 403, 없는 글 404, SQLite 사용 불가 503입니다. 글 수 검사와 INSERT를 `BEGIN IMMEDIATE` 트랜잭션 안에서 수행하여 동시 요청에서도 한도를 지킵니다.

## 간단한 확인 문제

- 이름 20자는 성공하고 21자는 왜 422인가요?
- 글을 쓴 후 서버를 재시작해도 남아 있는 이유는 무엇인가요?
- SQL 문자열 결합 대신 `?`를 쓰는 이유는 무엇인가요?
- GET 목록에 삭제 키를 넣으면 어떤 문제가 생길까요?
- 무료 서버가 DB 파일을 지우는 환경이라면 코드가 정상이어도 글이 사라질까요?
