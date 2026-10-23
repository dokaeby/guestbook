"""로컬/호스팅 콘솔 관리: python manage.py usage | backup | delete ID"""
import argparse
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DB = ROOT / "data" / "guestbook.sqlite3"


def main():
    parser = argparse.ArgumentParser(description="방명록 저장 용량 확인 / 백업 / 관리자 삭제")
    parser.add_argument("command", choices=["usage", "backup", "delete"])
    parser.add_argument("id", type=int, nargs="?")
    args = parser.parse_args()
    if args.command == "usage":
        total = sum(p.stat().st_size for p in ROOT.rglob("*") if p.is_file())
        print(f"프로젝트 전체: {total / 1024 / 1024:.2f} MiB (가상환경/백업 포함)")
        print(f"DB: {DB.stat().st_size / 1024:.1f} KiB" if DB.exists() else "DB: 아직 없음")
        if DB.exists():
            with sqlite3.connect(DB) as db:
                print(f"등록 글: {db.execute('SELECT COUNT(*) FROM entries').fetchone()[0]} / 1000")
        print("PythonAnywhere 전체 사용량은 Dashboard/Files에서도 확인하세요.")
    elif not DB.exists():
        parser.error("DB가 없습니다. 먼저 서버를 한 번 실행하세요.")
    elif args.command == "backup":
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        destination = DB.parent / f"backup-{stamp}.sqlite3"
        # 실행 중인 DB도 SQLite 백업 API로 일관된 복사본을 만듭니다.
        with sqlite3.connect(DB) as source, sqlite3.connect(destination) as target:
            source.backup(target)
        print(f"백업 완료: {destination}")
        print("백업은 PC에 내려받고 서버에는 필요한 소수만 보관하세요.")
    else:
        if args.id is None:
            parser.error("삭제할 글 ID를 입력하세요: python manage.py delete 1")
        with sqlite3.connect(DB) as db:
            cursor = db.execute("DELETE FROM entries WHERE id = ?", (args.id,))
        print(f"삭제한 글: {cursor.rowcount}개")


if __name__ == "__main__":
    main()
