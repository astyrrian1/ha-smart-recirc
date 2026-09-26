"""Bundle a wheel built from the exact external library revision in library.lock.json."""

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
import zipfile
from email.parser import BytesParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def build(source: Path, output: Path) -> None:
    lock = json.loads((ROOT / "library.lock.json").read_text())
    commit = subprocess.check_output(
        ["git", "-C", str(source), "rev-parse", "HEAD"], text=True
    ).strip()
    if commit != lock["commit"]:
        raise ValueError("Library checkout does not match the pinned commit")
    if subprocess.check_output(["git", "-C", str(source), "status", "--porcelain"]):
        raise ValueError("Library checkout must be clean")
    with tempfile.TemporaryDirectory(prefix="recirc-wheel-") as temporary:
        subprocess.run(
            [sys.executable, "-m", "build", "--wheel", "--outdir", temporary, str(source)],
            check=True,
        )
        (wheel,) = Path(temporary).glob("*.whl")
        with zipfile.ZipFile(wheel) as dependency:
            metadata_path = next(
                n for n in dependency.namelist() if n.endswith(".dist-info/METADATA")
            )
            metadata = BytesParser().parsebytes(dependency.read(metadata_path))
            if (
                metadata["Name"] != "leridian-smart-recirc"
                or metadata["Version"] != lock["version"]
            ):
                raise ValueError("Built wheel metadata does not match the dependency lock")
            package_files = [
                n for n in dependency.namelist() if n.startswith("leridian_smart_recirc/")
            ]
            if "leridian_smart_recirc/client.py" not in package_files:
                raise ValueError("Wheel does not contain the protocol client")
            output.parent.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
                component = ROOT / "custom_components/smart_recirc"
                for path in sorted(component.rglob("*")):
                    relative = path.relative_to(component)
                    if (
                        path.is_file()
                        and "_vendor" not in relative.parts
                        and "__pycache__" not in relative.parts
                        and path.suffix != ".pyc"
                    ):
                        archive.write(path, f"custom_components/smart_recirc/{relative}")
                vendor = "custom_components/smart_recirc/_vendor"
                for name in package_files:
                    archive.writestr(f"{vendor}/{name}", dependency.read(name))
                archive.writestr(f"{vendor}/__init__.py", "")
                provenance = lock | {"wheel_sha256": hashlib.sha256(wheel.read_bytes()).hexdigest()}
                archive.writestr(
                    f"{vendor}/library-provenance.json", json.dumps(provenance, indent=2)
                )
    print(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--library-source", type=Path, default=ROOT / ".deps/library")
    parser.add_argument("--output", type=Path, default=ROOT / "dist/smart_recirc.zip")
    args = parser.parse_args()
    build(args.library_source.resolve(), args.output.resolve())
