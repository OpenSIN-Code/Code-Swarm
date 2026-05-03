from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from recursivemas.load_from_repo import (
    SUPPORTED_BENCHMARKS,
    STYLE_METADATA,
    STYLE_SPECS,
    describe_style,
    list_supported_styles,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = REPO_ROOT / "recursivemas" / "run.py"
REQUIRED_RUNTIME_DEPENDENCIES = ("torch", "transformers", "sentencepiece", "accelerate", "huggingface_hub")


def missing_runtime_dependencies() -> list[str]:
    return [name for name in REQUIRED_RUNTIME_DEPENDENCIES if importlib.util.find_spec(name) is None]


def format_style_summary(style: str) -> str:
    info = describe_style(style)
    roles = "\n".join(f"- {role}: {desc}" for role, desc in info["roles"])
    repos = "\n".join(f"- {name}: {repo}" for name, repo in info["repos"].items())
    return (
        f"{info['display_name']}\n"
        f"Family: {info['family']}\n"
        f"Description: {info['description']}\n"
        f"Recommended dataset: {info['recommended_dataset']}\n"
        f"Recommended batch size: {info['recommended_batch_size']}\n\n"
        f"Roles:\n{roles}\n\n"
        f"Checkpoints:\n{repos}"
    )


def build_run_command(
    style: str,
    *,
    dataset: str = "math500",
    dataset_split: str = "",
    batch_size: int | None = None,
    device: str | None = None,
    seed: int = 42,
    sample_seed: int = -1,
    rounds: int = 3,
    latent_length: int = 32,
    temperature: float = 0.6,
    top_p: float = 0.95,
    top_k: int = -1,
    trust_remote_code: bool = True,
    python_executable: str | None = None,
) -> list[str]:
    if style not in STYLE_SPECS:
        raise ValueError(f"Unsupported RecursiveMAS style: {style}")

    metadata = STYLE_METADATA[style]
    resolved_batch_size = batch_size or int(metadata["recommended_batch_size"])
    python = python_executable or sys.executable

    command = [
        python,
        str(RUNNER_PATH),
        "--style",
        style,
        "--dataset",
        dataset,
        "--seed",
        str(seed),
        "--sample_seed",
        str(sample_seed),
        "--num_recursive_rounds",
        str(rounds),
        "--batch_size",
        str(resolved_batch_size),
        "--latent_length",
        str(latent_length),
        "--temperature",
        str(temperature),
        "--top_p",
        str(top_p),
        "--top_k",
        str(top_k),
        "--trust_remote_code",
        "1" if trust_remote_code else "0",
    ]
    if dataset_split:
        command.extend(["--dataset_split", dataset_split])
    if device:
        command.extend(["--device", device])
    return command


def benchmark_rows() -> list[dict[str, str]]:
    return [
        {
            "key": item["key"],
            "name": item["name"],
            "metric": item["metric"],
            "domain": item["domain"],
        }
        for item in SUPPORTED_BENCHMARKS
    ]
