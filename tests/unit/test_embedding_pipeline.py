"""Qwen embedding pipeline smoke tests."""

from __future__ import annotations

from pathlib import Path

from packages.data_pipeline.loaders import GraphTextPairBuilder, KiCadSourceAuditor
from packages.training import EmbeddingTrainer, EmbeddingTrainingConfig


def test_source_auditor_smoke(tmp_path: Path) -> None:
    raw_root = tmp_path / "raw" / "demo_project"
    raw_root.mkdir(parents=True, exist_ok=True)
    (raw_root / "demo_project.kicad_pcb").write_text("(kicad_pcb)", encoding="utf-8")
    (raw_root / "demo_project.kicad_sch").write_text("(kicad_sch)", encoding="utf-8")

    manifest_path = tmp_path / "manifest.json"
    auditor = KiCadSourceAuditor()
    summary = auditor.audit(str(tmp_path / "raw"), str(manifest_path))

    assert summary["total_projects"] == 1
    assert manifest_path.exists()


def test_build_pairs_smoke(tmp_path: Path) -> None:
    builder = GraphTextPairBuilder(seed=7, negatives_per_sample=1)
    parsed_dir = Path("data/fixtures/parsed_boards")
    output_dir = tmp_path / "pairs"

    summary = builder.build_pairs(str(parsed_dir), str(output_dir))
    assert summary["task_type"] == "GraphTextRetrieval"
    assert (output_dir / "train" / "data.jsonl").exists()
    assert (output_dir / "val" / "data.jsonl").exists()
    assert (output_dir / "test" / "data.jsonl").exists()


def test_embedding_train_smoke(tmp_path: Path) -> None:
    builder = GraphTextPairBuilder(seed=7, negatives_per_sample=1)
    parsed_dir = Path("data/fixtures/parsed_boards")
    pair_dir = tmp_path / "pairs"
    builder.build_pairs(str(parsed_dir), str(pair_dir))

    config = EmbeddingTrainingConfig(
        dataset_path=str(pair_dir),
        output_dir=str(tmp_path / "outputs"),
        text_encoder_mode="hash",
        freeze_text_encoder=True,
        epochs=1,
        batch_size=2,
        num_workers=0,
        embedding_dim=64,
        graph_hidden_dim=32,
        graph_feature_dim=12,
        device="cpu",
    )
    trainer = EmbeddingTrainer(config)
    summary = trainer.train()
    assert summary["best_recall_at_1"] >= 0.0

    checkpoint = Path(config.output_dir) / "checkpoints" / "best_model.pt"
    metrics = trainer.evaluate(split="test", checkpoint_path=str(checkpoint), noise_std=0.05)
    assert "recall_at_1" in metrics
    assert "mrr" in metrics
