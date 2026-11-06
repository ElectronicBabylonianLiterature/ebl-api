import hashlib
import json
from pathlib import Path
import shutil

from ebl.fragmentarium.application.map_artifact_generator import DEFAULT_OUTPUT_DIR


def copy_artifacts(tmp_path: Path) -> Path:
    destination = tmp_path / "artifacts"
    shutil.copytree(DEFAULT_OUTPUT_DIR, destination)
    return destination


def replace_declared_file(data_dir: Path, name: str, payload: object) -> None:
    content = (
        payload if isinstance(payload, bytes) else json.dumps(payload).encode("utf-8")
    )
    (data_dir / name).write_bytes(content)
    manifest_path = data_dir / f"{name.split('_', 1)[0]}_artifact_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["files"][name] = hashlib.sha256(content).hexdigest()
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False) + "\n", encoding="utf-8"
    )
