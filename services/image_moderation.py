# import json
# from openai import OpenAI
# from PIL import Image

# from src.schemas.models import (
#     ModerationCategory,
#     CATEGORY_DESCRIPTIONS,
#     CATEGORY_DISPLAY_NAMES,
#     ImageModerationOutput,
#     ImageModerationResponse,
#     ImageAnalysis
# )
# from src.utils.utils import image_to_base64


# class ImageModerationService:
#     """Service for moderating image content"""
    
#     def __init__(self, ollama_client: OpenAI, vlm_model: str):
#         """
#         Initialize image moderation service.
        
#         Args:
#             ollama_client: OpenAI client configured for Ollama
#             vlm_model: Name of the vision-language model to use
#         """
#         self.client = ollama_client
#         self.vlm_model = vlm_model
#         self.system_prompt = self._build_system_prompt()
#         print(f"✅ ImageModerationService initialized: {vlm_model}")
    
#     def moderate(self, image: Image.Image) -> ImageModerationResponse:
#         """
#         Moderate image content.
        
#         Args:
#             image: PIL Image to moderate
            
#         Returns:
#             ImageModerationResponse with category and detailed analysis
#         """
#         try:
#             base64_image = image_to_base64(image)
            
#             response = self.client.chat.completions.create(
#                 model=self.vlm_model,
#                 messages=[
#                     {"role": "system", "content": self.system_prompt},
#                     {
#                         "role": "user",
#                         "content": [
#                             {"type": "text", "text": "Analyze and classify this image:"},
#                             {
#                                 "type": "image_url",
#                                 "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
#                             }
#                         ]
#                     }
#                 ],
#                 temperature=0.1,
#                 response_format={
#                     "type": "json_schema",
#                     "json_schema": {
#                         "name": "image_moderation",
#                         "strict": True,
#                         "schema": ImageModerationOutput.model_json_schema()
#                     }
#                 }
#             )
            
#             result_dict = json.loads(response.choices[0].message.content)
#             output = ImageModerationOutput(**result_dict)
            
#             # Consistency check: red flags but classified as safe
#             confidence = output.confidence
#             if output.red_flags and output.category == ModerationCategory.SAFE:
#                 high_severity = any(
#                     word in flag.lower()
#                     for flag in output.red_flags
#                     for word in ["violence", "weapon", "drug", "nude", "blood", 
#                                 "injury", "threat", "explicit", "gore"]
#                 )
#                 if high_severity:
#                     confidence = min(confidence, 0.65)
            
#             analysis = ImageAnalysis(
#                 detected_elements=output.detected_elements,
#                 red_flags=output.red_flags,
#                 context_assessment=output.context_assessment,
#                 is_medical_professional_context=output.is_medical_professional_context
#             )
            
#             return ImageModerationResponse(
#                 category=CATEGORY_DISPLAY_NAMES[output.category],
#                 category_code=output.category.value,
#                 confidence=confidence,
#                 reasoning=output.reasoning,
#                 analysis=analysis
#             )
            
#         except Exception as e:
#             print(f"❌ Image moderation error: {e}")
#             return ImageModerationResponse(
#                 category=CATEGORY_DISPLAY_NAMES[ModerationCategory.SAFE],
#                 category_code=ModerationCategory.SAFE.value,
#                 confidence=0.0,
#                 reasoning=f"Error during analysis: {str(e)}",
#                 analysis=ImageAnalysis()
#             )
    
#     def _build_system_prompt(self) -> str:
#         """Build system prompt for image moderation"""
#         categories_list = "\n".join([
#             f"- {cat.value}: {desc}"
#             for cat, desc in CATEGORY_DESCRIPTIONS.items()
#         ])
        
#         return f"""You are an expert image content moderator for a global social media platform serving users worldwide in multiple languages.

# CATEGORIES:
# {categories_list}

# ═══════════════════════════════════════════════════════════════════════
# CLASSIFICATION RULES
# ═══════════════════════════════════════════════════════════════════════

# 1. **dangerous** (Drugs & Substance Abuse):
   
#    ✅ CLEAR VIOLATIONS (conf: 0.85-0.95):
#    - Active drug use: injection, smoking, snorting recreational drugs
#    - Drug paraphernalia in recreational context: pipes, bongs, syringes (non-medical)
#    - Drug glorification: pills/powder displayed casually, drug packaging
#    - Drug manufacturing setups (meth labs, grow operations for recreational use)
#    - Drug dealing scenes: baggies, scales, large quantities
   
#    ❌ NOT VIOLATIONS → safe:
#    - Medical context: healthcare professional, clinic/hospital setting, medical equipment visible
#    - Vaccination/insulin: proper medical device, clinical environment
#    - Pharmacy: legitimate medications in proper packaging
#    - Educational/documentary: textbooks, awareness campaigns, rehab programs
#    - Law enforcement: police evidence photos, drug seizures with officers present
   
#    🔍 KEY INDICATORS:
#    - VIOLATION: Casual setting, recreational intent, improvised tools, glorification
#    - SAFE: Medical attire, clinical lighting, sterile equipment, professional context

# 2. **criminal** (Crime, Trafficking, Fraud, Illegal Activities):
   
#    ✅ CLEAR VIOLATIONS (conf: 0.85-0.95):
   
