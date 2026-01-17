"""
Domain expert detector - activates domain experts based on content analysis.
"""
from typing import List, Tuple
import re


class DomainExpertDetector:
    """
    Detects and activates domain expert agents based on project content.
    Uses keyword matching with confidence scoring.
    """

    # Keyword mappings from agent-orchestration-v2.yml
    KEYWORD_MAPPINGS = {
        "healthcare": {
            "agent_id": "healthcare_expert",
            "keywords": [
                "health", "medical", "patient", "clinical", "hospital",
                "diagnosis", "treatment", "hipaa", "ehr", "emr", "healthcare",
                "doctor", "nurse", "prescription", "pharmacy", "telemedicine",
            ],
        },
        "finance": {
            "agent_id": "finance_expert",
            "keywords": [
                "bank", "banking", "payment", "transaction", "trading",
                "stock", "investment", "loan", "credit", "debit", "fintech",
                "pci", "sox", "financial", "money", "wallet", "ledger",
            ],
        },
        "ecommerce": {
            "agent_id": "ecommerce_expert",
            "keywords": [
                "shop", "shopping", "cart", "checkout", "product", "catalog",
                "order", "inventory", "ecommerce", "store", "merchant",
                "customer", "purchase", "retail",
            ],
        },
        "edtech": {
            "agent_id": "edtech_expert",
            "keywords": [
                "learning", "course", "student", "education", "school",
                "university", "lms", "training", "curriculum", "assessment",
                "grade", "classroom", "teacher", "ferpa",
            ],
        },
        "iot": {
            "agent_id": "iot_expert",
            "keywords": [
                "sensor", "device", "embedded", "telemetry", "iot",
                "connected", "smart", "mqtt", "edge", "firmware",
                "gateway", "actuator",
            ],
        },
        "gaming": {
            "agent_id": "gaming_expert",
            "keywords": [
                "game", "gaming", "player", "multiplayer", "score",
                "level", "match", "leaderboard", "realtime", "lobby",
            ],
        },
        "social": {
            "agent_id": "social_expert",
            "keywords": [
                "social", "feed", "post", "community", "follow",
                "like", "share", "comment", "friend", "network",
                "timeline", "notification",
            ],
        },
        "legaltech": {
            "agent_id": "legaltech_expert",
            "keywords": [
                "contract", "legal", "compliance", "document", "attorney",
                "law", "signature", "esign", "clause", "agreement", "regulation",
            ],
        },
        "logistics": {
            "agent_id": "logistics_expert",
            "keywords": [
                "shipping", "tracking", "warehouse", "delivery", "logistics",
                "supply chain", "fleet", "route", "carrier", "freight", "package",
            ],
        },
        "hrtech": {
            "agent_id": "hrtech_expert",
            "keywords": [
                "employee", "hiring", "payroll", "hr", "recruitment",
                "onboarding", "benefits", "performance", "applicant",
                "workforce", "talent",
            ],
        },
    }

    CONFIDENCE_THRESHOLD = 0.3
    MAX_EXPERTS = 3

    def detect_domains(
        self,
        project_overview: str,
        key_features: str = "",
        constraints: str = "",
    ) -> List[Tuple[str, float]]:
        """
        Analyze text and return activated domains with confidence scores.

        Args:
            project_overview: Main project description
            key_features: Optional key features text
            constraints: Optional constraints text

        Returns:
            List of (domain, confidence) tuples, sorted by confidence
        """
        combined_text = f"{project_overview} {key_features} {constraints}".lower()

        domain_scores = []

        for domain, config in self.KEYWORD_MAPPINGS.items():
            score = self._calculate_score(combined_text, config["keywords"])
            if score >= self.CONFIDENCE_THRESHOLD:
                domain_scores.append((domain, score))

        # Sort by confidence descending, limit to max experts
        domain_scores.sort(key=lambda x: x[1], reverse=True)

        return domain_scores[:self.MAX_EXPERTS]

    def _calculate_score(self, text: str, keywords: List[str]) -> float:
        """
        Calculate keyword match confidence score.

        Uses weighted scoring:
        - More keyword matches = higher score
        - Normalized by keyword list size
        """
        matches = 0
        for keyword in keywords:
            # Use word boundary matching for better accuracy
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, text):
                matches += 1

        # Calculate score (normalize to 0-1)
        if not keywords:
            return 0.0

        score = min(matches / (len(keywords) * 0.3), 1.0)
        return round(score, 2)

    def get_agent_id(self, domain: str) -> str:
        """Get agent ID for a domain."""
        config = self.KEYWORD_MAPPINGS.get(domain)
        return config["agent_id"] if config else None
