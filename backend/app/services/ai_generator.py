"""AI Content Generator service using AWS Bedrock (Claude)."""

import json
import logging
import uuid
from typing import Dict, List, Optional

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from app.config import settings

logger = logging.getLogger(__name__)


# Platform-specific content guidelines
PLATFORM_GUIDELINES = {
    "tiktok": {
        "max_length": 300,
        "style": "Short, punchy, trend-driven. Use casual language, slang acceptable. "
                 "Hook viewer in first 2 seconds with text. Include CTA. Emoji-friendly.",
        "hashtag_count": 5,
        "dimensions": "1080x1920 (9:16 vertical)",
    },
    "instagram": {
        "max_length": 2200,
        "style": "Visual-first storytelling. Mix short punchy lines with longer narrative. "
                 "Use line breaks for readability. Start with a hook. End with CTA or question. "
                 "Aesthetic and polished tone.",
        "hashtag_count": 20,
        "dimensions": "1080x1080 (feed) or 1080x1920 (story/reel)",
    },
    "facebook": {
        "max_length": 5000,
        "style": "Conversational and engaging. Longer form storytelling welcome. "
                 "Ask questions to drive comments. Use emotional triggers. "
                 "Include link previews when possible. Professional but approachable.",
        "hashtag_count": 5,
        "dimensions": "1200x630 (feed) or 1080x1920 (story)",
    },
}

# Content pillar prompt templates
PILLAR_PROMPTS = {
    "educational": (
        "Create an educational post that teaches the audience something valuable "
        "about {industry}. Share a tip, how-to, or little-known fact. Position the "
        "business as a knowledgeable authority. Make it actionable and shareable."
    ),
    "promotional": (
        "Create a promotional post that highlights the product/service benefits without "
        "being overly salesy. Focus on the transformation or outcome the customer gets. "
        "Include a clear but natural call-to-action. Use social proof if possible."
    ),
    "engagement": (
        "Create a highly interactive post designed to maximize comments and shares. "
        "Ask a thought-provoking question, create a poll, or start a conversation "
        "related to {industry}. Make it easy and fun to respond."
    ),
    "behind_the_scenes": (
        "Create a behind-the-scenes post that humanizes the brand. Show the team, "
        "the process, or the story behind the business. Build trust through transparency "
        "and authenticity. Make followers feel like insiders."
    ),
    "testimonials": (
        "Create a post featuring customer success or testimonial content. Frame it as "
        "a story of transformation. Highlight specific results. Make it relatable for "
        "potential customers. Include gratitude and community building."
    ),
}

# Engagement hooks library
ENGAGEMENT_HOOKS = [
    "Stop scrolling - this changes everything about {topic}",
    "Most people get this wrong about {topic}. Here's the truth:",
    "I wish someone told me this sooner about {topic}:",
    "Hot take: {topic} is not what you think it is",
    "The {industry} secret nobody talks about:",
    "POV: You just discovered {topic}",
    "Save this for later - you'll thank me:",
    "Unpopular opinion about {topic}:",
]


