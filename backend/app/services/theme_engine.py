"""Theme consistency engine for maintaining brand voice across content."""

import logging
from collections import Counter
from datetime import datetime
from typing import Dict, List, Optional

from app.config import settings

logger = logging.getLogger(__name__)

# Brand voice archetypes with characteristics
BRAND_VOICE_ARCHETYPES = {
    "professional": {
        "traits": ["authoritative", "knowledgeable", "reliable", "clear"],
        "avoid": ["slang", "excessive emojis", "informal abbreviations"],
        "tone_words": ["discover", "expertise", "solutions", "proven", "results"],
        "emoji_frequency": "minimal",
    },
    "casual": {
        "traits": ["friendly", "approachable", "relatable", "warm"],
        "avoid": ["jargon", "overly formal language", "corporate speak"],
        "tone_words": ["hey", "awesome", "love", "check out", "grab"],
        "emoji_frequency": "moderate",
    },
    "bold": {
        "traits": ["confident", "direct", "energetic", "provocative"],
        "avoid": ["hedging language", "passive voice", "being wishy-washy"],
        "tone_words": ["game-changer", "unleash", "dominate", "crush it", "next level"],
        "emoji_frequency": "moderate",
    },
    "inspirational": {
        "traits": ["uplifting", "motivational", "empathetic", "visionary"],
        "avoid": ["negativity", "complaints", "mundane details"],
        "tone_words": ["transform", "believe", "journey", "dream", "together"],
        "emoji_frequency": "moderate",
    },
    "playful": {
        "traits": ["humorous", "witty", "creative", "surprising"],
        "avoid": ["boring language", "overly serious tone", "lengthy explanations"],
        "tone_words": ["surprise", "fun", "wild", "obsessed", "literally"],
        "emoji_frequency": "heavy",
    },
    "luxurious": {
        "traits": ["elegant", "exclusive", "sophisticated", "refined"],
        "avoid": ["casual language", "discounts language", "urgency tactics"],
        "tone_words": ["exquisite", "curated", "bespoke", "timeless", "artisan"],
        "emoji_frequency": "minimal",
    },
}

# Content pillar distribution targets
DEFAULT_PILLAR_DISTRIBUTION = {
    "educational": 0.25,
    "promotional": 0.20,
    "engagement": 0.25,
    "behind_the_scenes": 0.15,
    "testimonials": 0.15,
}


