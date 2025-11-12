from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class ModerationCategory(str, Enum):
    """Content moderation categories"""
    SAFE = "safe"
    VIOLENCE_THREATS = "violence_threats"
    OBSCENE = "obscene"
    SELF_HARM = "self_harm"
    ILLEGAL = "illegal"
    SEXUAL_EXPLICIT = "sexual_explicit"
    HATE_DISCRIMINATION = "hate_discrimination"
    DANGEROUS = "dangerous"
    CRIMINAL = "criminal"
    GORE = "gore"


CATEGORY_DISPLAY_NAMES = {
    ModerationCategory.SAFE: "Safe",
    ModerationCategory.VIOLENCE_THREATS: "Violence & Threats",
    ModerationCategory.OBSCENE: "Obscene",
    ModerationCategory.SELF_HARM: "Self Harm",
    ModerationCategory.ILLEGAL: "Illegal Content",
    ModerationCategory.SEXUAL_EXPLICIT: "Sexual Explicit",
    ModerationCategory.HATE_DISCRIMINATION: "Hate & Discrimination",
    ModerationCategory.DANGEROUS: "Dangerous",
    ModerationCategory.CRIMINAL: "Criminal",
    ModerationCategory.GORE: "Gore"
}

CATEGORY_DESCRIPTIONS = {
    ModerationCategory.SAFE: "Safe content, no violations detected",
    ModerationCategory.VIOLENCE_THREATS: "Violence, threats, weapons in threatening context",
    ModerationCategory.OBSCENE: "Obscene language, profanity, vulgar content",
    ModerationCategory.SELF_HARM: "Suicide, self-harm, eating disorders",
    ModerationCategory.ILLEGAL: "Anti-state content, historical distortion (Vietnam Cybersecurity Law)",
    ModerationCategory.SEXUAL_EXPLICIT: "Pornography, nudity, explicit sexual content",
    ModerationCategory.HATE_DISCRIMINATION: "Hate speech, discrimination based on race/religion/gender",
    ModerationCategory.DANGEROUS: "Drugs, controlled substances, drug paraphernalia, substance abuse",
    ModerationCategory.CRIMINAL: "Weapon trafficking, scams, fraud, smuggling, criminal activities",
    ModerationCategory.GORE: "Blood, graphic violence, severe injuries, accident scenes"
}


# Request Models
class TextModerationRequest(BaseModel):
    """Request model for text moderation"""
    text: str = Field(..., description="Text content to moderate", min_length=1)


class ImageModerationRequest(BaseModel):
    """Request model for image moderation"""
    image_url: Optional[str] = Field(None, description="URL to image file")
    image_base64: Optional[str] = Field(None, description="Base64 encoded image (JPEG/PNG)")


class VideoModerationRequest(BaseModel):
    """Request model for video moderation"""
    video_url: Optional[str] = Field(None, description="URL to video file")
    sampling_fps: float = Field(default=0.5, ge=0.1, le=2.0, description="Frame sampling rate")


# Response Models
class TextModerationOutput(BaseModel):
    """Structured output for text moderation"""
    category: ModerationCategory = Field(description="Classification category")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score")
    reasoning: str = Field(description="Explanation for decision")


class ImageAnalysis(BaseModel):
    """Analysis details for image moderation"""
    detected_elements: List[str] = Field(default_factory=list, description="Key objects detected")
    red_flags: List[str] = Field(default_factory=list, description="Concerning elements")
    context_assessment: str = Field(default="other", description="Context type")
    is_medical_professional_context: bool = Field(default=False)


class ImageModerationOutput(BaseModel):
    """Structured output for image moderation"""
    category: ModerationCategory = Field(description="Classification category")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score")
    reasoning: str = Field(description="Explanation for decision")
    detected_elements: List[str] = Field(default_factory=list)
    red_flags: List[str] = Field(default_factory=list)
    context_assessment: str = Field(default="other")
    is_medical_professional_context: bool = Field(default=False)


class TextModerationResponse(BaseModel):
    """Response model for text moderation"""
    category: str = Field(description="Display name of category")
    category_code: str = Field(description="Internal category code")
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str


class ImageModerationResponse(BaseModel):
    """Response model for image moderation"""
    category: str
    category_code: str
    confidence: float
    reasoning: str
    analysis: ImageAnalysis


class FrameModerationResult(BaseModel):
    """Result for a single video frame"""
    timestamp: float = Field(description="Timestamp in seconds")
    frame_index: int
    category: str
    category_code: str
    confidence: float
    reasoning: str
    analysis: Optional[ImageAnalysis] = None


class VideoModerationSummary(BaseModel):
    """Summary statistics for video moderation"""
    total_frames: int
    flagged_frames: int
    flagged_percentage: float
    audio_safe: bool


class VideoModerationResponse(BaseModel):
    """Response model for video moderation"""
    overall_decision: str
    overall_decision_code: str
    overall_confidence: float
    flagged_content: List[str]
    audio_moderation: TextModerationResponse
    frame_moderation: List[FrameModerationResult]
    summary: VideoModerationSummary