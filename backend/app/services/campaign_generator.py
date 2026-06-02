"""AI Campaign Generator service for Meta Ads campaigns."""

import json
import logging
import random
from typing import Dict, List, Optional

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from app.config import settings

logger = logging.getLogger(__name__)

# Meta Ads best practices
META_ADS_GUIDELINES = {
    "headline_max_chars": 40,
    "primary_text_max_chars": 125,  # Visible without "See More"
    "description_max_chars": 30,
    "cta_options": [
        "LEARN_MORE", "SHOP_NOW", "SIGN_UP", "BOOK_NOW",
        "CONTACT_US", "GET_OFFER", "DOWNLOAD", "SUBSCRIBE",
        "ORDER_NOW", "GET_QUOTE", "APPLY_NOW", "WATCH_MORE",
    ],
    "ad_formats": ["single_image", "carousel", "video", "collection"],
    "placements": ["feed", "stories", "reels", "audience_network"],
}

# Hook type descriptions for prompt engineering
HOOK_TYPE_DESCRIPTIONS = {
    "pain_point": "Focus on a specific pain, frustration, or problem the audience faces. Make them feel understood.",
    "aspirational": "Paint a vivid picture of the ideal outcome. Make them desire the transformation.",
    "social_proof": "Leverage numbers, testimonials, or community to build trust and FOMO.",
    "curiosity": "Create an information gap that makes them need to click to find out more.",
    "urgency": "Create time pressure or scarcity that drives immediate action.",
    "contrarian": "Challenge conventional wisdom or common beliefs to stop the scroll.",
}


