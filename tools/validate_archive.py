"""Check HACS extraction layout and import the bundled library without site packages."""

import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def validate() -> None:
    hacs = json.loads((ROOT / "hacs.json").read_text())
    with zipfile.ZipFile(ROOT / "dist" / hacs["filename"]) as archive:
        names = archive.namelist()
        assert len(names) == len(set(names)), "Duplicate archive entries"
        assert "manifest.json" in names, "HACS extracts directly into the integration directory"
        assert "_vendor/leridian_smart_recirc/client.py" in names
        assert all(not Path(n).is_absolute() and ".." not in Path(n).parts for n in names)
        assert all(not n.startswith("custom_components/") for n in names)
        assert archive.read("LICENSE") == (ROOT / "LICENSE").read_bytes()
        assert b"MIT License" in archive.read("_vendor/LICENSE")
        manifest = json.loads(archive.read("manifest.json"))
        source_manifest = ROOT / "custom_components/smart_recirc/manifest.json"
        assert manifest == json.loads(source_manifest.read_text())
        provenance = json.loads(archive.read("_vendor/library-provenance.json"))
        lock = json.loads((ROOT / "library.lock.json").read_text())
        assert all(provenance[key] == value for key, value in lock.items())
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "custom_components" / manifest["domain"]
            archive.extractall(target)
            subprocess.run(
                [sys.executable, "-I", "-S", "-c",
                 "import sys; sys.path.insert(0, sys.argv[1]); "
                 "import leridian_smart_recirc.client",
                 str(target / "_vendor")],
                check=True,
            )
    print("HACS archive layout, manifest, dependency provenance and isolated import passed")


if __name__ == "__main__":
    validate()
