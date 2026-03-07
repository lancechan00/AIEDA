"""训练与评估 smoke tests。"""

from __future__ import annotations

from pathlib import Path

from packages.training import Trainer, TrainingConfig


def _make_config(tmp_path: Path) -> TrainingConfig:
    return TrainingConfig(
        experiment_name="smoke_test",
        dataset_path="data/fixtures/local_route_choice_lite",
        output_dir=str(tmp_path / "outputs"),
        model_name="tiny_baseline",
        modalities=["geometry", "image"],
        epochs=1,
        batch_size=2,
        num_workers=0,
        hidden_dim=32,
        device="cpu",
    )


def test_train_smoke(tmp_path: Path) -> None:
    config = _make_config(tmp_path)
    trainer = Trainer(config)
    summary = trainer.train()

    assert summary["best_accuracy"] >= 0.0
    assert (Path(config.output_dir) / "checkpoints" / "best_model.pt").exists()


def test_eval_smoke(tmp_path: Path) -> None:
    config = _make_config(tmp_path)
    trainer = Trainer(config)
    trainer.train()

    checkpoint = Path(config.output_dir) / "checkpoints" / "best_model.pt"
    metrics = trainer.evaluate(split="test", checkpoint_path=str(checkpoint))

    assert "accuracy" in metrics
    assert "top_3_accuracy" in metrics
