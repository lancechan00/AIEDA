"""PatchGenerationLite pipeline smoke tests。"""

from __future__ import annotations

from pathlib import Path

from packages.data_pipeline.loaders import PatchGenerationBuilder
from packages.evaluation import compute_patch_metrics
from packages.training import GenerativeTrainer, GenerativeTrainingConfig


def test_patch_dataset_build_smoke(tmp_path: Path) -> None:
    builder = PatchGenerationBuilder(config={"max_samples_per_board": 8, "max_context_tracks": 4})
    parsed_dir = Path("data/fixtures/parsed_boards")
    output_dir = tmp_path / "patch_dataset"

    summary = builder.build_dataset(parsed_data_dir=str(parsed_dir), output_dir=str(output_dir))

    assert summary["splits"]["train"]["num_samples"] > 0
    assert summary["splits"]["val"]["num_samples"] > 0
    assert summary["splits"]["test"]["num_samples"] > 0


def test_patch_generation_train_smoke(tmp_path: Path) -> None:
    builder = PatchGenerationBuilder(config={"max_samples_per_board": 8, "max_context_tracks": 4})
    dataset_dir = tmp_path / "patch_dataset"
    builder.build_dataset(parsed_data_dir="data/fixtures/parsed_boards", output_dir=str(dataset_dir))

    config = GenerativeTrainingConfig(
        dataset_path=str(dataset_dir),
        output_dir=str(tmp_path / "outputs"),
        epochs=1,
        batch_size=2,
        num_workers=0,
        load_pretrained=False,
        device="cpu",
        eval_generation_samples=4,
        generation_max_new_tokens=32,
    )
    trainer = GenerativeTrainer(config)
    summary = trainer.train()

    assert "best_action_exact_match" in summary
    assert (Path(config.output_dir) / "checkpoints" / "best_model.pt").exists()


def test_patch_metrics_smoke() -> None:
    preds = ['{"op":"add_trace","net_id":"N1","params":{"layer":"F.Cu","points":[[0,0],[1,1]]}}']
    targets = ['{"op":"add_trace","net_id":"N1","params":{"layer":"F.Cu","points":[[0,0],[1,1]]}}']
    metrics = compute_patch_metrics(predictions=preds, targets=targets)
    assert metrics["parse_success_rate"] == 1.0
    assert metrics["field_completeness_rate"] == 1.0
