from pathlib import Path

from services.etl_service.app.services.excel_ingestor import file_sha256


def test_file_sha256(tmp_path: Path):
    f = tmp_path / "x.bin"
    f.write_bytes(b"hello smartbarrel")
    h = file_sha256(f)
    assert len(h) == 64
    assert all(c in "0123456789abcdef" for c in h)
