"""RecursiveLink modules from RecursiveMAS (Stanford/NVIDIA).
Inner Link: latent state refinement within an agent.
Outer Link (CrossModelAdapter): latent state transfer between agents.
"""
from __future__ import annotations
from typing import Dict, Optional
import torch
import torch.nn as nn


class Adapter(nn.Module):
    """Inner Link: refines latent states within the same agent."""

    def __init__(self, hidden_size: int):
        super().__init__()
        self.proj1 = nn.Linear(hidden_size, hidden_size)
        self.act = nn.GELU()
        self.proj2 = nn.Linear(hidden_size, hidden_size)
        self.pre_ln = nn.LayerNorm(hidden_size)
        self.post_ln = nn.LayerNorm(hidden_size)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        h = self.pre_ln(x)
        out = self.proj2(self.act(self.proj1(h)))
        out = x + out
        return self.post_ln(out)


class CrossModelAdapter(nn.Module):
    """Outer Link: transfers latent states between different agents."""

    def __init__(self, in_dim: int, out_dim: int):
        super().__init__()
        hidden_dim = out_dim * 2
        self.proj1 = nn.Linear(in_dim, hidden_dim)
        self.act = nn.GELU()
        self.proj2 = nn.Linear(hidden_dim, out_dim)
        self.ln_source = nn.LayerNorm(in_dim)
        self.ln_target = nn.LayerNorm(out_dim)
        self.residual_proj = nn.Linear(in_dim, out_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        h = self.ln_source(x)
        out = self.proj2(self.act(self.proj1(h)))
        out = out + self.residual_proj(x)
        return self.ln_target(out)


class RecursiveMASBridge:
    """Bridge between Code-Swarm LangGraph pipeline and RecursiveMAS latent space.
    
    
    Manages Inner/Outer adapters for all configured agents.
    """

    def __init__(self, agent_map: Dict[str, int], hidden_size: int = 768):
        self.agent_map = agent_map  # agent_name -> agent_idx
        self.inner_adapters = nn.ModuleDict({
            name: Adapter(hidden_size) for name in agent_map
        })
        # Outer Links: full mesh between all agents
        self.outer_adapters = nn.ModuleDict()
        for src in agent_map:
            for tgt in agent_map:
                if src != tgt:
                    self.outer_adapters[f"{src}→{tgt}"] = CrossModelAdapter(
                        hidden_size, hidden_size
                    )

    def inner_step(self, agent: str, latent: torch.Tensor) -> torch.Tensor:
        """Run inner link: refine latent state within agent."""
        return self.inner_adapters[agent](latent)

    def outer_transfer(self, src: str, tgt: str, latent: torch.Tensor) -> torch.Tensor:
        """Run outer link: transfer latent state from src to tgt agent."""
        key = f"{src}→{tgt}"
        if key in self.outer_adapters:
            return self.outer_adapters[key](latent)
        return latent  # passthrough if no link

    def forward(self, agent: str, latent: torch.Tensor) -> torch.Tensor:
        """Full recursive step: inner refine + outer broadcast."""
        refined = self.inner_step(agent, latent)
        # Broadcast to all other agents via outer links
        outputs = {}
        for target in self.agent_map:
            if target != agent:
                outputs[target] = self.outer_transfer(agent, target, refined)
        return refined, outputs
