from app.services.instructional_qc_service import calculate_instructional_score, validate_instructional_payload


def test_programmatic_instructional_score():
    criteria = [
        {"criterion": "objective_alignment", "score": 80},
        {"criterion": "clarity", "score": 70},
        {"criterion": "logical_progression", "score": 60},
        {"criterion": "examples_and_applications", "score": 50},
        {"criterion": "activity", "score": 40},
        {"criterion": "knowledge_check", "score": 70},
        {"criterion": "pacing_and_45_minute_fit", "score": 100},
    ]
    issues = [{"severity": "high"}, {"severity": "medium"}]
    assert calculate_instructional_score(criteria, issues) == 56


def test_invalid_criterion_is_rejected():
    try:
        validate_instructional_payload({"criteria_scores": [{"criterion": "humour", "score": 50}], "issues": []})
    except ValueError:
        pass
    else:
        raise AssertionError("Invalid instructional criterion was accepted")


def test_issue_requires_actionable_recommendation():
    payload = {"criteria_scores": [], "issues": [{"issue_id": "I1", "issue_category": "clarity", "severity": "low", "explanation": "Unclear", "recommendation": ""}]}
    try:
        validate_instructional_payload(payload)
    except ValueError:
        pass
    else:
        raise AssertionError("Issue without recommendation was accepted")
