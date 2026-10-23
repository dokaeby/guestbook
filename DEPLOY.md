# 무료 배포 안내

확인일: **2026-10-23**. 아래 내용은 공식 문서를 조회해 작성했습니다. 서비스의 무료 정책은 바뀔 수 있으며 계정의 실제 표시 조건이 우선합니다.

## 사이트 비교

| 사이트 | 무료 조건/저장 특성 | 이 프로젝트 판단 |
| --- | --- | --- |
| [PythonAnywhere](https://www.pythonanywhere.com/pricing/) | Beginner $0, 앱 1개·워커 1개·512 MiB. SQLite 사용 가능 | 소규모 실습용 후보. FastAPI의 ASGI 배포는 별도 실험 기능으로 조건 확인 필요 |
| [Render](https://render.com/docs/free) | 무료 웹 서비스가 있으나 로컬 파일 변경은 휴면·재시작·재배포 시 유실, 무료 영구 디스크 없음 | SQLite 글 보존 조건과 맞지 않아 권장하지 않음 |

PythonAnywhere의 [무료 계정 안내](https://help.pythonanywhere.com/pages/FreeAccountsFeatures/)에는 앱의 만료 기간이 1개월로 기재되어 있습니다. [2026년 변경 안내](https://blog.pythonanywhere.com/221/)도 확인하고, 계정의 만료 표시·연장 방법을 확인하세요. ASGI 앱 관리 UI는 별도이므로 일반 Web 탭의 동작이 그대로 적용된다고 가정하지 마세요. 만료 전에 갱신 가능 여부를 확인하고 백업하세요.

[요금 설명](https://www.pythonanywhere.com/pricing/)상 CPU 100초/일은 콘솔·작업에 관한 한도이며 일반 웹앱 방문 처리의 하루 100초 한도라는 뜻은 아닙니다. 무료 계정의 웹 워커와 대역폭은 제한됩니다. 정량적인 방문자 수 보장은 없습니다.

## FastAPI 배포에 관한 전제

[공식 ASGI 배포 문서](https://help.pythonanywhere.com/pages/ASGICommandLine/)는 FastAPI를 지원하지만 **실험 기능이며 장기 가격 미확정, 정적 파일 매핑 미지원, 제한적인 관리 UI**라고 명시합니다. 따라서 아래는 현재 공식 절차에 맞춘 배포 방법이지, 영구 무료나 계정별 배포 성공 보장이 아닙니다.

이 프로젝트는 FastAPI가 `/static` 파일을 직접 제공하므로 정적 파일 매핑이 필요 없습니다. WSGI 설정 파일에 `from main import app as application`을 넣으면 동작하지 않습니다. FastAPI는 ASGI 앱이므로 아래 Uvicorn 방식을 사용합니다. 계정에서 ASGI 무료 기능이 허용되지 않거나 유료 전환을 요구하면 진행을 멈추고 로컬에서 실행하세요. 유료 플랜을 선택하거나 DB를 임시 파일 시스템으로 옮길 필요는 없습니다.

## 1. 업로드 ZIP 준비 (Windows PowerShell)

```powershell
cd C:\Users\Playdata\aio4\ai4_section01\Day8\guestbook
.\.venv\Scripts\python.exe package.py
```

`guestbook-upload.zip`에는 실행 코드·화면·설명만 들어갑니다. DB, 백업, 가상환경, `.git`, 테스트 패키지는 넣지 않습니다. 로컬에 쓴 글은 새 배포로 옮겨지지 않습니다.

## 2. 무료 계정과 파일 업로드

1. [가입 화면](https://www.pythonanywhere.com/pricing/)에서 **Create a Beginner account**를 선택합니다. 유료 Developer 계정을 고르지 마세요.
2. Files에서 `/home/사용자명/guestbook` 폴더를 만들고 ZIP을 업로드합니다.
3. Consoles에서 Bash 콘솔을 열고 압축을 풉니다.

```bash
cd ~/guestbook
unzip guestbook-upload.zip
ls
```

`main.py`, `requirements.txt`, `static`이 바로 보여야 합니다. `guestbook/guestbook/main.py`처럼 한 단계 더 들어가 있다면 실제 `main.py`가 있는 경로를 이후 명령에 사용하세요.

## 3. 운영 의존성만 설치

PythonAnywhere 콘솔의 `python3.13 --version`으로 버전을 확인합니다. 없다면 `python3.12`로 아래의 두 곳을 바꿉니다.

```bash
python3.13 -m venv ~/.virtualenvs/guestbook
~/.virtualenvs/guestbook/bin/python -m pip install --no-cache-dir -r ~/guestbook/requirements.txt
~/.virtualenvs/guestbook/bin/python -m pip check
```

호스팅에는 `requirements-dev.txt`를 설치하지 않습니다. `uvicorn[standard]`, 개발 도구, AI 라이브러리도 필요 없습니다. DB인 `sqlite3`는 Python에 내장되어 따로 설치하지 않습니다.

## 4. ASGI 관리 도구와 토큰

계정의 Account → API token에서 토큰을 생성합니다. 공식 안내에 따르면 생성 후 Bash 콘솔의 관리 도구가 사용할 수 있습니다. 토큰을 소스·ZIP·채팅·Git에 복사하지 마세요.

별도 가상환경에 관리 도구를 설치합니다. 앱 패키지 버전과 섞이지 않습니다.

```bash
python3.13 -m venv ~/.virtualenvs/pa-tools
~/.virtualenvs/pa-tools/bin/python -m pip install --no-cache-dir pythonanywhere
~/.virtualenvs/pa-tools/bin/pa website --help
```

## 5. 웹사이트 생성

아래의 `YOURUSERNAME`을 **모두** 실제 사용자명으로 바꾸세요. 미국 서비스 기준이며 EU 계정은 도메인을 `YOURUSERNAME.eu.pythonanywhere.com`으로 바꿉니다. 이미 같은 도메인의 앱이 있으면 중복 생성하거나 기존 앱을 삭제하지 말고 설정을 먼저 확인하세요.

```bash
~/.virtualenvs/pa-tools/bin/pa website create --domain YOURUSERNAME.pythonanywhere.com --command '/home/YOURUSERNAME/.virtualenvs/guestbook/bin/uvicorn --app-dir /home/YOURUSERNAME/guestbook --uds ${DOMAIN_SOCKET} main:app --workers 1 --no-access-log'
```

**작은따옴표와 `${DOMAIN_SOCKET}`는 그대로 둡니다.** 호스팅 서버가 실제 소켓 경로를 주입합니다. Bash에서 미리 치환하면 안 됩니다. Windows 로컬 명령에 이 소켓 옵션을 사용하지 마세요. 배포 명령을 Bash에서 직접 실행해 서버를 계속 켜 두는 방식도 사용하지 않습니다.

이 명령은 공개 웹앱을 만듭니다. 기존 사용자 글이나 개인정보가 든 DB를 업로드하지 않았는지 확인한 후 실행하세요.

## 6. 실제 확인

```bash
~/.virtualenvs/pa-tools/bin/pa website get --domain YOURUSERNAME.pythonanywhere.com
```

브라우저에서 `https://YOURUSERNAME.pythonanywhere.com`을 열어 다음을 확인합니다.

1. 한국어 화면과 스타일이 표시됩니다.
2. 인사를 하나 등록하면 목록에 표시됩니다.
3. 새로고침 후에도 글이 남아 있습니다.
4. 아래 reload 실행 후에도 남아 있습니다.
5. 같은 브라우저에서 내 글 삭제가 됩니다.

```bash
~/.virtualenvs/pa-tools/bin/pa website reload --domain YOURUSERNAME.pythonanywhere.com
```

에러가 나면 `pa website get`에 나온 error/server log 경로를 확인하세요. ASGI 앱은 일반 Web 탭에서 보이지 않을 수 있습니다. 이 문서 작성 과정에서는 실제 계정의 배포·갱신·HTTPS 연결을 검증하지 않았습니다.

## 7. 무료 한도 점검

앱에는 글 1,000개, 내용 500자, DB 본체 16 MiB, 요청 8 KiB 제한이 있습니다. 글이 가득 차면 새 글을 거절하며 자동 유료 확장을 요청하지 않습니다. 3초 등록 간격은 프로세스 1개 기준이며 재시작하면 초기화됩니다.

하지만 무료 디스크에는 **관리 도구·앱 가상환경·캐시·백업·저널**도 포함됩니다. 글 제한만으로 계정 전체의 512 MiB를 보장할 수는 없습니다. 설치 뒤와 운영 중 Dashboard/Files의 전체 사용량을 확인하세요.

```bash
~/.virtualenvs/guestbook/bin/python ~/guestbook/manage.py usage
du -sh ~/guestbook ~/.virtualenvs/guestbook ~/.virtualenvs/pa-tools
du -hs /tmp ~/.[!.]* ~/* 2>/dev/null
```

운영 기준으로 전체 350 MiB 이하를 목표로 잡아 여유를 둡니다. 이 수치는 앱 운영상의 보수적인 목표이며 호스팅 업체의 별도 무료 한도가 아닙니다. 한도에 가까우면 필요 없는 ZIP·옛 백업을 PC로 내려받은 뒤 Files에서 해당 파일만 정리하세요. 유료 업그레이드 없이도 쓰기 실패나 서비스 제한이 발생할 수 있습니다. 트래픽·실행 시간은 코드 크기만으로 상한을 보장할 수 없습니다.

## 8. 백업과 관리자 삭제

```bash
~/.virtualenvs/guestbook/bin/python ~/guestbook/manage.py backup
~/.virtualenvs/guestbook/bin/python ~/guestbook/manage.py delete 12
```

백업은 `data/backup-날짜.sqlite3`에 생성됩니다. Files에서 PC로 내려받고 서버에는 소수만 보관하세요. 삭제 명령은 지정한 글을 즉시 삭제하므로 ID를 먼저 확인하세요. 실행 중인 DB를 단순 파일 복사하는 대신 백업 명령을 사용하세요.

복원은 앱을 중지한 상태에서 현재 DB를 별도로 보관하고, 정상 백업을 `data/guestbook.sqlite3`로 교체한 뒤 앱을 재시작하는 방식입니다. 호스팅의 앱 중지 방법은 최신 관리 도구 도움말을 확인하세요. 코드만 다시 업로드할 때 `data`를 덮어쓰거나 삭제하지 않습니다.

## 공식 출처

- [가격 및 무료 가입](https://www.pythonanywhere.com/pricing/)
- [무료 계정 기능](https://help.pythonanywhere.com/pages/FreeAccountsFeatures/)
- [DB 종류와 SQLite](https://help.pythonanywhere.com/pages/KindsOfDatabases/)
- [ASGI/FastAPI 배포 절차와 실험 기능 제한](https://help.pythonanywhere.com/pages/ASGICommandLine/)
- [계정 디스크 용량](https://help.pythonanywhere.com/pages/DiskQuota/)
- [2026년 무료 계정 변경](https://blog.pythonanywhere.com/221/)
- [Render 무료 서비스의 파일 유실 조건](https://render.com/docs/free)
