"""数据管道 smoke tests。"""

from __future__ import annotations

from pathlib import Path

from packages.data_pipeline.loaders import DatasetLoader
from packages.data_pipeline.parsers import KiCadParser
from packages.data_pipeline.transformers import SampleExtractor


FIXTURE_ROOT = Path(__file__).resolve().parents[1] / "fixtures"


def test_parser_smoke(tmp_path: Path) -> None:
    parser = KiCadParser()
    source_dir = FIXTURE_ROOT / "raw"
    output_dir = tmp_path / "parsed"

    parser.parse_projects(str(source_dir), str(output_dir), max_workers=1)

    parsed_files = sorted(output_dir.glob("*.json"))
    assert len(parsed_files) == 1
    assert parsed_files[0].name == "fixture_project.json"


def test_dataset_build_smoke(tmp_path: Path) -> None:
    loader = DatasetLoader()
    parsed_dir = Path("data/fixtures/parsed_boards")
    output_dir = tmp_path / "dataset"

    summary = loader.build_dataset(str(parsed_dir), str(output_dir), task_type="LocalRouteChoiceLite")
    validation = loader.validate_dataset(str(output_dir))

    assert summary["splits"]["train"]["num_boards"] == 1
    assert summary["splits"]["val"]["num_boards"] == 1
    assert summary["splits"]["test"]["num_boards"] == 1
    assert validation["valid"] is True


def test_weak_label_is_deterministic() -> None:
    extractor = SampleExtractor(region_size=32, world_window=16.0)
    project_data = {
        "project_name": "demo",
        "board": {
            "tracks": [
                {"type": "segment", "start": [0.0, 0.0], "end": [10.0, 0.0], "net": 1},
                {"type": "segment", "start": [10.0, 0.0], "end": [10.0, 6.0], "net": 1},
            ]
        },
    }

    samples = extractor.extract_samples_from_project(project_data, task_type="LocalRouteChoiceLite")
    labels = [sample["label"] for sample in samples]

    assert labels == ["right", "down"]