class AIGeneratorService:
    """Service for generating AI-powered social media content using AWS Bedrock."""

    def __init__(self):
        """Initialize the AI generator with Bedrock client."""
        self._client = None

    @property
    def client(self):
        """Lazy initialization of boto3 Bedrock client."""
        if self._client is None:
            try:
                session_kwargs = {"region_name": settings.aws_region}
                if settings.aws_access_key_id and settings.aws_secret_access_key:
                    session_kwargs["aws_access_key_id"] = settings.aws_access_key_id
                    session_kwargs["aws_secret_access_key"] = settings.aws_secret_access_key

                session = boto3.Session(**session_kwargs)
                self._client = session.client("bedrock-runtime")
            except NoCredentialsError:
                logger.warning("AWS credentials not configured. Using mock responses.")
                self._client = None
        return self._client

    def _build_brand_bible_prompt(self, business: Dict) -> str:
        """Build brand bible system prompt for consistent voice."""
        return f"""You are a world-class social media content creator and brand strategist.

BRAND BIBLE - Follow these guidelines strictly:
- Business Name: {business.get('name', 'Our Brand')}
- Industry: {business.get('industry', 'General')}
- Brand Voice: {business.get('brand_voice', 'professional')}
- Target Audience: {business.get('target_audience', 'General audience')}
- Unique Selling Points: {', '.join(business.get('unique_selling_points', []))}
- Brand Description: {business.get('description', '')}

VOICE GUIDELINES:
- Maintain a {business.get('brand_voice', 'professional')} tone throughout
- Speak directly to the target audience
- Reference the brand's unique value proposition naturally
- Be authentic - avoid generic marketing language
- Match the energy level to the brand voice

CONTENT RULES:
- Never use offensive or controversial content
- Stay on-brand at all times
- Include value in every post (entertain, educate, or inspire)
- Use power words that resonate with the target audience
- Create FOMO or urgency when appropriate for promotional content"""

    def _build_generation_prompt(
        self,
        platform: str,
        pillar_type: str,
        business: Dict,
        topic: Optional[str] = None,
        language: str = "en",
        num_variants: int = 2,
    ) -> str:
        """Build the content generation prompt."""
        guidelines = PLATFORM_GUIDELINES.get(platform, PLATFORM_GUIDELINES["instagram"])
        pillar_prompt = PILLAR_PROMPTS.get(pillar_type, PILLAR_PROMPTS["engagement"])
        pillar_prompt = pillar_prompt.format(industry=business.get("industry", "business"))

        topic_instruction = ""
        if topic:
            topic_instruction = f"\nSPECIFIC TOPIC: Create content about: {topic}"

        language_instruction = ""
        if language != "en":
            language_instruction = f"\nLANGUAGE: Generate all content in language code: {language}"

        return f"""Generate {num_variants} unique social media post variants for {platform.upper()}.

PLATFORM REQUIREMENTS:
- Maximum length: {guidelines['max_length']} characters
- Style: {guidelines['style']}
- Suggested hashtag count: {guidelines['hashtag_count']}

CONTENT PILLAR: {pillar_type.upper()}
{pillar_prompt}
{topic_instruction}
{language_instruction}

REQUIREMENTS FOR EACH VARIANT:
1. Start with an attention-grabbing hook (first line must stop the scroll)
2. Include a clear call-to-action
3. Suggest relevant hashtags (mix trending + niche)
4. Add an engagement question or prompt
5. Each variant must be distinctly different in approach/angle

OUTPUT FORMAT (JSON):
{{
    "variants": [
        {{
            "content": "The full post text",
            "hashtags": ["hashtag1", "hashtag2", ...],
            "engagement_hook": "The hook/CTA used",
            "estimated_engagement": "high/medium/low"
        }}
    ]
}}

Generate compelling, scroll-stopping content that drives engagement."""

    async def generate_content(
        self,
        business: Dict,
        platform: str,
        pillar_type: str = "engagement",
        topic: Optional[str] = None,
        language: str = "en",
        num_variants: int = 2,
    ) -> List[Dict]:
        """
        Generate social media content using AWS Bedrock Claude.

        Args:
            business: Business profile data
            platform: Target platform (tiktok, instagram, facebook)
            pillar_type: Content pillar type
            topic: Optional specific topic
            language: Output language code
            num_variants: Number of variants to generate

        Returns:
            List of content variant dictionaries
        """
        system_prompt = self._build_brand_bible_prompt(business)
        user_prompt = self._build_generation_prompt(
            platform=platform,
            pillar_type=pillar_type,
            business=business,
            topic=topic,
            language=language,
            num_variants=num_variants,
        )

        try:
            if self.client is None:
                logger.info("No Bedrock client available, using mock generation")
                return self._generate_mock_content(
                    business, platform, pillar_type, num_variants
                )

            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 2048,
                "system": system_prompt,
                "messages": [
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.8,
                "top_p": 0.9,
            })

            response = self.client.invoke_model(
                modelId=settings.bedrock_model_id,
                body=body,
                contentType="application/json",
                accept="application/json",
            )

            response_body = json.loads(response["body"].read())
            content_text = response_body["content"][0]["text"]

            # Parse the JSON response
            result = json.loads(content_text)
            return result.get("variants", [])

        except (ClientError, json.JSONDecodeError) as e:
            logger.error(f"Bedrock API error: {e}")
            return self._generate_mock_content(
                business, platform, pillar_type, num_variants
            )
        except Exception as e:
            logger.error(f"Unexpected error in content generation: {e}")
            return self._generate_mock_content(
                business, platform, pillar_type, num_variants
            )

    def _generate_mock_content(
        self,
        business: Dict,
        platform: str,
        pillar_type: str,
        num_variants: int,
    ) -> List[Dict]:
        """Generate mock content when Bedrock is unavailable."""
        variant_group = str(uuid.uuid4())[:8]
        guidelines = PLATFORM_GUIDELINES.get(platform, PLATFORM_GUIDELINES["instagram"])
        business_name = business.get("name", "Our Brand")
        industry = business.get("industry", "business")

        variants = []
        for i in range(num_variants):
            if pillar_type == "educational":
                content = (
                    f"Did you know? Here's a game-changing {industry} tip that most people miss.\n\n"
                    f"At {business_name}, we've learned that success comes from understanding "
                    f"the fundamentals.\n\n"
                    f"Save this post for later - your future self will thank you!\n\n"
                    f"Variant {i + 1}: What's your biggest {industry} challenge? Drop it below!"
                )
            elif pillar_type == "promotional":
                content = (
                    f"Transform your {industry} results with {business_name}.\n\n"
                    f"Our clients see real results because we focus on what matters most: "
                    f"delivering value that makes a difference.\n\n"
                    f"Variant {i + 1}: Ready to level up? Link in bio!"
                )
            elif pillar_type == "behind_the_scenes":
                content = (
                    f"A peek behind the curtain at {business_name}.\n\n"
                    f"Every day, our team works to bring you the best in {industry}. "
                    f"Here's what that looks like in action.\n\n"
                    f"Variant {i + 1}: Want to see more of our process? Let us know!"
                )
            elif pillar_type == "testimonials":
                content = (
                    f"Another amazing result from our {business_name} community!\n\n"
                    f"When our clients succeed, we succeed. This is why we do what we do "
                    f"in the {industry} space.\n\n"
                    f"Variant {i + 1}: Share your success story with us!"
                )
            else:  # engagement
                content = (
                    f"Quick question for our {industry} community:\n\n"
                    f"What's the one thing you wish you knew when you started?\n\n"
                    f"At {business_name}, we love hearing from you. Drop your answer "
                    f"below and let's learn from each other!\n\n"
                    f"Variant {i + 1}"
                )

            hashtags = [
                f"{industry.lower().replace(' ', '')}",
                f"{business_name.lower().replace(' ', '')}",
                f"{platform}marketing",
                "socialmedia",
                "growthmindset",
                f"{pillar_type}content",
            ]

            variants.append({
                "content": content[:guidelines["max_length"]],
                "hashtags": hashtags[:guidelines["hashtag_count"]],
                "engagement_hook": f"Engaging {pillar_type} hook for {platform}",
                "estimated_engagement": "medium",
                "variant_group": variant_group,
            })

        return variants

    async def generate_hashtags(
        self,
        business: Dict,
        platform: str,
        content: str,
        count: int = 10,
    ) -> List[str]:
        """Generate relevant hashtags for content."""
        industry = business.get("industry", "business")
        name = business.get("name", "brand")

        # Return curated hashtag suggestions based on content
        base_hashtags = [
            f"#{industry.lower().replace(' ', '')}",
            f"#{name.lower().replace(' ', '')}",
            f"#{platform}marketing",
            "#socialmediamarketing",
            "#contentcreator",
            "#digitalmarketing",
            "#brandbuilding",
            "#entrepreneurlife",
            "#marketingtips",
            "#growyourbusiness",
        ]
        return base_hashtags[:count]


# Singleton instance
ai_generator_service = AIGeneratorService()