class CampaignGeneratorService:
    """Service for generating Meta Ads campaign angles and creatives."""

    def __init__(self):
        """Initialize the campaign generator with Bedrock client."""
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
        return f"""You are a world-class Meta Ads strategist and direct response copywriter.

BRAND BIBLE - Follow these guidelines strictly:
- Business Name: {business.get('name', 'Our Brand')}
- Industry: {business.get('industry', 'General')}
- Brand Voice: {business.get('brand_voice', 'professional')}
- Target Audience: {business.get('target_audience', 'General audience')}
- Unique Selling Points: {', '.join(business.get('unique_selling_points', []))}
- Brand Description: {business.get('description', '')}

META ADS BEST PRACTICES:
- Headlines must be under 40 characters (punchy, scroll-stopping)
- Primary text should hook within the first 125 characters (before "See More")
- Use pattern interrupts and emotional triggers
- Write in the language of the target audience (conversational, not corporate)
- Every creative must have a clear CTA
- Focus on benefits, not features
- Use specific numbers and social proof where possible
- Target the South African market context where relevant"""

    def _build_angles_prompt(
        self,
        campaign_objective: str,
        product_service: str,
        target_audience: Optional[str] = None,
    ) -> str:
        """Build prompt for generating 3 advertising angles."""
        audience_context = f"\nTARGET AUDIENCE: {target_audience}" if target_audience else ""

        return f"""Generate 3 distinct advertising ANGLES for a Meta Ads campaign.

CAMPAIGN OBJECTIVE: {campaign_objective}
PRODUCT/SERVICE: {product_service}{audience_context}

Each angle must use a DIFFERENT hook type from these options:
1. pain_point - Focus on a specific frustration or problem
2. aspirational - Paint the ideal outcome/transformation
3. social_proof - Leverage numbers, testimonials, community

For each angle, provide:
- hook_type: one of (pain_point, aspirational, social_proof)
- title: A short name for this angle (max 50 chars)
- description: Explain the angle strategy in 1-2 sentences
- target_emotion: The primary emotion this angle targets (e.g., frustration, desire, trust, curiosity)

OUTPUT FORMAT (JSON):
{{
    "angles": [
        {{
            "hook_type": "pain_point",
            "title": "Short angle name",
            "description": "Strategy explanation",
            "target_emotion": "frustration"
        }},
        {{
            "hook_type": "aspirational",
            "title": "Short angle name",
            "description": "Strategy explanation",
            "target_emotion": "desire"
        }},
        {{
            "hook_type": "social_proof",
            "title": "Short angle name",
            "description": "Strategy explanation",
            "target_emotion": "trust"
        }}
    ]
}}

Make each angle distinctly different in approach. They should feel like 3 different campaigns targeting the same product."""

    def _build_creatives_prompt(
        self,
        angle: Dict,
        product_service: str,
        campaign_objective: str,
        target_audience: Optional[str] = None,
    ) -> str:
        """Build prompt for generating 5 creatives per angle."""
        audience_context = f"\nTARGET AUDIENCE: {target_audience}" if target_audience else ""

        return f"""Generate 5 unique ad creative variations for this advertising angle.

ANGLE: {angle.get('title', '')}
HOOK TYPE: {angle.get('hook_type', '')}
ANGLE DESCRIPTION: {angle.get('description', '')}
TARGET EMOTION: {angle.get('target_emotion', '')}
PRODUCT/SERVICE: {product_service}
CAMPAIGN OBJECTIVE: {campaign_objective}{audience_context}

For each creative, provide:
- headline: Short, punchy (MAX 40 characters). Must stop the scroll.
- primary_text: Main ad copy optimized for Meta (hook in first 125 chars, then expand)
- description: Optional link description (max 30 chars)
- call_to_action: One of: LEARN_MORE, SHOP_NOW, SIGN_UP, BOOK_NOW, CONTACT_US, GET_OFFER, DOWNLOAD, SUBSCRIBE, ORDER_NOW, GET_QUOTE
- image_concept: Describe what the ad image/visual should show
- ad_format: One of: single_image, carousel, video, collection
- platform_placement: One of: feed, stories, reels, audience_network

RULES:
- Each creative must be distinctly different (different hook, angle, or format)
- Mix up ad formats and placements across the 5 creatives
- Headlines MUST be under 40 characters
- Primary text should be compelling and conversion-focused
- Image concepts should be specific and actionable for a designer

OUTPUT FORMAT (JSON):
{{
    "creatives": [
        {{
            "headline": "Max 40 char headline",
            "primary_text": "Full ad copy text...",
            "description": "Link description",
            "call_to_action": "SHOP_NOW",
            "image_concept": "Description of the visual",
            "ad_format": "single_image",
            "platform_placement": "feed"
        }}
    ]
}}

Generate 5 creatives that a media buyer would be excited to test."""

    async def generate_angles(
        self,
        business: Dict,
        campaign_objective: str,
        product_service: str,
        target_audience: Optional[str] = None,
    ) -> List[Dict]:
        """Generate 3 unique advertising angles for a campaign."""
        system_prompt = self._build_brand_bible_prompt(business)
        user_prompt = self._build_angles_prompt(
            campaign_objective=campaign_objective,
            product_service=product_service,
            target_audience=target_audience,
        )

        try:
            if self.client is None:
                logger.info("No Bedrock client available, using mock angles")
                return self._generate_mock_angles(product_service, campaign_objective)

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
            result = json.loads(content_text)
            return result.get("angles", [])

        except (ClientError, json.JSONDecodeError) as e:
            logger.error(f"Bedrock API error generating angles: {e}")
            return self._generate_mock_angles(product_service, campaign_objective)
        except Exception as e:
            logger.error(f"Unexpected error generating angles: {e}")
            return self._generate_mock_angles(product_service, campaign_objective)

    async def generate_creatives(
        self,
        business: Dict,
        angle: Dict,
        product_service: str,
        campaign_objective: str,
        target_audience: Optional[str] = None,
    ) -> List[Dict]:
        """Generate 5 creative variations for a specific angle."""
        system_prompt = self._build_brand_bible_prompt(business)
        user_prompt = self._build_creatives_prompt(
            angle=angle,
            product_service=product_service,
            campaign_objective=campaign_objective,
            target_audience=target_audience,
        )

        try:
            if self.client is None:
                logger.info("No Bedrock client available, using mock creatives")
                return self._generate_mock_creatives(angle, product_service)

            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 4096,
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
            result = json.loads(content_text)
            return result.get("creatives", [])

        except (ClientError, json.JSONDecodeError) as e:
            logger.error(f"Bedrock API error generating creatives: {e}")
            return self._generate_mock_creatives(angle, product_service)
        except Exception as e:
            logger.error(f"Unexpected error generating creatives: {e}")
            return self._generate_mock_creatives(angle, product_service)

    def _generate_mock_angles(
        self, product_service: str, campaign_objective: str
    ) -> List[Dict]:
        """Generate mock angles when Bedrock is unavailable."""
        return [
            {
                "hook_type": "pain_point",
                "title": f"The {product_service[:20]} Struggle",
                "description": (
                    f"Highlight the frustration people face without {product_service}. "
                    "Make them feel understood before presenting the solution."
                ),
                "target_emotion": "frustration",
            },
            {
                "hook_type": "aspirational",
                "title": f"Imagine Life With {product_service[:15]}",
                "description": (
                    "Paint a vivid picture of the transformation and ideal outcome. "
                    "Focus on the after-state and how life improves."
                ),
                "target_emotion": "desire",
            },
            {
                "hook_type": "social_proof",
                "title": f"Join 500+ Happy Customers",
                "description": (
                    "Leverage community size, testimonials, and results to build trust. "
                    "Use specific numbers and success stories."
                ),
                "target_emotion": "trust",
            },
        ]

    def _generate_mock_creatives(
        self, angle: Dict, product_service: str
    ) -> List[Dict]:
        """Generate mock creatives when Bedrock is unavailable."""
        hook_type = angle.get("hook_type", "pain_point")
        formats = ["single_image", "carousel", "video", "single_image", "collection"]
        placements = ["feed", "stories", "reels", "feed", "audience_network"]
        ctas = ["LEARN_MORE", "SHOP_NOW", "SIGN_UP", "GET_OFFER", "BOOK_NOW"]

        creatives = []
        for i in range(5):
            if hook_type == "pain_point":
                headlines = [
                    "Stop wasting time on this",
                    "Tired of the same results?",
                    "This mistake costs you daily",
                    "Why nothing has worked yet",
                    "The problem nobody talks about",
                ]
                primary_texts = [
                    f"You have been struggling with this for too long. {product_service} finally solves the problem you thought was unsolvable. Here is how it works...",
                    f"Every day without {product_service}, you are leaving results on the table. Most people do not realize the impact until they see the difference.",
                    f"If you have tried everything and nothing worked, it is not your fault. {product_service} takes a completely different approach.",
                    f"The old way is broken. You know it. We know it. That is exactly why we built {product_service} from the ground up.",
                    f"What if the thing holding you back was something you could fix today? {product_service} makes it possible.",
                ]
            elif hook_type == "aspirational":
                headlines = [
                    "Your best results start here",
                    "Imagine waking up to this",
                    "This is your next level",
                    "The life you deserve awaits",
                    "Transform in just 30 days",
                ]
                primary_texts = [
                    f"Imagine having everything sorted. {product_service} makes that your reality, not just a dream. Start your transformation today.",
                    f"Picture this: you wake up and everything just works. That is what life looks like with {product_service}. Join thousands who made the switch.",
                    f"Your competitors are already using {product_service} to get ahead. The question is not if you should start, but how soon you can begin.",
                    f"Six months from now, you will wish you started today. {product_service} is the fastest path to the results you have been dreaming about.",
                    f"Success leaves clues. The top performers all have one thing in common: {product_service}. Now it is your turn.",
                ]
            else:  # social_proof
                headlines = [
                    "Join 500+ SA businesses",
                    "See why they switched",
                    "Rated #1 by our customers",
                    "Real results, real people",
                    "The reviews speak volumes",
                ]
                primary_texts = [
                    f"Over 500 South African businesses already trust {product_service}. See why they rated us 4.9/5 stars and never looked back.",
                    f"\"Best decision we ever made\" - that is what our customers say about {product_service}. Join the community and see for yourself.",
                    f"When 93% of customers recommend you to their friends, you know you are doing something right. Discover {product_service} today.",
                    f"From Cape Town to Joburg, businesses are switching to {product_service}. Here is what they are saying about the results...",
                    f"Do not take our word for it. See the actual results our customers are getting with {product_service}. Numbers do not lie.",
                ]

            creatives.append({
                "headline": headlines[i][:40],
                "primary_text": primary_texts[i],
                "description": f"Try {product_service[:20]} now",
                "call_to_action": ctas[i],
                "image_concept": f"Professional photo showing {product_service} in action with happy customers, bright and clean aesthetic, brand colors prominent",
                "ad_format": formats[i],
                "platform_placement": placements[i],
            })

        return creatives

    async def generate_creative_image(
        self,
        image_concept: str,
        brand_colors: Optional[List[str]] = None,
        business_name: Optional[str] = None,
        industry: Optional[str] = None,
        placement: str = "feed",
    ) -> Optional[str]:
        """Generate an image for a campaign creative using Bria AI.

        Args:
            image_concept: The image concept description from the creative.
            brand_colors: Brand color palette for context.
            business_name: Business name for context.
            industry: Industry for context.
            placement: Ad placement (feed, stories, reels) to determine dimensions.

        Returns:
            Base64-encoded image string, or None if generation fails.
        """
        from app.services.image_generator import image_generator_service, _build_image_prompt

        # Map placement to platform dimensions
        placement_to_platform = {
            "feed": "instagram_feed",
            "stories": "instagram_story",
            "reels": "tiktok",
            "audience_network": "facebook_feed",
        }
        platform = placement_to_platform.get(placement, "instagram_feed")

        prompt = _build_image_prompt(
            text=image_concept,
            brand_colors=brand_colors,
            business_name=business_name,
            industry=industry,
            style="bold_text",
            platform=platform,
        )

        from app.services.image_generator import PLATFORM_DIMENSIONS
        dims = PLATFORM_DIMENSIONS.get(platform, PLATFORM_DIMENSIONS["instagram_feed"])

        image_base64 = image_generator_service.generate_image_ai(
            prompt=prompt,
            width=dims["width"],
            height=dims["height"],
        )

        return image_base64


# Singleton instance
campaign_generator_service = CampaignGeneratorService()