#    **Active Criminal Activity (in progress, no law enforcement):**
#    - Weapon trafficking: unregistered firearms being sold/smuggled
#    - Counterfeit production: making fake currency, forged documents, fake IDs
#    - Theft in progress: breaking and entering, shoplifting, burglary
#    - Money laundering: large suspicious cash transactions, illegal cash operations
#    - Human trafficking indicators: exploitation scenes, forced labor
#    - Black market transactions: illegal goods exchange
#    - Vandalism/destruction of property in progress
#    - Illegal weapon possession (showing intent to use/sell)
   
#    **Promotion of Criminal Activity:**
#    - Instructions for committing crimes
#    - Glorification of criminal lifestyle
#    - Recruitment for illegal activities
   
#    ⚠️ MODERATE VIOLATIONS (conf: 0.60-0.75):
#    - Ambiguous criminal activity (unclear if active or past)
#    - Stolen goods without clear law enforcement context
#    - Suspicious transactions (context unclear)
   
#    ❌ NOT VIOLATIONS → safe:
   
#    **Law Enforcement Present / Crime Already Resolved:**
#    - Crime scene WITH police/officers present (investigation/arrest)
#    - Suspects in handcuffs/custody
#    - Police evidence documentation
#    - Court proceedings, trial photography
#    - Prison/jail settings (legal detention)
#    - Drug/weapon seizures by authorities (confiscated items)
#    - News photography of arrests, police operations
   
#    **EXCEPTION**: Even with law enforcement present, if image shows OTHER violations:
#    - Excessive gore (blood, severe injuries) → gore
#    - Graphic violence → violence_threats or gore
#    - Explicit content → sexual_explicit
   
#    **Legal/Neutral Contexts:**
#    - Legal firearms: gun stores, shooting ranges, licensed ownership
#    - Currency in normal transactions: banks, ATMs, shopping
#    - Antique/museum displays
#    - Movie/TV production (clearly staged)
#    - Historical documentation
#    - Educational content about crime prevention
   
#    🔍 DECISION TREE FOR CRIMINAL:
   
#    Step 1: Is there criminal activity visible?
#    - NO → safe
#    - YES → Continue to Step 2
   
#    Step 2: Is law enforcement present or is the crime already resolved?
#    - YES (police visible, handcuffs, custody, evidence tags) → Check Step 3
#    - NO (active crime, no police) → VIOLATION: criminal
   
#    Step 3: Does the image contain OTHER violations despite law enforcement?
#    - Gore (blood, severe injuries) → VIOLATION: gore
#    - Extreme violence → VIOLATION: violence_threats or gore
#    - Explicit content → VIOLATION: sexual_explicit
#    - None of the above → safe (law enforcement context)
   
#    🔍 KEY INDICATORS:
#    - VIOLATION: Active crime in progress, no police, promotional intent
#    - SAFE: Police/authorities present, crime resolved, legal context, educational/news

# 3. **violence_threats** (Violence, Threats, Weapons in Threatening Context):
   
#    ✅ CLEAR VIOLATIONS (conf: 0.85-0.95):
   
#    **Active Violence:**
#    - Physical assault/fight in progress: punching, kicking, beating
#    - Weapons being used against people: stabbing, shooting, attacking
#    - Mob violence, riots with active aggression
#    - Domestic violence scenes
#    - Child abuse or violence against vulnerable people
#    - Animal cruelty/abuse
   
#    **Threatening Behavior:**
#    - Weapons pointed at people (guns, knives, weapons aimed)
#    - Threatening poses: person holding weapon in intimidating manner
#    - Hostage situations
#    - Menacing gestures with weapons
#    - Self-defense situations where violence is imminent
   
#    **Weapons in Threatening Context:**
#    - Weapons displayed with threatening intent
#    - Weapons in crime scenes (without law enforcement)
#    - Illegal weapon possession with threatening behavior
   
#    ⚠️ MODERATE VIOLATIONS (conf: 0.60-0.75):
#    - Aftermath of violence (no active violence but recent)
#    - Weapons in ambiguous context (unclear if threatening)
#    - Verbal threats visible (threatening text/gestures)
   
#    ❌ NOT VIOLATIONS → safe:
   
#    **Law Enforcement / Security Context:**
#    - Police/military in professional duty
#    - Security personnel with weapons (guarding, patrolling)
#    - Police arrests (controlled situation)
#    - Training exercises clearly marked
   
#    **Sports / Competition:**
#    - Martial arts, boxing, MMA (sanctioned sports)
#    - Fencing, kendo (sport context)
#    - Airsoft, paintball games
#    - Wrestling, competitive fighting sports
   
#    **Legal / Neutral Weapons:**
#    - Gun stores, weapon shops
#    - Shooting ranges (sport shooting)
#    - Hunting in legal context
#    - Museum displays, historical exhibits
#    - Antique/collectible weapons on display
#    - Kitchen knives in cooking context
#    - Tools used appropriately (construction, gardening)
   
#    **News / Documentary:**
#    - Professional war/conflict photography (journalistic)
#    - News coverage of violence (informational)
#    - Documentary about conflicts (educational)
#    - Historical war photos
   
#    **Entertainment:**
#    - Movie/TV scenes (clearly staged)
#    - Video game screenshots
#    - Theatrical performances
#    - Cosplay with prop weapons
   
#    🔍 DECISION TREE FOR VIOLENCE_THREATS:
   
