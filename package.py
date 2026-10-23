"""실행: python package.py. 운영 파일만 포함한 업로드 ZIP을 만듭니다."""
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parent
FILES = ["main.py", "manage.py", "moderation.py", "moderation.json", "requirements.txt", "README.md", "DEPLOY.md", "CODE_GUIDE.md", "ASSETS.md"]


def main():
    archive = ROOT / "guestbook-upload.zip"
    with ZipFile(archive, "w", compression=ZIP_DEFLATED) as bundle:
        for name in FILES:
            bundle.write(ROOT / name, name)
        for path in sorted((ROOT / "static").rglob("*")):
            if path.is_file():
                bundle.write(path, path.relative_to(ROOT).as_posix())
    print(f"업로드 ZIP: {archive.name} ({archive.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
