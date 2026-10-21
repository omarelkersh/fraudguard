from fraudguard_investigator.rag import split_policy

POLICY = """# Title

## R1 Card testing
Many small payments.

## R2 Foreign ATM cash-out
Large withdrawal abroad.
"""


def test_split_policy_gives_one_chunk_per_rule():
    chunks = split_policy(POLICY)
    assert len(chunks) == 2
    assert chunks[0].startswith("## R1 Card testing")
    assert "# Title" not in chunks[0]