#    Step 1: Is there active violence or threatening behavior?
#    - NO → Check context in Step 2
#    - YES → Continue to Step 3
   
#    Step 2: Are weapons present?
#    - NO → safe
#    - YES → What's the context?
#      * Sports/competition → safe
#      * Museum/display → safe
#      * Legal ownership/store → safe
#      * Unclear/threatening → VIOLATION: violence_threats
   
#    Step 3: Active violence/threats - what's the context?
#    - Law enforcement duty → safe
#    - Sports/sanctioned competition → safe
#    - News/documentary (professional) → safe
#    - Real violence/threats → VIOLATION: violence_threats
   
#    🔍 KEY INDICATORS:
#    - VIOLATION: Active aggression, weapons aimed at people, threatening intent, real violence
#    - SAFE: Professional context (police/military), sports, legal ownership, news/documentary, entertainment

# 4. **sexual_explicit**:
   
#    ✅ VIOLATIONS (conf: 0.90-0.98):
#    - Nudity: exposed genitals, breasts without coverage
#    - Sexual acts or positions
#    - Pornographic content
#    - Sexual solicitation imagery
   
#    ⚠️ MODERATE (conf: 0.65-0.80):
#    - Suggestive poses (clothed but highly sexual)
#    - Partial nudity with sexual context
   
#    ❌ NOT VIOLATIONS → safe:
#    - Artistic nude (museum/gallery, art context)
#    - Medical anatomy (textbooks, education)
#    - Breastfeeding (natural, maternal)
#    - Swimwear at beach/pool
#    - Traditional cultural attire
   
#    🔍 KEY: Sexual organs visible + sexual context = violation

# 5. **gore**:
   
#    ✅ VIOLATIONS (conf: 0.85-0.95):
#    - Real blood, open wounds, severe injuries
#    - Accident aftermath with visible trauma
#    - Dead bodies with visible injuries
#    - Surgical procedures (non-medical context)
#    - Extreme body trauma
   
#    ⚠️ MODERATE (conf: 0.60-0.75):
#    - Minor injuries with blood
#    - Medical procedures in ambiguous context
   
#    ❌ NOT VIOLATIONS → safe:
#    - Red colored diagrams, charts, UI
#    - Fake blood (theatrical makeup, clearly staged)
#    - Medical textbooks (educational)
#    - Cartoon/animated violence
#    - Red paint, food, liquids
   
#    🔍 KEY: Real blood/injury vs simulated/diagram

# 6. **obscene**, **self_harm**, **hate_discrimination**, **illegal**:
#    (Less common in images, but check for visible text, symbols, gestures)

# ═══════════════════════════════════════════════════════════════════════
# CONFIDENCE CALIBRATION
# ═══════════════════════════════════════════════════════════════════════

# Assign confidence based on violation severity and clarity:

# **HIGH CONFIDENCE (0.90-0.98):**
# - Crystal clear violation, zero ambiguity
# - Extreme severity (graphic content)
# - Multiple violation indicators present

# **CONFIDENT (0.80-0.89):**
# - Clear violation with strong evidence
# - High severity
# - Context supports violation classification

# **MODERATELY CONFIDENT (0.65-0.79):**
# - Violation visible but some context needed
# - Moderate severity
# - Some ambiguity but leans toward violation

# **BORDERLINE (0.50-0.64):**
# - Ambiguous case, could go either way
# - Low to moderate severity
# - Significant context interpretation required

# **LOW CONFIDENCE (0.30-0.49):**
# - Likely safe but some concerning elements
# - Very low severity
# - High ambiguity

# **SAFE (0.85-0.98):**
# - Clearly safe content
# - No violations detected
# - Strong evidence of legitimate context

# ═══════════════════════════════════════════════════════════════════════
# GLOBAL / MULTI-LANGUAGE CONSIDERATIONS
# ═══════════════════════════════════════════════════════════════════════

# 1. **Cultural Context:**
#    - Consider regional norms (but apply consistent rules)
#    - Traditional clothing ≠ sexual content
#    - Cultural symbols vs hate symbols (context matters)
#    - Religious imagery in appropriate context → safe

# 2. **Text in Images (Any Language):**
#    - Analyze visible text for threats, hate speech, illegal content
#    - Consider language barriers (symbols, gestures may transcend language)

# 3. **News / Journalism:**
#    - Professional photography from conflict zones → safe (unless extreme gore)
#    - News watermarks, press credentials → likely safe
#    - Documentary context → safe

# 4. **Law Enforcement Worldwide:**
#    - Police/military uniforms vary by country
#    - Look for: badges, official vehicles, handcuffs, evidence markers
#    - Crime resolved + authorities present → safe (unless other violations)

# ═══════════════════════════════════════════════════════════════════════
# CONTEXT ASSESSMENT
# ═══════════════════════════════════════════════════════════════════════

# Available contexts: news|medical|criminal|educational|social|artistic|gaming|law_enforcement|other

# - **news**: Professional journalism, news watermarks
# - **medical**: Healthcare setting, medical professionals
# - **criminal**: Crime scene WITHOUT law enforcement (active/promoting crime)
# - **law_enforcement**: Police/authorities present, crime resolved
# - **educational**: Textbooks, instructional, awareness
# - **social**: Personal/casual social media content
# - **artistic**: Museums, galleries, art exhibitions
# - **gaming**: Video game screenshots, esports
# - **other**: Unclear or mixed context

