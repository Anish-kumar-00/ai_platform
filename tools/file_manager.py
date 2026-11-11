import io
import shutil
import zipfile
from pathlib import Path

HIDDEN_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv"}
MAX_READ = 300_000
MAX_WRITE = 2_000_000
MAX_ZIP_TOTAL = 50_000_000


class FileError(Exception):
    """Safe, user-friendly file error."""


class FileManager:
    """All file access for one project, locked inside its root folder."""

    def __init__(self, root):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _safe(self, rel: str) -> Path:
        rel = (rel or "").strip().replace("\\", "/").lstrip("/")
        if not rel:
            raise FileError("Path is empty.")
        p = (self.root / rel).resolve()
        if self.root not in p.parents:
            raise FileError("Path is outside the project.")
        if any(part in HIDDEN_DIRS for part in p.relative_to(self.root).parts):
            raise FileError("That folder is not allowed.")
        return p

    def exists(self, rel: str) -> bool:
        return self._safe(rel).exists()

    def list_files(self) -> list:
        out = []
        for p in sorted(self.root.rglob("*")):
            rel = p.relative_to(self.root)
            if any(x in HIDDEN_DIRS for x in rel.parts):
                continue
            if p.is_file():
                out.append(rel.as_posix())
        return out

    def tree(self) -> str:
        lines, seen = [], set()
        for f in self.list_files():
            parts = f.split("/")
            for i in range(len(parts) - 1):
                d = "/".join(parts[: i + 1])
                if d not in seen:
                    seen.add(d)
                    lines.append("  " * i + parts[i] + "/")
            lines.append("  " * (len(parts) - 1) + parts[-1])
        return "\n".join(lines)

    def read(self, rel: str) -> str:
        p = self._safe(rel)
        if not p.is_file():
            raise FileError("File not found.")
        if p.stat().st_size > MAX_READ:
            raise FileError("File is too large to edit here.")
        try:
            return p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            raise FileError("Binary file - cannot be edited as text.")

    def write(self, rel: str, content: str) -> None:
        if len(content.encode("utf-8")) > MAX_WRITE:
            raise FileError("Content too large.")
        p = self._safe(rel)
        if p.is_dir():
            raise FileError("A folder with this name already exists.")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")

    def write_bytes(self, rel: str, data: bytes) -> None:
        if len(data) > MAX_WRITE * 10:
            raise FileError("File too large.")
        p = self._safe(rel)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)

    def make_dir(self, rel: str) -> None:
        self._safe(rel).mkdir(parents=True, exist_ok=True)

    def delete(self, rel: str) -> None:
        p = self._safe(rel)
        if p.is_dir():
            shutil.rmtree(p)
        elif p.is_file():
            p.unlink()
        else:
            raise FileError("Nothing to delete.")

    def extract_zip(self, data: bytes) -> int:
        """Extract a zip into the project (zip-slip safe). Returns file count."""
        count, total = 0, 0
        try:
            z = zipfile.ZipFile(io.BytesIO(data))
        except zipfile.BadZipFile:
            raise FileError("Not a valid zip file.")
        with z:
            infos = [i for i in z.infolist() if not i.is_dir()]
            if len(infos) > 1000:
                raise FileError("Too many files in zip (limit 1000).")
            names = [i.filename for i in infos]
            tops = {n.split("/")[0] for n in names}
            strip = len(tops) == 1 and all("/" in n for n in names)
            for i in infos:
                name = i.filename.split("/", 1)[1] if strip else i.filename
                total += i.file_size
                if total > MAX_ZIP_TOTAL:
                    raise FileError("Zip too large (50 MB limit).")
                try:
                    self.write_bytes(name, z.read(i))
                    count += 1
                except FileError:
                    continue  # skip unsafe/hidden entries
        return count
