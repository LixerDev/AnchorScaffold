"""
Generator — selects template and optionally uses GPT-4 to customize/create programs.

Two paths:
1. Template path: use pre-built Anchor template, substitute program name
2. AI path: send description to GPT-4 with Anchor expert system prompt
"""

from src.models import GenerationRequest, GeneratedProgram, TemplateKind, TEMPLATE_REGISTRY
from src.templates import get_template_code
from src.test_generator import TestGenerator
from src.scaffolder import make_anchor_toml, make_cargo_workspace, make_cargo_program, make_client_stub
from src.logger import get_logger
from config import config

logger = get_logger(__name__)

ANCHOR_SYSTEM_PROMPT = """You are an expert Solana/Anchor program developer. 
Generate complete, production-quality Anchor 0.30.0 programs in Rust.

Rules:
- Use anchor_lang::prelude::*
- Use anchor_spl::token for SPL token operations
- Include proper account validation with constraints
- Include comprehensive error enums with #[error_code]
- Include events with #[event]
- Use checked arithmetic (checked_add, checked_sub, checked_mul)
- All account structs need proper space calculation with #[account(init, ...)]
- Include sensible doc comments on all instructions
- Use Clock::get()? for time operations
- Do NOT include placeholder comments like "// add logic here" — write the actual logic
- The program must be complete and compilable

Output ONLY valid Rust code starting with `use anchor_lang::prelude::*;`
Do not include markdown code blocks or explanations."""


class Generator:
    def __init__(self):
        self.test_gen = TestGenerator()

    async def generate(self, request: GenerationRequest) -> GeneratedProgram:
        """
        Generate a complete Anchor program from the request.

        If template is CUSTOM or AI is forced, uses GPT-4.
        Otherwise, uses the pre-built template.

        Parameters:
        - request: GenerationRequest with all params

        Returns:
        - GeneratedProgram with all file contents
        """
        rust_code = ""
        ai_generated = False

        if request.template_kind == TemplateKind.CUSTOM:
            if config.ai_enabled and request.use_ai:
                rust_code = await self._generate_with_ai(request)
                ai_generated = True
            else:
                rust_code = self._generate_fallback(request)
        else:
            # Use template
            rust_code = get_template_code(request.template_kind, request.program_name)
            logger.info(f"Using template: {request.template_kind.value}")

            # If AI enabled, optionally enhance with description-specific customizations
            if config.ai_enabled and request.use_ai and request.description:
                rust_code = await self._enhance_with_ai(rust_code, request)

        ts_tests = self.test_gen.generate(request.template_kind, request.program_name)
        anchor_toml = make_anchor_toml(request.program_name)
        cargo_ws = make_cargo_workspace(request.program_name)
        cargo_prog = make_cargo_program(request.program_name)
        client_stub = make_client_stub(request.program_name)

        return GeneratedProgram(
            name=request.program_name,
            template_kind=request.template_kind,
            rust_code=rust_code,
            typescript_tests=ts_tests,
            anchor_toml=anchor_toml,
            cargo_workspace=cargo_ws,
            cargo_program=cargo_prog,
            client_stub=client_stub,
            ai_generated=ai_generated,
            description=request.description,
        )

    async def _generate_with_ai(self, request: GenerationRequest) -> str:
        """Generate fully custom program with GPT-4."""
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)

            user_prompt = (
                f"Generate a complete Anchor/Rust program for this requirement:\n\n"
                f"{request.description}\n\n"
                f"Program name (Rust module): {request.program_name.replace('-', '_')}\n"
                "Include: all instructions, account structs, error codes, events, and helper functions."
            )

            logger.info("Calling GPT-4 for custom program generation...")
            response = await client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": ANCHOR_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=4096,
                temperature=0.2,
            )

            code = response.choices[0].message.content.strip()
            # Strip markdown if GPT wraps it
            if code.startswith("```"):
                code = "\n".join(code.split("\n")[1:])
            if code.endswith("```"):
                code = "\n".join(code.split("\n")[:-1])
            return code

        except Exception as e:
            logger.error(f"GPT-4 generation failed: {e}")
            return self._generate_fallback(request)

    async def _enhance_with_ai(self, template_code: str, request: GenerationRequest) -> str:
        """Use GPT-4 to add description-specific customizations to the template."""
        if not request.description:
            return template_code
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)

            prompt = (
                f"Here is an Anchor/Rust program template:\n\n```rust\n{template_code[:2000]}\n```\n\n"
                f"The user's requirements: {request.description}\n\n"
                "Add any custom logic, rename fields, or adjust constants to match the requirements. "
                "Return the complete modified Rust code only."
            )

            response = await client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": ANCHOR_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=4096,
                temperature=0.2,
            )

            code = response.choices[0].message.content.strip()
            if code.startswith("```"):
                code = "\n".join(code.split("\n")[1:])
            if code.endswith("```"):
                code = "\n".join(code.split("\n")[:-1])
            return code

        except Exception as e:
            logger.debug(f"AI enhancement failed: {e}")
            return template_code

    def _generate_fallback(self, request: GenerationRequest) -> str:
        """Generate a minimal custom Anchor stub when AI is not available."""
        module_name = request.program_name.replace("-", "_")
        return f'''// Generated by AnchorScaffold — LixerDev
// Program: {request.program_name}
// Description: {request.description}
// Note: Add OPENAI_API_KEY to .env for AI-powered full generation.

use anchor_lang::prelude::*;
use anchor_spl::token::{{Token, TokenAccount, Mint}};

declare_id!("11111111111111111111111111111111");

#[program]
pub mod {module_name} {{
    use super::*;

    /// Initialize the program
    pub fn initialize(ctx: Context<Initialize>) -> Result<()> {{
        let state = &mut ctx.accounts.state;
        state.authority = ctx.accounts.authority.key();
        state.bump = ctx.bumps.state;
        Ok(())
    }}

    // TODO: Add your custom instructions here
    // Run: anchor-scaffold generate "{request.description}" with OPENAI_API_KEY set
    // for full AI-powered generation.
}}

#[derive(Accounts)]
pub struct Initialize<\'info> {{
    #[account(
        init,
        payer = authority,
        space = 8 + ProgramState::INIT_SPACE,
        seeds = [b"state"],
        bump,
    )]
    pub state: Account<\'info, ProgramState>,

    #[account(mut)]
    pub authority: Signer<\'info>,

    pub system_program: Program<\'info, System>,
}}

#[account]
#[derive(InitSpace)]
pub struct ProgramState {{
    pub authority: Pubkey,  // 32
    pub bump: u8,           // 1
}}

#[error_code]
pub enum ErrorCode {{
    #[msg("Unauthorized access")]
    Unauthorized,
}}
'''
