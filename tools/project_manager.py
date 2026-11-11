import io
import re
import shutil
import zipfile
from pathlib import Path

from database import db
from tools.file_manager import FileManager

ROOT = Path("workspaces")


def _slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9_-]+", "-", name.lower()).strip("-") or "project"


def create_project(name: str) -> int:
    base = _slugify(name)
    slug, n = base, 2
    while (ROOT / slug).exists():
        slug = f"{base}-{n}"
        n += 1
    (ROOT / slug).mkdir(parents=True)
    return db.create_project(name.strip(), slug)


def project_dir(project: dict) -> Path:
    return ROOT / project["slug"]


def delete_project(project_id: int) -> None:
    project = db.get_project(project_id)
    if project:
        shutil.rmtree(project_dir(project), ignore_errors=True)
        db.delete_project(project_id)


def zip_bytes(project: dict) -> bytes:
    fm = FileManager(project_dir(project))
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for rel in fm.list_files():
            z.write(fm.root / rel, rel)
    return buf.getvalue()
