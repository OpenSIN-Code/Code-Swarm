import torch
import torch.nn as nn

class RecursiveLink(nn.Module):
    """
    RecursiveLink: 2-Layer Residual Modul für latenten State-Transfer.
    """
    def __init__(self, input_dim: int, hidden_dim: int):
        super().__init__()
        self.layer1 = nn.Linear(input_dim, hidden_dim)
        self.activation = nn.GELU()
        self.layer2 = nn.Linear(hidden_dim, input_dim)
        self.residual = nn.Identity()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        residual = x
        out = self.layer1(x)
        out = self.activation(out)
        out = self.layer2(out)
        return out + residual
