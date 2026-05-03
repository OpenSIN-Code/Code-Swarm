from __future__ import annotations

from typing import Dict

STYLE_SPECS: Dict[str, Dict[str, object]] = {
    "sequential_light": {
        "family": "sequential",
        "repos": {
            "planner": "RecursiveMAS/Sequential-Light-Planner-Qwen3-1.7B",
            "critic": "RecursiveMAS/Sequential-Light-Critic-Llama3.2-1B",
            "solver": "RecursiveMAS/Sequential-Light-Solver-Qwen2.5-Math-1.5B",
            "outer": "RecursiveMAS/Sequential-Light-Outerlinks",
        },
    },
    "sequential_scaled": {
        "family": "sequential",
        "repos": {
            "planner": "RecursiveMAS/Sequential-Scaled-Planner-Gemma3-4B",
            "critic": "RecursiveMAS/Sequential-Scaled-Critic-Llama3.2-3B",
            "solver": "RecursiveMAS/Sequential-Scaled-Solver-Qwen3.5-4B",
            "outer": "RecursiveMAS/Sequential-Scaled-Outerlinks",
        },
    },
    "mixture": {
        "family": "mixture",
        "repos": {
            "math": "RecursiveMAS/Mixture-Math-DeepSeek-R1-Distill-Qwen-1.5B",
            "code": "RecursiveMAS/Mixture-Code-Qwen2.5-Coder-3B",
            "science": "RecursiveMAS/Mixture-Science-BioMistral-7B",
            "summarizer": "RecursiveMAS/Mixture-Summarizer-Qwen3.5-2B",
            "outer": "RecursiveMAS/Mixture-Outerlinks",
        },
    },
    "distillation": {
        "family": "distillation",
        "repos": {
            "expert": "RecursiveMAS/Distillation-Expert-Qwen3.5-9B",
            "learner": "RecursiveMAS/Distillation-Learner-Qwen3.5-4B",
            "outer": "RecursiveMAS/Distillation-Outerlinks",
        },
    },
    "deliberation": {
        "family": "deliberation",
        "repos": {
            "reflector": "RecursiveMAS/Deliberation-Reflector-Qwen3.5-4B",
            "toolcaller": "RecursiveMAS/Deliberation-Toolcaller-Qwen3.5-4B",
            "outer": "RecursiveMAS/Deliberation-Outerlinks",
        },
    },
}

STYLE_METADATA: Dict[str, Dict[str, object]] = {
    "sequential_light": {
        "display_name": "Sequential (Light)",
        "description": "Planner → Critic → Solver with lightweight models and latent feedback.",
        "recommended_dataset": "math500",
        "recommended_batch_size": 32,
        "roles": (
            ("planner", "Decomposes the task into structured subproblems."),
            ("critic", "Checks assumptions and spots flaws early."),
            ("solver", "Produces the final answer or implementation."),
        ),
    },
    "sequential_scaled": {
        "display_name": "Sequential (Scaled)",
        "description": "Higher-capacity Planner → Critic → Solver stack for stronger reasoning.",
        "recommended_dataset": "math500",
        "recommended_batch_size": 16,
        "roles": (
            ("planner", "Decomposes the task into structured subproblems."),
            ("critic", "Checks assumptions and spots flaws early."),
            ("solver", "Produces the final answer or implementation."),
        ),
    },
    "mixture": {
        "display_name": "Mixture",
        "description": "Parallel specialists reason independently and a summarizer aggregates the latent state.",
        "recommended_dataset": "math500",
        "recommended_batch_size": 16,
        "roles": (
            ("math", "Handles mathematical reasoning."),
            ("code", "Handles coding and program synthesis."),
            ("science", "Handles scientific and biomedical reasoning."),
            ("summarizer", "Aggregates specialist output into one answer."),
        ),
    },
    "distillation": {
        "display_name": "Distillation",
        "description": "Expert → Learner recursion that compresses capability into the cheaper model.",
        "recommended_dataset": "math500",
        "recommended_batch_size": 16,
        "roles": (
            ("expert", "Provides rich guidance and high-capacity reasoning."),
            ("learner", "Absorbs the expert signal and becomes faster to serve."),
        ),
    },
    "deliberation": {
        "display_name": "Deliberation",
        "description": "Reflector ↔ Tool-Caller loop for search- and execution-backed reasoning.",
        "recommended_dataset": "math500",
        "recommended_batch_size": 16,
        "roles": (
            ("reflector", "Critiques and refines the reasoning loop."),
            ("toolcaller", "Calls tools such as search or Python execution."),
        ),
    },
}

SUPPORTED_BENCHMARKS = (
    {"key": "math500", "name": "MATH500", "metric": "accuracy", "domain": "math reasoning"},
    {"key": "aime_2025", "name": "AIME 2025", "metric": "accuracy", "domain": "competition math"},
    {"key": "aime_2026", "name": "AIME 2026", "metric": "accuracy", "domain": "competition math"},
    {"key": "gpqa_d", "name": "GPQA-D", "metric": "accuracy", "domain": "graduate Q&A"},
    {"key": "livecodebench", "name": "LiveCodeBench", "metric": "pass@1", "domain": "code generation"},
    {"key": "medqa", "name": "MedQA", "metric": "accuracy", "domain": "medical reasoning"},
    {"key": "codegen", "name": "CodeGen", "metric": "pass@1", "domain": "code generation"},
    {"key": "mbppplus", "name": "MBPP+", "metric": "pass@k", "domain": "code generation"},
    {"key": "bamboogle", "name": "Bamboogle", "metric": "accuracy", "domain": "search QA"},
)

DATASET_DEFAULT_SPLIT = {
    "math500": "test",
    "math-500": "test",
    "huggingfaceh4/math-500": "test",
    "gpqa": "train",
    "gpqa_diamond": "train",
    "idavidrein/gpqa": "train",
    "medqa": "train",
    "local/medqa": "train",
    "mbppplus": "test",
    "evalplus/mbppplus": "test",
}


def list_supported_styles() -> tuple[str, ...]:
    return tuple(STYLE_SPECS.keys())


def get_style_metadata(style: str) -> Dict[str, object]:
    if style not in STYLE_METADATA:
        raise ValueError(f"Unsupported style metadata: {style}")
    return STYLE_METADATA[style]


def describe_style(style: str) -> Dict[str, object]:
    spec = STYLE_SPECS.get(style)
    if spec is None:
        raise ValueError(f"Unsupported style: {style}")
    metadata = get_style_metadata(style)
    return {
        "style": style,
        "family": spec["family"],
        "display_name": metadata["display_name"],
        "description": metadata["description"],
        "recommended_dataset": metadata["recommended_dataset"],
        "recommended_batch_size": metadata["recommended_batch_size"],
        "roles": metadata["roles"],
        "repos": spec["repos"],
    }
