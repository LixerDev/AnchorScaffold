from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class TemplateKind(str, Enum):
    STAKING     = "staking"
    ESCROW      = "escrow"
    VESTING     = "vesting"
    DAO         = "dao"
    LOTTERY     = "lottery"
    MULTISIG    = "multisig"
    MARKETPLACE = "marketplace"
    LAUNCHPAD   = "launchpad"
    CUSTOM      = "custom"


@dataclass
class TemplateInfo:
    kind: TemplateKind
    display_name: str
    description: str
    instructions: list[str]
    accounts: list[str]
    errors: list[str]
    events: list[str]
    keywords: list[str]            # Used for NL matching
    complexity: str                # Simple / Medium / Advanced


TEMPLATE_REGISTRY: dict[TemplateKind, TemplateInfo] = {
    TemplateKind.STAKING: TemplateInfo(
        kind=TemplateKind.STAKING,
        display_name="Time-Based Staking",
        description="Stake SPL tokens and earn reward tokens proportional to stake amount and time.",
        instructions=["initialize", "stake", "unstake", "claim_rewards"],
        accounts=["StakingPool", "StakeAccount", "Vault", "RewardVault"],
        errors=["InsufficientStake", "NoPendingRewards", "Overflow", "Underflow"],
        events=["StakeEvent", "UnstakeEvent", "ClaimEvent"],
        keywords=["stake", "staking", "reward", "earn", "time", "lock", "deposit", "yield"],
        complexity="Medium",
    ),
    TemplateKind.ESCROW: TemplateInfo(
        kind=TemplateKind.ESCROW,
        display_name="SPL Token Escrow",
        description="Trustless escrow: buyer deposits tokens, release requires seller fulfillment + buyer approval.",
        instructions=["create_escrow", "fulfill", "approve_release", "cancel", "dispute"],
        accounts=["EscrowAccount", "EscrowVault"],
        errors=["EscrowNotFulfilled", "Unauthorized", "EscrowExpired", "AlreadyFulfilled"],
        events=["EscrowCreated", "EscrowFulfilled", "EscrowReleased", "EscrowCancelled"],
        keywords=["escrow", "buyer", "seller", "conditional", "release", "payment", "trustless", "p2p"],
        complexity="Medium",
    ),
    TemplateKind.VESTING: TemplateInfo(
        kind=TemplateKind.VESTING,
        display_name="Token Vesting",
        description="Lock tokens with a cliff period and linear vesting schedule. Common for team allocations.",
        instructions=["create_vesting", "claim", "cancel_vesting"],
        accounts=["VestingAccount", "VestingVault"],
        errors=["CliffNotReached", "NothingToVest", "VestingNotCancellable", "Unauthorized"],
        events=["VestingCreated", "TokensClaimed", "VestingCancelled"],
        keywords=["vest", "vesting", "cliff", "linear", "unlock", "lock", "schedule", "team", "allocation"],
        complexity="Medium",
    ),
    TemplateKind.DAO: TemplateInfo(
        kind=TemplateKind.DAO,
        display_name="DAO Governance",
        description="On-chain governance: create proposals, vote with token weight, execute approved proposals.",
        instructions=["initialize_dao", "create_proposal", "cast_vote", "execute_proposal", "cancel_proposal"],
        accounts=["DaoConfig", "Proposal", "VoteRecord", "Treasury"],
        errors=["ProposalNotActive", "AlreadyVoted", "QuorumNotMet", "VotingPeriodOver", "Unauthorized"],
        events=["ProposalCreated", "VoteCast", "ProposalExecuted", "ProposalCancelled"],
        keywords=["dao", "governance", "vote", "voting", "proposal", "quorum", "treasury", "community"],
        complexity="Advanced",
    ),
    TemplateKind.LOTTERY: TemplateInfo(
        kind=TemplateKind.LOTTERY,
        display_name="On-Chain Lottery",
        description="Buy tickets with SOL, random winner selection using slot hash, claim prize pool.",
        instructions=["initialize_lottery", "buy_ticket", "draw_winner", "claim_prize"],
        accounts=["LotteryAccount", "TicketAccount"],
        errors=["LotteryNotActive", "LotteryNotDrawn", "AlreadyClaimed", "NotWinner", "LotteryFull"],
        events=["TicketPurchased", "WinnerDrawn", "PrizeClaimed"],
        keywords=["lottery", "raffle", "ticket", "winner", "random", "prize", "jackpot", "lucky"],
        complexity="Medium",
    ),
    TemplateKind.MULTISIG: TemplateInfo(
        kind=TemplateKind.MULTISIG,
        display_name="M-of-N Multisig",
        description="Multi-signature wallet requiring M approvals from N owners before executing transactions.",
        instructions=["create_multisig", "create_transaction", "approve", "reject", "execute_transaction"],
        accounts=["Multisig", "MultisigTransaction"],
        errors=["AlreadyApproved", "AlreadyRejected", "ThresholdNotMet", "TransactionExpired", "Unauthorized"],
        events=["TransactionCreated", "TransactionApproved", "TransactionExecuted", "TransactionRejected"],
        keywords=["multisig", "multi-sig", "multi", "signature", "owners", "threshold", "approval", "safe"],
        complexity="Advanced",
    ),
    TemplateKind.MARKETPLACE: TemplateInfo(
        kind=TemplateKind.MARKETPLACE,
        display_name="NFT Marketplace",
        description="Fixed-price NFT marketplace: list, buy, delist. Supports royalties and platform fees.",
        instructions=["list_nft", "buy_nft", "delist_nft", "update_price"],
        accounts=["MarketplaceConfig", "Listing"],
        errors=["ListingNotActive", "InsufficientFunds", "NotOwner", "PriceMismatch"],
        events=["NftListed", "NftSold", "NftDelisted", "PriceUpdated"],
        keywords=["nft", "marketplace", "list", "buy", "sell", "royalty", "collection", "mint", "trade"],
        complexity="Advanced",
    ),
    TemplateKind.LAUNCHPAD: TemplateInfo(
        kind=TemplateKind.LAUNCHPAD,
        display_name="Token Launchpad",
        description="Fair token launch: contribute SOL during sale period, claim tokens at TGE proportionally.",
        instructions=["initialize_sale", "contribute", "finalize_sale", "claim_tokens", "refund"],
        accounts=["SaleConfig", "Contribution"],
        errors=["SaleNotActive", "SaleEnded", "HardCapReached", "BelowMinContribution", "AlreadyClaimed"],
        events=["SaleInitialized", "ContributionMade", "SaleFinalized", "TokensClaimed"],
        keywords=["launch", "launchpad", "sale", "ido", "igo", "contribute", "tge", "fair", "token"],
        complexity="Medium",
    ),
}


@dataclass
class GenerationRequest:
    description: str
    program_name: str
    template_kind: TemplateKind
    output_dir: str
    use_ai: bool = True
    extra_params: dict = field(default_factory=dict)


@dataclass
class GeneratedProgram:
    name: str
    template_kind: TemplateKind
    rust_code: str
    typescript_tests: str
    anchor_toml: str
    cargo_workspace: str
    cargo_program: str
    client_stub: str = ""
    ai_generated: bool = False
    description: str = ""
