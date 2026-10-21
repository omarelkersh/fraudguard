import re


def split_policy(text: str) -> list[str]:
    """Split the policy into one chunk per '## ' section (the title stays in the chunk)."""
    sections = re.split(r"\n(?=## )", text)  # split before every line starting with "## "
    return [s.strip() for s in sections if s.startswith("## ")]  # keep only the rule sections
