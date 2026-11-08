from app.services.factual_qc_service import calculate_factual_score, validate_qc_payload


def test_programmatic_factual_score():
    claims = [
        {"verification_status": "verified"},
        {"verification_status": "verified"},
        {"verification_status": "unsupported"},
    ]
    issues = [{"severity": "high"}]
    score, counts = calculate_factual_score(claims, issues)
    assert score == 58
    assert counts["verified"] == 2
    assert counts["unsupported"] == 1


def test_rejects_unretrieved_citation():
    payload = {
        "claims": [{"claim_id": "C1", "statement": "A fact", "verification_status": "verified", "associated_references": [{"url": "https://made-up.example"}]}],
        "issues": [],
    }
    claims, issues = validate_qc_payload(payload, {"https://retrieved.example"})
    assert claims[0]["associated_references"][0]["url"] is None
    assert claims[0]["associated_references"][0]["citation_status"] == "unavailable"
    assert issues == []


def test_source_status_and_severity_are_validated():
    payload = {"claims": [], "issues": [{"severity": "extreme", "verification_status": "unsupported"}]}
    try:
        validate_qc_payload(payload, set())
    except ValueError:
        pass
    else:
        raise AssertionError("Invalid severity was accepted")
