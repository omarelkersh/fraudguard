from agent_eval import grade, unknown_ids

CASE = {"suspicious": False, "must_cite": [], "must_not_cite": ["R1"]}


def test_not_suspicious_is_not_read_as_suspicious():
    result = grade("**Verdict:** Not suspicious.", CASE)
    assert result["verdict_correct"] == 1


def test_forbidden_rule_is_flagged():
    result = grade("Verdict: Suspicious (R1 card testing).\nRules: R1", CASE)
    assert result["verdict_correct"] == 0
    assert result["forbidden_rules"] == ["R1"]


def test_missing_verdict_is_wrong():
    assert grade("I could not decide.", CASE)["verdict_correct"] == 0


def test_made_up_transaction_id_is_flagged():
    real = "24df6dcc-490c-4f97-ab0c-456b8ab20bf4"
    fake = "11111111-2222-3333-4444-555555555555"
    assert unknown_ids(f"Evidence: {real} and {fake}", {real}) == [fake]


def test_rule_mentioned_as_not_applicable_is_not_cited():
    report = "Verdict: Not suspicious. R1 is not applicable.\nRules: none"
    assert grade(report, CASE)["forbidden_rules"] == []
