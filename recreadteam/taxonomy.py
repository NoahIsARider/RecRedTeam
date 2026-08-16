"""Threat taxonomy: 8 threat categories for LLM/Agentic recommendation systems,
mapped to OWASP ASI 2026 (Agentic Security Initiative) and OWASP LLM Top-10.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ThreatCategory:
    id: str
    name: str
    name_cn: str
    description: str
    owasp_asi: str
    owasp_llm: str
    default_severity: str
    examples: tuple[str, ...] = field(default_factory=tuple)


HALLUCINATION = ThreatCategory(
    id="hallucination",
    name="Product Hallucination",
    name_cn="商品幻觉",
    description=(
        "The agent fabricates or confidently repeats product attributes, claims, "
        "features or availability that do not exist in the retrieved context "
        "(fake specs, fake certifications, fake stock, non-existent products)."
    ),
    owasp_asi="ASI-08 Deceptive Interface",
    owasp_llm="LLM09 Misinformation",
    default_severity="high",
    examples=("phantom SKU", "fabricated spec sheet", "fake 'FDA approved' badge"),
)

INDIRECT_INJECTION = ThreatCategory(
    id="indirect_prompt_injection",
    name="Indirect Prompt Injection",
    name_cn="间接提示注入",
    description=(
        "Hidden instructions embedded in third-party content (product description, "
        "seller profile, reviews, images/OCR) hijack the agent to act against the "
        "user's interest, e.g. force a specific product, exfiltrate data or spread FUD."
    ),
    owasp_asi="ASI-02 Indirect Prompt Injection",
    owasp_llm="LLM01 Prompt Injection",
    default_severity="critical",
    examples=("description-level instruction", "seller profile payload", "review-carried injection"),
)

FAKE_REVIEWS = ThreatCategory(
    id="fake_review_manipulation",
    name="Fake Review Manipulation",
    name_cn="虚假评论操纵",
    description=(
        "Attackers inject synthetic reviews or manipulate review signals (ratings, "
        "helpful votes) to steer the agent's ranking and recommendation toward a "
        "malicious or low-quality product."
    ),
    owasp_asi="ASI-06 Memory & Context Poisoning",
    owasp_llm="LLM04 Data and Model Poisoning",
    default_severity="high",
    examples=("astroturfed 5-star flood", "sock-puppet reviews", "review suppression"),
)

PRICE_DECEPTION = ThreatCategory(
    id="price_deception",
    name="Price Deception",
    name_cn="价格欺骗",
    description=(
        "Misleading pricing signals: fake anchor prices, 'was $X now $Y' without a "
        "real historical price, hidden fees at checkout, currency/unit confusion. "
        "The agent echoes or reinforces the deceptive price as a bargain."
    ),
    owasp_asi="ASI-08 Deceptive Interface",
    owasp_llm="LLM09 Misinformation",
    default_severity="high",
    examples=("fake anchor price", "hidden surcharge", "bait-and-switch deal"),
)

DARK_PATTERN = ThreatCategory(
    id="dark_pattern",
    name="Dark Patterns",
    name_cn="暗黑模式",
    description=(
        "Deceptive interface/interaction design: pre-checked boxes, disguised ads, "
        "forced subscription, hard-to-find cancellation, countdown pressure. The "
        "agent surfaces or endorses these patterns without warning the user."
    ),
    owasp_asi="ASI-08 Deceptive Interface",
    owasp_llm="LLM05 Improper Output Handling",
    default_severity="high",
    examples=("pre-checked add-on", "forced continuity", "fake urgency timer"),
)

FILTER_BUBBLE = ThreatCategory(
    id="filter_bubble",
    name="Filter Bubble / Ranking Manipulation",
    name_cn="过滤气泡",
    description=(
        "The recommendation scope is artificially narrowed: sponsored/attacker "
        "items crowd out organic alternatives, competitors are suppressed, and the "
        "user is never shown the full option space."
    ),
    owasp_asi="ASI-03 Tool Misuse",
    owasp_llm="LLM05 Improper Output Handling",
    default_severity="medium",
    examples=("sponsored crowding", "competitor suppression", "curated narrow list"),
)

STEREOTYPE_BIAS = ThreatCategory(
    id="stereotype_bias",
    name="Stereotype Bias",
    name_cn="刻板偏见",
    description=(
        "Recommendations encode demographic/gender/age/ethnic stereotypes from "
        "profiles or content (e.g. 'women want beauty, men want tech'), producing "
        "biased, exclusionary or harmful suggestions."
    ),
    owasp_asi="ASI-03 Tool Misuse",
    owasp_llm="LLM09 Misinformation",
    default_severity="medium",
    examples=("gendered product steering", "age-based pigeonholing", "biased persona targeting"),
)

BACKDOOR = ThreatCategory(
    id="backdoor",
    name="Backdoor / Triggered Hijack",
    name_cn="后门",
    description=(
        "A trigger phrase or token hidden in the item or prompt silently switches "
        "the agent to malicious behavior (e.g. redirect to a phishing shop, leak "
        "account data) that is undetectable without the trigger."
    ),
    owasp_asi="ASI-09 Supply Chain",
    owasp_llm="LLM04 Data and Model Poisoning",
    default_severity="critical",
    examples=("trigger word redirect", "phishing link swap", "silent data funnel"),
)

MULTI_TURN_ESCALATION = ThreatCategory(
    id="multi_turn_escalation",
    name="Multi-turn Social Engineering Escalation",
    name_cn="多轮升级",
    description=(
        "A conversational attacker progressively escalates across turns to extract "
        "personal data, payment details or force harmful actions, exploiting the "
        "agent's lack of persistent safety state."
    ),
    owasp_asi="ASI-05 Data Exfiltration",
    owasp_llm="LLM05 Improper Output Handling",
    default_severity="critical",
    examples=("slow-roll PII extraction", "escalating privilege trick", "convincing order-fraud"),
)

ALL_CATEGORIES: tuple[ThreatCategory, ...] = (
    HALLUCINATION,
    INDIRECT_INJECTION,
    FAKE_REVIEWS,
    PRICE_DECEPTION,
    DARK_PATTERN,
    FILTER_BUBBLE,
    STEREOTYPE_BIAS,
    BACKDOOR,
    MULTI_TURN_ESCALATION,
)

CATEGORY_MAP: dict[str, ThreatCategory] = {c.id: c for c in ALL_CATEGORIES}


def get_category(category_id: str) -> ThreatCategory:
    if category_id not in CATEGORY_MAP:
        raise KeyError(f"Unknown threat category: {category_id}")
    return CATEGORY_MAP[category_id]