class ThemeEngineService:
    """Service for maintaining brand voice consistency and theme management."""

    def __init__(self):
        """Initialize the theme engine."""
        self._post_history: List[Dict] = []

    def get_brand_voice_guidelines(self, voice: str) -> Dict:
        """
        Get brand voice guidelines for content generation.

        Args:
            voice: Brand voice archetype name

        Returns:
            Voice guidelines dictionary
        """
        return BRAND_VOICE_ARCHETYPES.get(
            voice.lower(),
            BRAND_VOICE_ARCHETYPES["professional"]
        )

    def build_voice_prompt(self, business: Dict) -> str:
        """
        Build a brand voice system prompt for AI content generation.

        Args:
            business: Business profile data

        Returns:
            Formatted voice prompt string
        """
        voice = business.get("brand_voice", "professional")
        guidelines = self.get_brand_voice_guidelines(voice)

        return f"""BRAND VOICE CALIBRATION:
Voice Type: {voice.upper()}
Key Traits: {', '.join(guidelines['traits'])}
Words to Use: {', '.join(guidelines['tone_words'])}
Things to Avoid: {', '.join(guidelines['avoid'])}
Emoji Usage: {guidelines['emoji_frequency']}

ADDITIONAL BRAND CONTEXT:
- Industry: {business.get('industry', 'General')}
- Target Audience: {business.get('target_audience', 'General audience')}
- Unique Positioning: {', '.join(business.get('unique_selling_points', []))}

Maintain this voice consistently across all generated content. The content should
feel like it comes from one unified brand personality."""

    def score_content_consistency(
        self,
        content: str,
        business: Dict,
    ) -> Dict:
        """
        Score how well content matches the brand voice.

        Args:
            content: The content to evaluate
            business: Business profile data

        Returns:
            Consistency score and breakdown
        """
        voice = business.get("brand_voice", "professional")
        guidelines = self.get_brand_voice_guidelines(voice)

        content_lower = content.lower()

        # Score based on tone word usage
        tone_hits = sum(
            1 for word in guidelines["tone_words"]
            if word.lower() in content_lower
        )
        tone_score = min(1.0, tone_hits / max(1, len(guidelines["tone_words"]) * 0.3))

        # Score based on avoiding restricted patterns
        avoid_hits = sum(
            1 for pattern in guidelines["avoid"]
            if pattern.lower() in content_lower
        )
        avoid_penalty = min(1.0, avoid_hits * 0.2)

        # Emoji frequency check
        emoji_count = sum(1 for c in content if ord(c) > 127000)
        if guidelines["emoji_frequency"] == "minimal":
            emoji_score = 1.0 if emoji_count <= 2 else max(0.5, 1.0 - emoji_count * 0.1)
        elif guidelines["emoji_frequency"] == "heavy":
            emoji_score = min(1.0, emoji_count * 0.2) if emoji_count > 0 else 0.5
        else:
            emoji_score = 0.8  # Moderate is flexible

        # Calculate overall score
        overall_score = (tone_score * 0.4 + (1.0 - avoid_penalty) * 0.3 + emoji_score * 0.3)

        return {
            "overall_score": round(overall_score, 2),
            "tone_alignment": round(tone_score, 2),
            "guideline_compliance": round(1.0 - avoid_penalty, 2),
            "emoji_appropriateness": round(emoji_score, 2),
            "voice_type": voice,
        }

    def get_pillar_distribution(
        self,
        post_history: List[Dict],
        target_distribution: Optional[Dict] = None,
    ) -> Dict:
        """
        Analyze current content pillar distribution vs target.

        Args:
            post_history: List of past posts with pillar_type
            target_distribution: Target distribution (defaults to balanced)

        Returns:
            Distribution analysis with recommendations
        """
        if target_distribution is None:
            target_distribution = DEFAULT_PILLAR_DISTRIBUTION

        # Count actual distribution
        pillar_counts = Counter(
            post.get("pillar_type", "engagement") for post in post_history
        )
        total = sum(pillar_counts.values()) or 1

        actual_distribution = {
            pillar: count / total
            for pillar, count in pillar_counts.items()
        }

        # Calculate balance score
        balance_scores = {}
        recommendations = []

        for pillar, target in target_distribution.items():
            actual = actual_distribution.get(pillar, 0.0)
            deviation = abs(target - actual)
            balance_scores[pillar] = {
                "target": round(target, 2),
                "actual": round(actual, 2),
                "deviation": round(deviation, 2),
            }

            if actual < target - 0.1:
                recommendations.append(
                    f"Increase '{pillar}' content (currently {actual:.0%}, target {target:.0%})"
                )
            elif actual > target + 0.1:
                recommendations.append(
                    f"Reduce '{pillar}' content (currently {actual:.0%}, target {target:.0%})"
                )

        overall_balance = 1.0 - (
            sum(abs(target_distribution.get(p, 0) - actual_distribution.get(p, 0))
                for p in target_distribution) / 2
        )

        return {
            "overall_balance_score": round(max(0, overall_balance), 2),
            "pillar_breakdown": balance_scores,
            "recommendations": recommendations,
            "total_posts_analyzed": total,
        }

    def suggest_next_pillar(
        self,
        post_history: List[Dict],
        target_distribution: Optional[Dict] = None,
    ) -> str:
        """
        Suggest the next content pillar to use for balanced distribution.

        Args:
            post_history: List of past posts
            target_distribution: Target distribution weights

        Returns:
            Suggested pillar type string
        """
        if target_distribution is None:
            target_distribution = DEFAULT_PILLAR_DISTRIBUTION

        if not post_history:
            # Start with educational content
            return "educational"

        # Count recent posts by pillar
        pillar_counts = Counter(
            post.get("pillar_type", "engagement") for post in post_history
        )
        total = sum(pillar_counts.values()) or 1

        # Find the most underrepresented pillar
        max_deficit = -1.0
        suggested_pillar = "engagement"

        for pillar, target_weight in target_distribution.items():
            actual_weight = pillar_counts.get(pillar, 0) / total
            deficit = target_weight - actual_weight
            if deficit > max_deficit:
                max_deficit = deficit
                suggested_pillar = pillar

        return suggested_pillar

    def check_content_repetition(
        self,
        new_content: str,
        recent_posts: List[str],
        similarity_threshold: float = 0.7,
    ) -> Dict:
        """
        Check if new content is too similar to recent posts.

        Uses simple word overlap for fast checking.

        Args:
            new_content: Content to check
            recent_posts: List of recent post contents
            similarity_threshold: Maximum acceptable similarity

        Returns:
            Repetition check results
        """
        if not recent_posts:
            return {"is_repetitive": False, "max_similarity": 0.0, "similar_to_index": None}

        new_words = set(new_content.lower().split())
        max_similarity = 0.0
        most_similar_idx = None

        for idx, post in enumerate(recent_posts):
            post_words = set(post.lower().split())
            if not new_words or not post_words:
                continue

            # Jaccard similarity
            intersection = len(new_words & post_words)
            union = len(new_words | post_words)
            similarity = intersection / union if union > 0 else 0.0

            if similarity > max_similarity:
                max_similarity = similarity
                most_similar_idx = idx

        return {
            "is_repetitive": max_similarity >= similarity_threshold,
            "max_similarity": round(max_similarity, 3),
            "similar_to_index": most_similar_idx,
        }

    def get_theme_score(self, business: Dict, posts: List[Dict]) -> Dict:
        """
        Calculate overall theme consistency score.

        Args:
            business: Business profile
            posts: List of generated posts

        Returns:
            Theme score breakdown
        """
        if not posts:
            return {
                "overall_score": 0.0,
                "brand_voice_consistency": 0.0,
                "visual_consistency": 0.0,
                "content_pillar_balance": {},
                "recommendations": ["Generate some content to start tracking consistency."],
            }

        # Score each post for voice consistency
        voice_scores = []
        for post in posts:
            content = post.get("content", "")
            score = self.score_content_consistency(content, business)
            voice_scores.append(score["overall_score"])

        avg_voice_score = sum(voice_scores) / len(voice_scores) if voice_scores else 0.0

        # Get pillar distribution
        pillar_analysis = self.get_pillar_distribution(posts)

        # Visual consistency (based on whether brand colors are being used)
        visual_score = 0.8 if business.get("brand_colors") else 0.5

        overall = (avg_voice_score * 0.4 + pillar_analysis["overall_balance_score"] * 0.3 + visual_score * 0.3)

        recommendations = pillar_analysis["recommendations"]
        if avg_voice_score < 0.7:
            recommendations.append("Improve brand voice alignment in generated content.")
        if not business.get("brand_colors"):
            recommendations.append("Add brand colors to improve visual consistency.")

        return {
            "overall_score": round(overall, 2),
            "brand_voice_consistency": round(avg_voice_score, 2),
            "visual_consistency": round(visual_score, 2),
            "content_pillar_balance": pillar_analysis["pillar_breakdown"],
            "recommendations": recommendations,
        }


# Singleton instance
theme_engine_service = ThemeEngineService()
