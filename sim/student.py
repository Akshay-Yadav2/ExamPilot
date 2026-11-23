from dataclasses import dataclass

import numpy as np


@dataclass
class SimStudent:
    mastery: np.ndarray  # hidden P(correct) per topic
    learn_rate: float = 0.06  # each question closes 6% of the gap to 1
    forget_rate: float = 0.003  # everything fades a little per question

    def answer(self, topic: int, rng: np.random.Generator) -> float:
        correct = rng.random() < self.mastery[topic]
        self.mastery[topic] += self.learn_rate * (1 - self.mastery[topic])
        self.mastery -= self.forget_rate * self.mastery
        return 1.0 if correct else 0.0
