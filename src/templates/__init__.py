"""Template registry — maps TemplateKind to code generation functions."""

from src.models import TemplateKind
from src.templates.staking import STAKING_TEMPLATE
from src.templates.escrow import ESCROW_TEMPLATE
from src.templates.other import (
    VESTING_TEMPLATE,
    DAO_TEMPLATE,
    LOTTERY_TEMPLATE,
    MULTISIG_TEMPLATE,
    MARKETPLACE_TEMPLATE,
    LAUNCHPAD_TEMPLATE,
)

_TEMPLATES = {
    TemplateKind.STAKING:     STAKING_TEMPLATE,
    TemplateKind.ESCROW:      ESCROW_TEMPLATE,
    TemplateKind.VESTING:     VESTING_TEMPLATE,
    TemplateKind.DAO:         DAO_TEMPLATE,
    TemplateKind.LOTTERY:     LOTTERY_TEMPLATE,
    TemplateKind.MULTISIG:    MULTISIG_TEMPLATE,
    TemplateKind.MARKETPLACE: MARKETPLACE_TEMPLATE,
    TemplateKind.LAUNCHPAD:   LAUNCHPAD_TEMPLATE,
}


def get_template_code(kind: TemplateKind, program_name: str) -> str:
    """Return the Rust code for a template with the program name substituted."""
    template_fn = _TEMPLATES.get(kind)
    if not template_fn:
        raise ValueError(f"No template found for: {kind}")
    return template_fn(program_name)
