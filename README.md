# 작은 방명록

Day1~Day8 학습 내용을 연결한 소규모 방명록입니다. 코드는 `Day8/guestbook`에만 추가했으며 기존 수업 예제는 수정하지 않았습니다. 현재 저장소에는 Day5 폴더가 없어 Day5 코드를 참고했다고 주장하지 않습니다.

- FastAPI + Pydantic: Day6~Day8의 요청 검증과 API 응답 모델
- Python 내장 `sqlite3`: DB 서버·ORM·외부 DB 계정 없이 파일 하나에 저장
- HTML/CSS/JavaScript: 이름과 인사 등록, 최신순 조회, 페이지 이동, 내 글 삭제
- pytest + TestClient: Day8의 정상·오류·경계값 검증
- 외부 API, 광고, 유료 기능, 이미지 업로드, 로그인, 다른 테이블과의 관계 없음

## Windows에서 실행

Python 3.12 이상을 권장합니다. 실제 검증 환경은 Python 3.13.14입니다. PowerShell에서:

```powershell
cd C:\Users\Playdata\aio4\ai4_section01\Day8\guestbook
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --no-cache-dir -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8765 --workers 1
```

설치된 Python이 3.12라면 첫 명령의 `-3.13`을 `-3.12`로 바꾸세요. `py`를 찾지 못하면 Python 설치 후 터미널을 다시 열거나 설치된 Python 실행 파일의 경로를 사용하세요. 가상환경 활성화는 필요 없습니다.

- 화면: <http://127.0.0.1:8765>
- Swagger API 실습: <http://127.0.0.1:8765/docs>
- 종료: 터미널에서 `Ctrl+C`
- DB: 최초 실행 때 `data/guestbook.sqlite3` 자동 생성. 재실행해도 유지됩니다.
- 포트 사용 중이면 `--port 8766`처럼 바꾸고 브라우저 주소도 바꾸세요.

## 테스트

```powershell
.\.venv\Scripts\python.exe -m pip install --no-cache-dir -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q test_guestbook.py
.\.venv\Scripts\python.exe -m pip check
```

이 프로젝트 폴더의 테스트만 실행하세요. 수업 전체에는 의도적으로 실패하도록 만든 예제가 있습니다. `requirements.txt`는 운영용, `requirements-dev.txt`는 개발용입니다. 상위 수업 환경과 버전을 섞지 않도록 별도 가상환경을 권장합니다. 버전 고정은 검증 재현용이며 보안 업데이트까지 자동으로 보장하는 잠금 파일은 아닙니다.

## 사용 규칙과 용량

| 항목 | 설정 |
| --- | --- |
| 이름 | 공백 제거 후 1~20자 |
| 내용 | 공백 제거 후 1~500자 |
| 전체 글 | 최대 1,000개, 초과 시 409 응답. 오래된 글을 자동 삭제하지 않음 |
| 목록 | 기본 10개, 한 번에 최대 20개 |
| 요청 본문 | 최대 8 KiB, 초과 시 413 응답 |
| DB 본체 | SQLite 페이지 제한으로 최대 16 MiB |
| 등록 간격 | 전체 방문자 기준 3초, 초과 시 429 응답 |
| 서버 프로세스 | 1개. 간격 제한은 이 프로세스의 메모리에 유지됨 |

등록 간격은 서버 재시작 때 초기화됩니다. 접속자별 차단이나 완전한 봇 방지 기능은 아닙니다. 공개 대규모 서비스의 처리량을 보장하지 않습니다. 16 MiB는 DB 본체 제한으로, 트랜잭션 저널·백업·가상환경·로그는 별도 용량을 사용합니다. 따라서 무료 계정 전체 사용량도 확인해야 합니다.

삭제는 글을 쓴 브라우저에서만 가능합니다. 서버가 만든 무작위 삭제 키를 브라우저 `localStorage`에 저장하고 DB에는 해시만 보관합니다. 다른 기기, 시크릿 모드 종료, 브라우저 데이터 삭제 후에는 키가 없어 직접 삭제할 수 없습니다. 공용 PC에서는 같은 브라우저 사용자가 삭제할 수 있습니다. 관리자는 호스팅 콘솔에서 `python manage.py delete 글번호`로 삭제할 수 있습니다.

사용자 입력은 SQL 매개변수로 전달하며 화면에는 `textContent`로 출력합니다. 이름·내용은 모든 방문자에게 공개되므로 개인정보를 적지 마세요.

## 파일 안내

| 파일 | 역할 |
| --- | --- |
| `main.py` | 단일 테이블, SQLite 연결, 검증 모델, API, 요청 크기 제한 |
| `static/` | 반응형 한국어 화면, 스타일, fetch 호출 |
| `test_guestbook.py` | 동작·경계값·동시 쓰기·저장 유지 테스트 |
| `manage.py` | 용량 확인, SQLite 백업, 관리자 삭제 |
| `DEPLOY.md` | 무료 사이트 비교 및 PythonAnywhere 배포 명령 |
| `CODE_GUIDE.md` | 학습 코드 연결, 테이블 구조, API 설명 |
| `VERIFICATION.md` | 실제 검증 결과와 남은 검증 범위 |
| `package.py` | DB·가상환경을 제외한 업로드 ZIP 생성 |

## 무료 배포

**PythonAnywhere Beginner 무료 계정 + FastAPI ASGI 실험 기능**을 배포 대상으로 조사했습니다. SQLite 파일을 사용할 수 있지만 ASGI 지원과 장기 요금은 실험 단계이므로, 계정에서 무료 사용 가능 여부를 확인한 뒤 진행해야 합니다. 무료 지속 운영을 보장하는 서비스로 표현하지 않습니다.

현재 Render 무료 인스턴스는 재시작·휴면·재배포 시 로컬 SQLite 변경분이 사라집니다. 데이터 보존이 필요한 이 프로젝트의 기본 배포처로 사용하지 않습니다.

가입부터 업로드, 실행, 확인, 백업까지는 [DEPLOY.md](DEPLOY.md)를 따라 하세요. 여기서는 실제 외부 계정 생성이나 공개 배포를 수행하지 않았습니다.
