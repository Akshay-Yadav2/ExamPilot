import torch
from torch import nn


class TopicNet(nn.Module):
    """Shared layer + two heads. The course head has thousands of free labels,
    which helps the shared layer the topic head (few labels) sits on."""

    def __init__(self, dim: int, n_courses: int, n_topics: int, hidden: int = 256,
                 dropout: float = 0.2):
        super().__init__()
        self.body = nn.Sequential(nn.Linear(dim, hidden), nn.GELU(), nn.Dropout(dropout))
        self.course_head = nn.Linear(hidden, n_courses)
        self.topic_head = nn.Linear(hidden, n_topics)

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        h = self.body(x)
        return self.course_head(h), self.topic_head(h)
