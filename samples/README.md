# Sample data

Short study notes I wrote for all three courses, so the whole thing can be run and
tested without the real (copyrighted) slides. They cover every topic in
`db/topics.sql` at least once.

```
samples/
  daa/   shortest paths, DP, greedy + MST, flow + NP, asymptotics / D&C / graph search
  swe/   design patterns, testing, design principles + Scrum, requirements / UML / architecture
  ai/    search, adversarial search, MDPs + RL, probability, CSP / logic / ML
  quiz.json   37 hand-written quiz questions, at least one per topic
```

Load everything into a fresh database (no API key needed):

```sh
docker compose up -d db redis
make sample
```

That ingests the notes, then `exampilot.cli seed` fakes two weeks of quiz history
by replaying attempts through the real scheduler and spaced-repetition code, plus
some `llm_calls` rows so the spend table isn't empty. Some questions are left
unanswered, so the multiple-choice ones can be practised straight away. Short
answers still need the API for grading.

Everything the seed writes is tagged `model = 'sample'`. `make sample-clear` removes
it and resets the scheduler stats for the topics it touched.
