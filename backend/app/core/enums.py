from enum import Enum


class ResponseMode(str, Enum):
    FRIENDLY = "friendly"
    TECHNICAL = "technical"


class IntentType(str, Enum):
    GENERAL_CONSULTATION = "general_consultation"
    ARTICLE_LOOKUP = "article_lookup"
    JURISPRUDENCE_SUMMARY = "jurisprudence_summary"
    CONTRACT_ANALYSIS = "contract_analysis"
    NORM_COMPARISON = "norm_comparison"
    VALIDITY_CHECK = "validity_check"
    DOCUMENT_CHECKLIST = "document_checklist"
    USER_DOCUMENT = "user_document"
    LEGAL_DRAFT = "legal_draft"
    ESCALATION = "escalation"


class SourceType(str, Enum):
    LEGISLATION = "legislation"
    JURISPRUDENCE = "jurisprudence"
    SUMULA = "sumula"
    LICENSED_DOCTRINE = "licensed_doctrine"
    PROCESS_METADATA = "process_metadata"
    USER_DOCUMENT = "user_document"
    LEGACY_SEED = "legacy_seed"
    CONTRACT = "contract"
    SITUATION = "situation"


class SourceAuthority(str, Enum):
    PRIMARY = "primary"
    SECONDARY = "secondary"
    PRIVATE = "private"


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