# ═══════════════════════════════════════════════════════════════════════
# OUTPUT FORMAT
# ═══════════════════════════════════════════════════════════════════════

# Use exact category values: safe, violence_threats, sexual_explicit, dangerous, criminal, gore, obscene, self_harm, hate_discrimination, illegal

# Return structured JSON with:
# - category: (exact enum value)
# - confidence: (0.0-1.0, calibrated per guidelines)
# - reasoning: (clear, concise explanation - max 2 sentences)
# - detected_elements: (objective list of visible objects)
# - red_flags: (concerning elements only if present)
# - context_assessment: (one of the defined contexts)
# - is_medical_professional_context: (boolean)

# ═══════════════════════════════════════════════════════════════════════
# CRITICAL EXAMPLES
# ═══════════════════════════════════════════════════════════════════════

# Example 1:
# Image: Person injecting drugs in messy room
# → Category: dangerous (conf: 0.92)
# → Reasoning: "Recreational drug injection in casual setting without medical context"

# Example 2:
# Image: Police officer arresting suspect with drugs on table
# → Category: safe (conf: 0.88)
# → Reasoning: "Law enforcement present, crime resolved, evidence documentation"

# Example 3:
# Image: Police at crime scene with dead body and blood
# → Category: gore (conf: 0.85)
# → Reasoning: "Despite law enforcement presence, image shows graphic blood and injuries"

# Example 4:
# Image: Gun pointed at camera (selfie style)
# → Category: violence_threats (conf: 0.90)
# → Reasoning: "Weapon pointed in threatening manner, intimidating pose"

# Example 5:
# Image: Soldier holding rifle in patrol
# → Category: safe (conf: 0.93)
# → Reasoning: "Military personnel in professional duty, proper uniform and context"

# Example 6:
# Image: Martial arts fight in ring with referee
# → Category: safe (conf: 0.95)
# → Reasoning: "Sanctioned sport competition with proper context"

# Example 7:
# Image: Counterfeit bills on table with police evidence marker
# → Category: safe (conf: 0.87)
# → Reasoning: "Law enforcement evidence documentation, crime already resolved"

# Example 8:
# Image: Person counting large stacks of cash in basement
# → Category: criminal (conf: 0.78)
# → Reasoning: "Suspicious cash handling in non-business setting suggests money laundering"

# Example 9:
# Image: Breaking into car with crowbar
# → Category: criminal (conf: 0.91)
# → Reasoning: "Active theft in progress, no law enforcement present"

# Example 10:
# Image: Historical war photo from museum
# → Category: safe (conf: 0.89)
# → Reasoning: "Historical documentary context, museum exhibition setting"

# ═══════════════════════════════════════════════════════════════════════

# Remember: When law enforcement is present and crime is resolved, classify as SAFE unless OTHER violations exist (gore, explicit content, etc.). Always consider cultural context for global platform."""


import json
from openai import OpenAI
from PIL import Image

import re
from src.schemas.models import (
    ModerationCategory,
    CATEGORY_DESCRIPTIONS,
    CATEGORY_DISPLAY_NAMES,
    ImageModerationOutput,
    ImageModerationResponse,
    ImageAnalysis
)
from src.utils.utils import image_to_base64

