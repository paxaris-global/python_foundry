import shutil
from pathlib import Path

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def copy_project_to_downloads(zip_path: str, project_name: str, downloads_folder: str | None = None) -> str:
    """
    Copy the generated project zip file to the specified Downloads folder.

    Args:
        zip_path: Full path to the generated zip file
        project_name: Name of the project for the downloaded file
        downloads_folder: Optional specific folder path (overrides config)

    Returns:
        The path where the file was downloaded to

    Raises:
        FileNotFoundError: If the source zip file doesn't exist
        IOError: If the download fails
    """
    source_path = Path(zip_path)
    if not source_path.exists():
        raise FileNotFoundError(f"ZIP file not found at {zip_path}")

    # Determine final downloads directory
    if downloads_folder:
        target_dir = Path(downloads_folder).expanduser().resolve()
    else:
        target_dir = get_settings().downloads_dir
    target_dir.mkdir(parents=True, exist_ok=True)

    # Create destination path with project name
    destination_path = target_dir / f"{project_name}.zip"

    # If file already exists, add a counter
    counter = 1
    base_name = f"{project_name}.zip"
    while destination_path.exists():
        destination_path = target_dir / f"{project_name}-{counter}.zip"
        counter += 1

    try:
        # Copy the file to Downloads
        shutil.copy2(source_path, destination_path)
        logger.info(f"Project downloaded to: {destination_path}")
        return str(destination_path)
    except Exception as exc:
        logger.error(f"Failed to download project to Downloads: {exc}")
        raise IOError(f"Failed to copy project to Downloads: {exc}") from exc
