import numpy as np
import torch

from .model import TopicNet


class TopicClassifier:
    def __init__(self, model: TopicNet, courses: list[str], topics: list[str],
                 topic_course: dict[str, str], metrics: dict | None = None):
        self.model = model.eval()
        self.courses = courses
        self.topics = topics
        self.metrics = metrics or {}
        # per course: which topic columns are allowed
        self._masks = {
            c: torch.tensor([topic_course[t] == c for t in topics]) for c in courses
        }

    @classmethod
    def load(cls, path: str) -> "TopicClassifier":
        ckpt = torch.load(path, map_location="cpu", weights_only=True)
        model = TopicNet(ckpt["dim"], len(ckpt["courses"]), len(ckpt["topics"]))
        model.load_state_dict(ckpt["state_dict"])
        return cls(model, ckpt["courses"], ckpt["topics"], ckpt["topic_course"],
                   ckpt.get("metrics"))

    @torch.no_grad()
    def predict(self, vectors: np.ndarray, course: str) -> list[tuple[str | None, float | None]]:
        """(topic_id, confidence) per vector, only considering this course's topics."""
        x = torch.as_tensor(np.asarray(vectors), dtype=torch.float32)
        _, logits = self.model(x)
        logits[:, ~self._masks[course]] = float("-inf")
        probs = logits.softmax(1)
        conf, idx = probs.max(1)
        return [(self.topics[i], round(float(p), 4)) for i, p in zip(idx.tolist(), conf.tolist(),
                                                                       strict=True)]

    @torch.no_grad()
    def route(self, qvec: np.ndarray, min_conf: float = 0.8) -> str | None:
        x = torch.as_tensor(np.asarray(qvec), dtype=torch.float32).unsqueeze(0)
        course_logits, _ = self.model(x)
        probs = course_logits.softmax(1)[0]
        p, i = probs.max(0)
        return self.courses[int(i)] if float(p) >= min_conf else None
