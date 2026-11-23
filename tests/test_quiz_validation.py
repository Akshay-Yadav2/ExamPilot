from exampilot.quiz import QuizQuestion, grade_mcq, validate_questions


def q(kind="mcq", choices=("a", "b", "c", "d"), answer="a", ids=("c1",)):
    return QuizQuestion(kind=kind, question="?", choices=list(choices), answer=answer,
                        explanation="", source_chunk_ids=list(ids))


def test_drops_questions_citing_unknown_chunks():
    keep, dropped = validate_questions([q(ids=["nope"]), q()], {"c1"})
    assert dropped == 1 and len(keep) == 1


def test_drops_bad_mcq():
    keep, dropped = validate_questions(
        [q(choices=("a", "b", "c")), q(answer="z"), q(kind="short", choices=(), answer="x")],
        {"c1"},
    )
    assert dropped == 2
    assert keep[0][0].kind == "short"


def test_unknown_ids_filtered_but_question_kept():
    keep, dropped = validate_questions([q(ids=["c1", "made_up"])], {"c1"})
    assert dropped == 0
    assert keep[0][1] == ["c1"]


def test_mcq_grading_ignores_case_and_space():
    assert grade_mcq({"answer": "Bellman-Ford"}, "  bellman-ford ") == 2
    assert grade_mcq({"answer": "Bellman-Ford"}, "Dijkstra") == 0
