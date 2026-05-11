from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from app.core.config import get_settings
from app.utils.file_utils import list_files_recursive
from app.utils.zip_utils import safe_arcname


class ZipPackager:
    def package_to_zip(self, source_dir: Path, zip_path: Path) -> str:
        settings = get_settings()
        excluded_dir_names = {"node_modules", ".angular", "dist", "coverage", ".pytest_cache", "__pycache__"}
        excluded_file_suffixes = {".pyc", ".pyo"}
        excluded_file_names = {".DS_Store"}

        with ZipFile(zip_path, mode="w", compression=ZIP_DEFLATED) as archive:
            for file_path in list_files_recursive(source_dir):
                if any(part in excluded_dir_names for part in file_path.parts):
                    continue
                if file_path.name in excluded_file_names:
                    continue
                if file_path.suffix in excluded_file_suffixes:
                    continue
                arcname = safe_arcname(source_dir, file_path)
                archive.write(file_path, arcname=arcname)

        max_bytes = settings.max_zip_size_mb * 1024 * 1024
        if zip_path.stat().st_size > max_bytes:
            raise ValueError(f"Generated ZIP exceeds size limit: {zip_path.stat().st_size} bytes")
        return str(zip_path)