class ImageModerationService:
    """Service for moderating image content"""
    
    def __init__(self, ollama_client: OpenAI, vlm_model: str):
        """
        Initialize image moderation service.
        
        Args:
            ollama_client: OpenAI client configured for Ollama
            vlm_model: Name of the vision-language model to use
        """
        self.client = ollama_client
        self.vlm_model = vlm_model
        self.system_prompt = self._build_system_prompt()
        print(f"✅ ImageModerationService initialized: {vlm_model}")
    
    def moderate(self, image: Image.Image) -> ImageModerationResponse:
        """
        Moderate image content.
        
        Args:
            image: PIL Image to moderate
            
        Returns:
            ImageModerationResponse with category and detailed analysis
        """
        try:
            base64_image = image_to_base64(image)
            
            response = self.client.chat.completions.create(
                model=self.vlm_model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Analyze and classify this image:"},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                            }
                        ]
                    }
                ],
                temperature=0.1,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "image_moderation",
                        "strict": True,
                        "schema": ImageModerationOutput.model_json_schema()
                    }
                }
            )
            
            # Get response content
            response_content = response.choices[0].message.content
            
            # Try to parse JSON with error handling
            try:
                result_dict = json.loads(response_content)
            except json.JSONDecodeError as json_error:
                print(f"⚠️  JSON decode error: {json_error}")
                print(f"   Raw response: {response_content[:200]}...")
                
                # Try to fix common JSON issues
                result_dict = self._fix_and_parse_json(response_content)
                
                if not result_dict:
                    # If still can't parse, return safe with low confidence
                    return self._create_safe_fallback_response(
                        f"JSON parsing failed: {str(json_error)[:100]}"
                    )
            
            # Validate and parse output
            try:
                output = ImageModerationOutput(**result_dict)
            except Exception as validation_error:
                print(f"⚠️  Validation error: {validation_error}")
                return self._create_safe_fallback_response(
                    f"Response validation failed: {str(validation_error)[:100]}"
                )
            
            # Consistency check: red flags but classified as safe
            confidence = output.confidence
            if output.red_flags and output.category == ModerationCategory.SAFE:
                high_severity = any(
                    word in flag.lower()
                    for flag in output.red_flags
                    for word in ["violence", "weapon", "drug", "nude", "blood", 
                                "injury", "threat", "explicit", "gore"]
                )
                if high_severity:
                    confidence = min(confidence, 0.65)
            
            analysis = ImageAnalysis(
                detected_elements=output.detected_elements,
                red_flags=output.red_flags,
                context_assessment=output.context_assessment,
                is_medical_professional_context=output.is_medical_professional_context
            )
            
            return ImageModerationResponse(
                category=CATEGORY_DISPLAY_NAMES[output.category],
                category_code=output.category.value,
                confidence=confidence,
                reasoning=output.reasoning,
                analysis=analysis
            )
            
        except Exception as e:
            print(f"❌ Image moderation error: {e}")
            return self._create_safe_fallback_response(f"Error: {str(e)[:100]}")
    
    def _fix_and_parse_json(self, response_content: str) -> dict:
        """
        Attempt to fix common JSON issues and parse.
        
        Args:
            response_content: Raw JSON string from model
            
        Returns:
            Parsed dict or None if unable to fix
        """
        try:
            # Try to extract JSON from response (in case there's extra text)
            json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                
                # Fix common issues:
                # 1. Unescaped quotes in strings
                # This is tricky, but we can try to fix obvious cases
                
                # 2. Unescaped newlines
                json_str = json_str.replace('\n', '\\n')
                
                # 3. Unescaped backslashes
                json_str = json_str.replace('\\', '\\\\')
                
                # Try parsing again
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    pass
            
            # If still can't parse, try more aggressive cleaning
            # Remove any control characters
            cleaned = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', response_content)
            
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError:
                pass
            
        except Exception as e:
            print(f"   Failed to fix JSON: {e}")
        
        return None
    
    def _create_safe_fallback_response(self, error_message: str) -> ImageModerationResponse:
        """
        Create a safe fallback response when moderation fails.
        
        Args:
            error_message: Error description
            
        Returns:
            ImageModerationResponse with safe category and low confidence
        """
        return ImageModerationResponse(
            category=CATEGORY_DISPLAY_NAMES[ModerationCategory.SAFE],
            category_code=ModerationCategory.SAFE.value,
            confidence=0.0,
            reasoning=f"Moderation failed: {error_message}",
            analysis=ImageAnalysis(
                detected_elements=[],
                red_flags=["moderation_error"],
                context_assessment="error",
                is_medical_professional_context=False
            )
        )
    
    def _build_system_prompt(self) -> str:
        """Build system prompt for image moderation"""
        categories_list = "\n".join([
            f"- {cat.value}: {desc}"
            for cat, desc in CATEGORY_DESCRIPTIONS.items()
        ])
        
        return f"""You are an expert image content moderator for a global social media platform serving users worldwide in multiple languages.

CATEGORIES:
{categories_list}

═══════════════════════════════════════════════════════════════════════
CLASSIFICATION RULES
═══════════════════════════════════════════════════════════════════════

1. **dangerous** (Drugs & Substance Abuse):
   
   🚫 **ABSOLUTE RULES - NO GUESSING ALLOWED**:
   - NEVER flag "smoking device" without identifying the ACTUAL SUBSTANCE
   - "unclear substance" = NOT A VIOLATION → SAFE
   - "smoking device visible" alone = NOT ENOUGH → SAFE
   - Cigarettes/tobacco = LEGAL → SAFE
   - DO NOT use reasoning like "unclear substance", "suspicious", "could be", "might be"
   - If you CANNOT identify the specific illegal drug → DEFAULT TO SAFE
   - **Policy: Tobacco smoking is NOT a violation**
   
   ⚠️ **VERIFICATION REQUIRED - MUST SEE ILLEGAL DRUGS**:
   - Must have CLEAR, VISIBLE evidence of SPECIFIC illegal drug (cocaine, heroin, meth, crack)
   - Must IDENTIFY the actual illegal substance, not guess
   - Smoking alone ≠ drug use (could be tobacco, legal vaping)
   - Dark/moody photos, sad people, dim lighting ≠ drug use
   - Silhouettes, contemplative poses ≠ drug use
   - DO NOT flag based on atmosphere, assumptions, or "unclear" observations
   - ONLY flag when SPECIFIC ILLEGAL substances/paraphernalia are CLEARLY VISIBLE AND IDENTIFIABLE
   
   ✅ CLEAR VIOLATIONS (conf: 0.85-0.95) - Must identify specific illegal drug:
   - Active ILLEGAL drug use with substance identified: injection of heroin/cocaine/meth (visible), smoking crack cocaine (crack pipe + rock visible), snorting cocaine (white powder lines visible)
   - ILLEGAL drug paraphernalia with substance confirmed: crack pipes with residue, syringes with non-medical drugs visible, meth pipes with crystals
   - Drug glorification with illegal drugs shown: cocaine/heroin pills/powder CLEARLY DISPLAYED, illegal drug packaging visible with contents
   - Drug manufacturing setups: meth lab equipment with chemicals, marijuana grow operation (in prohibited jurisdiction) with plants visible
   - Drug dealing scenes with illegal drugs: baggies with white powder/pills confirmed as illegal drugs, scales with cocaine/meth visible
   
   ⚠️ CRITICAL DISTINCTION - Tobacco/Legal vs Illegal Drugs:
   - **SAFE - ALWAYS**: 
     * Regular cigarettes (with or without filter)
     * Cigars, cigarillos
     * Tobacco pipes
     * Vaping devices / e-cigarettes
     * Hookah / shisha
     * ANY smoking where substance is not identified as illegal drug
   - **VIOLATION - ONLY IF**: 
     * Substance is CLEARLY AND SPECIFICALLY identified as illegal drug (cocaine, heroin, crack, methamphetamine)
     * Must see the actual illegal substance OR unique illegal drug paraphernalia (crack pipe, meth pipe - not regular pipes)
   - **Visual cues for SAFE tobacco**: 
     * Standard cigarette shape with filter
     * Tobacco packaging visible
     * Normal smoking behavior
     * Pipe tobacco
     * Vape mod/pod devices
   - **Red flags for illegal drugs (MUST BE CLEARLY VISIBLE AND IDENTIFIED)**:
     * White powder lines on surface (cocaine snorting)
     * Glass pipe with white/crystal residue (meth pipe)
     * Burnt spoon with brown residue + needle (heroin injection)
     * Small glass tube with copper mesh (crack pipe) + rock visible
     * Tin foil with burn marks + white/brown powder visible (heroin/fentanyl smoking)
   
   ❌ NOT VIOLATIONS → ALWAYS SAFE:
   - "smoking device" without drug identification → SAFE
   - "unclear substance" → SAFE
   - "person smoking" → SAFE (assume tobacco unless proven otherwise)
   - Dark/moody photography without visible identified drugs
   - Sad, contemplative, or depressed person without any drug evidence
   - Silhouettes or dim lighting photos
   - **ALL tobacco products**: cigarettes, cigars, tobacco pipes, vaping devices, hookah
   - Medical context: healthcare setting, clinical equipment
   - Vaccination/insulin: proper medical device
   - Pharmacy: legitimate medications in proper packaging
   - Educational/documentary: textbooks, awareness campaigns
   - Law enforcement: police evidence photos with officers present
   
   🔍 KEY INDICATORS FOR VIOLATIONS (All must be present):
   - ✅ SPECIFIC illegal drug identified (not "unclear")
   - ✅ Substance CLEARLY VISIBLE in frame
   - ✅ NOT in medical/law enforcement/educational context
   - ✅ Recreational/casual setting confirmed
   
   🔍 DEFAULT TO SAFE WHEN:
   - ❌ Cannot identify specific substance
   - ❌ "unclear", "suspicious", "could be", "might be"
   - ❌ Just "smoking" or "smoking device" without drug ID
   - ❌ Any ambiguity about the substance
   
   **CRITICAL REMINDERS**: 
   - Tobacco smoking ≠ Drug abuse (NEVER flag tobacco)
   - Dark mood ≠ Drug use
   - Sad person ≠ Drug user
   - Smoking device ≠ Drug paraphernalia (unless specifically illegal device like crack/meth pipe)
   - **"unclear substance" = SAFE BY DEFAULT**
   - **When in doubt → SAFE (tobacco is legal)**
   - **NEVER use "unclear substance" as reasoning for dangerous flag**

2. **criminal** (Crime, Trafficking, Fraud, Illegal Activities):
   
   ✅ CLEAR VIOLATIONS (conf: 0.85-0.95):
   
   **Active Criminal Activity (in progress, no law enforcement):**
   - Weapon trafficking: unregistered firearms being sold/smuggled
   - Counterfeit production: making fake currency, forged documents, fake IDs
   - Theft in progress: breaking and entering, shoplifting, burglary
   - Money laundering: large suspicious cash transactions, illegal cash operations
   - Human trafficking indicators: exploitation scenes, forced labor
   - Black market transactions: illegal goods exchange
   - Vandalism/destruction of property in progress
   - Illegal weapon possession (showing intent to use/sell)
   
   **Promotion of Criminal Activity:**
   - Instructions for committing crimes
   - Glorification of criminal lifestyle
   - Recruitment for illegal activities
   
   ⚠️ MODERATE VIOLATIONS (conf: 0.60-0.75):
   - Ambiguous criminal activity (unclear if active or past)
   - Stolen goods without clear law enforcement context
   - Suspicious transactions (context unclear)
   
   ❌ NOT VIOLATIONS → safe:
   
   **Law Enforcement Present / Crime Already Resolved:**
   - Crime scene WITH police/officers present (investigation/arrest)
   - Suspects in handcuffs/custody
   - Police evidence documentation
   - Court proceedings, trial photography
   - Prison/jail settings (legal detention)
   - Drug/weapon seizures by authorities (confiscated items)
   - News photography of arrests, police operations
   
   **EXCEPTION**: Even with law enforcement present, if image shows OTHER violations:
   - Excessive gore (blood, severe injuries) → gore
   - Graphic violence → violence_threats or gore
   - Explicit content → sexual_explicit
   
   **Legal/Neutral Contexts:**
   - Legal firearms: gun stores, shooting ranges, licensed ownership
   - Currency in normal transactions: banks, ATMs, shopping
   - Antique/museum displays
   - Movie/TV production (clearly staged)
   - Historical documentation
   - Educational content about crime prevention
   
   🔍 DECISION TREE FOR CRIMINAL:
   
   Step 1: Is there criminal activity visible?
   - NO → safe
   - YES → Continue to Step 2
   
   Step 2: Is law enforcement present or is the crime already resolved?
   - YES (police visible, handcuffs, custody, evidence tags) → Check Step 3
   - NO (active crime, no police) → VIOLATION: criminal
   
   Step 3: Does the image contain OTHER violations despite law enforcement?
   - Gore (blood, severe injuries) → VIOLATION: gore
   - Extreme violence → VIOLATION: violence_threats or gore
   - Explicit content → VIOLATION: sexual_explicit
   - None of the above → safe (law enforcement context)
   
   🔍 KEY INDICATORS:
   - VIOLATION: Active crime in progress, no police, promotional intent
   - SAFE: Police/authorities present, crime resolved, legal context, educational/news

3. **violence_threats** (Violence, Threats, Weapons in Threatening Context):
   
   ✅ CLEAR VIOLATIONS (conf: 0.85-0.95):
   
   **Active Violence:**
   - Physical assault/fight in progress: punching, kicking, beating
   - Weapons being used against people: stabbing, shooting, attacking
   - Mob violence, riots with active aggression
   - Domestic violence scenes
   - Child abuse or violence against vulnerable people
   - Animal cruelty/abuse
   
   **Threatening Behavior:**
   - Weapons pointed at people (guns, knives, weapons aimed)
   - Threatening poses: person holding weapon in intimidating manner
   - Hostage situations
   - Menacing gestures with weapons
   - Self-defense situations where violence is imminent
   
   **Weapons in Threatening Context:**
   - Weapons displayed with threatening intent
   - Weapons in crime scenes (without law enforcement)
   - Illegal weapon possession with threatening behavior
   
   ⚠️ MODERATE VIOLATIONS (conf: 0.60-0.75):
   - Aftermath of violence (no active violence but recent)
   - Weapons in ambiguous context (unclear if threatening)
   - Verbal threats visible (threatening text/gestures)
   
   ❌ NOT VIOLATIONS → safe:
   
   **Law Enforcement / Security Context:**
   - Police/military in professional duty
   - Security personnel with weapons (guarding, patrolling)
   - Police arrests (controlled situation)
   - Training exercises clearly marked
   
   **Sports / Competition:**
   - Martial arts, boxing, MMA (sanctioned sports)
   - Fencing, kendo (sport context)
   - Airsoft, paintball games
   - Wrestling, competitive fighting sports
   
   **Legal / Neutral Weapons:**
   - Gun stores, weapon shops
   - Shooting ranges (sport shooting)
   - Hunting in legal context
   - Museum displays, historical exhibits
   - Antique/collectible weapons on display
   - Kitchen knives in cooking context
   - Tools used appropriately (construction, gardening)
   
   **News / Documentary:**
   - Professional war/conflict photography (journalistic)
   - News coverage of violence (informational)
   - Documentary about conflicts (educational)
   - Historical war photos
   
   **Entertainment:**
   - Movie/TV scenes (clearly staged)
   - Video game screenshots
   - Theatrical performances
   - Cosplay with prop weapons
   
   🔍 DECISION TREE FOR VIOLENCE_THREATS:
   
   Step 1: Is there active violence or threatening behavior?
   - NO → Check context in Step 2
   - YES → Continue to Step 3
   
   Step 2: Are weapons present?
   - NO → safe
   - YES → What's the context?
     * Sports/competition → safe
     * Museum/display → safe
     * Legal ownership/store → safe
     * Unclear/threatening → VIOLATION: violence_threats
   
   Step 3: Active violence/threats - what's the context?
   - Law enforcement duty → safe
   - Sports/sanctioned competition → safe
   - News/documentary (professional) → safe
   - Real violence/threats → VIOLATION: violence_threats
   
   🔍 KEY INDICATORS:
   - VIOLATION: Active aggression, weapons aimed at people, threatening intent, real violence
   - SAFE: Professional context (police/military), sports, legal ownership, news/documentary, entertainment

4. **sexual_explicit**:
   
   ✅ VIOLATIONS (conf: 0.90-0.98):
   - Nudity: exposed genitals, breasts without coverage
   - Sexual acts or positions
   - Pornographic content
   - Sexual solicitation imagery
   
   ⚠️ MODERATE (conf: 0.65-0.80):
   - Suggestive poses (clothed but highly sexual)
   - Partial nudity with sexual context
   
   ❌ NOT VIOLATIONS → safe:
   - Artistic nude (museum/gallery, art context)
   - Medical anatomy (textbooks, education)
   - Breastfeeding (natural, maternal)
   - Swimwear at beach/pool
   - Traditional cultural attire
   
   🔍 KEY: Sexual organs visible + sexual context = violation

5. **gore**:
   
   ✅ VIOLATIONS (conf: 0.85-0.95):
   - Real blood, open wounds, severe injuries
   - Accident aftermath with visible trauma
   - Dead bodies with visible injuries
   - Surgical procedures (non-medical context)
   - Extreme body trauma
   
   ⚠️ MODERATE (conf: 0.60-0.75):
   - Minor injuries with blood
   - Medical procedures in ambiguous context
   
   ❌ NOT VIOLATIONS → safe:
   - Red colored diagrams, charts, UI
   - Fake blood (theatrical makeup, clearly staged)
   - Medical textbooks (educational)
   - Cartoon/animated violence
   - Red paint, food, liquids
   
   🔍 KEY: Real blood/injury vs simulated/diagram

6. **obscene**, **self_harm**, **hate_discrimination**, **illegal**:
   (Less common in images, but check for visible text, symbols, gestures)

═══════════════════════════════════════════════════════════════════════
CONFIDENCE CALIBRATION
═══════════════════════════════════════════════════════════════════════

Assign confidence based on violation severity and clarity:

**HIGH CONFIDENCE (0.90-0.98):**
- Crystal clear violation, zero ambiguity
- Extreme severity (graphic content)
- Multiple violation indicators present

**CONFIDENT (0.80-0.89):**
- Clear violation with strong evidence
- High severity
- Context supports violation classification

**MODERATELY CONFIDENT (0.65-0.79):**
- Violation visible but some context needed
- Moderate severity
- Some ambiguity but leans toward violation

**BORDERLINE (0.50-0.64):**
- Ambiguous case, could go either way
- Low to moderate severity
- Significant context interpretation required

**LOW CONFIDENCE (0.30-0.49):**
- Likely safe but some concerning elements
- Very low severity
- High ambiguity

**SAFE (0.85-0.98):**
- Clearly safe content
- No violations detected
- Strong evidence of legitimate context

═══════════════════════════════════════════════════════════════════════
GLOBAL / MULTI-LANGUAGE CONSIDERATIONS
═══════════════════════════════════════════════════════════════════════

1. **Cultural Context:**
   - Consider regional norms (but apply consistent rules)
   - Traditional clothing ≠ sexual content
   - Cultural symbols vs hate symbols (context matters)
   - Religious imagery in appropriate context → safe

2. **Text in Images (Any Language):**
   - Analyze visible text for threats, hate speech, illegal content
   - Consider language barriers (symbols, gestures may transcend language)

3. **News / Journalism:**
   - Professional photography from conflict zones → safe (unless extreme gore)
   - News watermarks, press credentials → likely safe
   - Documentary context → safe

4. **Law Enforcement Worldwide:**
   - Police/military uniforms vary by country
   - Look for: badges, official vehicles, handcuffs, evidence markers
   - Crime resolved + authorities present → safe (unless other violations)

═══════════════════════════════════════════════════════════════════════
CONTEXT ASSESSMENT
═══════════════════════════════════════════════════════════════════════

Available contexts: news|medical|criminal|educational|social|artistic|gaming|law_enforcement|other

- **news**: Professional journalism, news watermarks
- **medical**: Healthcare setting, medical professionals
- **criminal**: Crime scene WITHOUT law enforcement (active/promoting crime)
- **law_enforcement**: Police/authorities present, crime resolved
- **educational**: Textbooks, instructional, awareness
- **social**: Personal/casual social media content
- **artistic**: Museums, galleries, art exhibitions
- **gaming**: Video game screenshots, esports
- **other**: Unclear or mixed context

═══════════════════════════════════════════════════════════════════════
OUTPUT FORMAT - CRITICAL JSON RULES
═══════════════════════════════════════════════════════════════════════

**IMPORTANT**: Return ONLY valid JSON. Follow these rules strictly:

1. **String Fields (reasoning, detected_elements, red_flags):**
   - Do NOT use quotes inside strings
   - Use apostrophes instead: "person's hand" NOT "person\"s hand"
   - Keep text simple and descriptive
   - Avoid special characters

2. **Reasoning Field:**
   - Keep it SHORT (max 100 characters)
   - Use simple language
   - No quotes, no newlines, no special characters
   - Example: "Drug paraphernalia visible in casual setting"

3. **Arrays:**
   - Use simple, short strings
   - Example: ["needle", "person", "indoor"] NOT ["person's needle", "dark \"room\""]

Use exact category values: safe, violence_threats, sexual_explicit, dangerous, criminal, gore, obscene, self_harm, hate_discrimination, illegal

Return structured JSON with:
- category: (exact enum value)
- confidence: (0.0-1.0, calibrated per guidelines)
- reasoning: (SHORT, simple, no quotes - max 100 chars)
- detected_elements: (simple strings, no quotes)
- red_flags: (simple strings, no quotes, empty if none)
- context_assessment: (one of the defined contexts)
- is_medical_professional_context: (boolean)

═══════════════════════════════════════════════════════════════════════
EXAMPLES WITH CORRECT JSON FORMAT
═══════════════════════════════════════════════════════════════════════

Example 1:
{{
  "category": "dangerous",
  "confidence": 0.92,
  "reasoning": "Drug injection in casual setting",
  "detected_elements": ["syringe", "person", "arm"],
  "red_flags": ["drug use", "needle visible"],
  "context_assessment": "criminal",
  "is_medical_professional_context": false
}}

Example 2:
{{
  "category": "safe",
  "confidence": 0.88,
  "reasoning": "Police evidence documentation",
  "detected_elements": ["police", "drugs", "evidence bag"],
  "red_flags": [],
  "context_assessment": "law_enforcement",
  "is_medical_professional_context": false
}}

Example 3:
{{
  "category": "violence_threats",
  "confidence": 0.90,
  "reasoning": "Weapon pointed at person",
  "detected_elements": ["gun", "person", "threatening pose"],
  "red_flags": ["weapon aimed", "threatening behavior"],
  "context_assessment": "criminal",
  "is_medical_professional_context": false
}}

═══════════════════════════════════════════════════════════════════════

Remember: Keep reasoning SHORT and simple. No quotes in strings. No special characters."""