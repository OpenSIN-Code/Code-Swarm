# RecursiveMAS Integration (from Stanford/NVIDIA Research)

Source: https://github.com/RecursiveMAS/RecursiveMAS
Paper: https://arxiv.org/abs/2604.25917

This directory contains code from RecursiveMAS - a recursive multi-agent framework
that scales agent collaboration through latent-space recursion.

## Files

- `modeling.py` → `recursive_link.py`: RecursiveLink (Inner + Outer adapters)
- `system_loader.py`: `load_mas_system()` API for loading full MAS pipelines
- `prompts.py`: Prompts for Sequential, Mixture, Deliberation, Distillation styles
- `inference_utils/`: Inference pipelines for all collaboration styles
- `hf_resolver.py`: HuggingFace checkpoint resolver
- `load_from_repo.py`: Style-to-checkpoint mappings

## Integration Status

- [x] Copied source code
- [ ] InnerAdapter pipeline integration
- [ ] OuterAdapter cross-agent transfer
- [ ] Multi-style agent orchestration
