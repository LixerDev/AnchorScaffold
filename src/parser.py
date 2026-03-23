"""
Parser — extracts intent and template match from a natural language description.

Uses keyword scoring to rank templates, then returns the best match.
If no template scores above threshold, returns CUSTOM (needs AI generation).
"""

import re
from src.models import TemplateKind, TemplateInfo, TEMPLATE_REGISTRY
from src.logger import get_logger

logger = get_logger(__name__)

MATCH_THRESHOLD = 2    # Minimum keyword score to suggest a template
SLUG_RE = re.compile(r"[^a-z0-9]+")


def parse_description(description: str) -> tuple[TemplateKind, float]:
    """
    Score all templates against the description and return the best match.

    Parameters:
    - description: Natural language program description

    Returns:
    - tuple: (TemplateKind, confidence_score)
      If no template matches well, returns (CUSTOM, 0.0)
    """
    text = description.lower()
    scores: dict[TemplateKind, float] = {}

    for kind, info in TEMPLATE_REGISTRY.items():
        score = 0.0
        for keyword in info.keywords:
            if keyword in text:
                # Exact word match = higher score
                if re.search(rf"\b{re.escape(keyword)}\b", text):
                    score += 2
                else:
                    score += 1
        scores[kind] = score
        logger.debug(f"Template {kind.value}: score={score}")

    if not scores:
        return TemplateKind.CUSTOM, 0.0

    best_kind = max(scores, key=lambda k: scores[k])
    best_score = scores[best_kind]

    if best_score < MATCH_THRESHOLD:
        logger.info(f"No template matched (best: {best_kind.value} @ {best_score}). Using AI custom generation.")
        return TemplateKind.CUSTOM, best_score

    logger.info(f"Best template match: {best_kind.value} (score={best_score})")
    return best_kind, best_score


def extract_program_name(description: str) -> str | None:
    """
    Try to extract a program name from the description.

    Looks for patterns like:
    - "called X" / "named X" / "for X"
    """
    patterns = [
        r"called\s+([a-zA-Z][a-zA-Z0-9_-]{2,30})",
        r"named\s+([a-zA-Z][a-zA-Z0-9_-]{2,30})",
        r"name(?:d)?\s+(?:it\s+)?([a-zA-Z][a-zA-Z0-9_-]{2,30})",
    ]
    for pattern in patterns:
        m = re.search(pattern, description, re.IGNORECASE)
        if m:
            return m.group(1).lower().replace(" ", "-")
    return None


def slugify(name: str) -> str:
    """Convert a name to a valid Rust module name."""
    slug = SLUG_RE.sub("-", name.lower()).strip("-")
    return slug or "my-program"


def to_rust_name(name: str) -> str:
    """Convert a dash-separated name to Rust snake_case module name."""
    return name.replace("-", "_").replace(" ", "_").lower()


def to_display_name(name: str) -> str:
    """Convert to Title Case for display."""
    return name.replace("-", " ").replace("_", " ").title()
