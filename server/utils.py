import trafilatura
from typing import Dict, Optional
import logging
import json
import os
import google.generativeai as genai
from datetime import datetime

logger = logging.getLogger(__name__)

def extract_article_content(url: str, content: str) -> Optional[str]:
    """
    Extract clean article content using trafilatura
    """
    try:
        # First try using the provided content directly
        logger.debug("Attempting to extract content directly from provided text")
        if content and len(content.strip()) > 0:  # Basic check for non-empty content
            logger.debug("Using provided content directly")
            return content.strip()

        # If no direct content, try URL-based extraction
        logger.debug(f"No direct content, attempting to extract from URL: {url}")
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            extracted = trafilatura.extract(downloaded)
            if extracted:
                logger.debug("Successfully extracted content from URL")
                logger.debug(f"Extracted content length: {len(extracted)}")
                return extracted
            else:
                logger.error("Failed to extract content from downloaded HTML")
        else:
            logger.error(f"Failed to download content from URL: {url}")

        return None
    except Exception as e:
        logger.error(f"Error extracting content: {str(e)}", exc_info=True)
        return None

def analyze_with_gemini(content: str) -> Dict:
    """
    Analyze content using Google's Gemini Pro API for sophisticated propaganda detection
    """
    try:
        GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
        if not GEMINI_API_KEY:
            logger.warning("Gemini API key not found, skipping AI analysis")
            return None

        # Configure the Gemini API
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-pro')

        # Prompt for propaganda analysis
        prompt = f"""Analyze the following text for propaganda techniques and biases. 
        Consider factors like emotional manipulation, logical fallacies, and misleading statements.
        Text: {content}

        Provide a response in the following JSON format:
        {{
            "propaganda_likelihood": <number between 0-100>,
            "detected_techniques": [<list of identified propaganda techniques>],
            "overall_analysis": "<detailed analysis>",
            "suggested_corrections": "<suggestions for more balanced reporting>"
        }}

        Ensure the response is valid JSON."""

        # Generate response
        response = model.generate_content(prompt)

        # Parse the response
        if response.text:
            try:
                return json.loads(response.text)
            except json.JSONDecodeError:
                logger.error("Failed to parse Gemini response as JSON")
                return None
        else:
            logger.error("Empty response from Gemini API")
            return None

    except Exception as e:
        logger.error(f"Error in Gemini analysis: {str(e)}", exc_info=True)
        return None

def analyze_propaganda(content: str) -> Dict:
    """
    Enhanced propaganda analysis combining pattern matching and AI analysis
    """
    import re

    # Expanded propaganda indicators with more sophisticated patterns
    propaganda_indicators = {
        'emotional_language': r'\b(shocking|outrageous|terrible|amazing|incredible|horrific|devastating|mind-blowing)\b',
        'absolutist_terms': r'\b(always|never|everyone|nobody|all|none|every single|absolutely)\b',
        'unverified_claims': r'\b(sources say|reportedly|allegedly|claims|according to some|many believe|experts suggest)\b',
        'loaded_words': r'\b(regime|puppet|radical|extremist|terrorist|freedom fighter|patriot|traitor)\b',
        'fear_mongering': r'\b(crisis|catastrophe|disaster|threat|danger|emergency|chaos|collapse)\b',
        'oversimplification': r'\b(simply|obviously|clearly|undoubtedly|without question|naturally)\b',
        'ad_hominem': r'\b(stupid|ignorant|foolish|incompetent|corrupt|evil|wicked)\b',
        'bandwagon': r'\b(everyone knows|popular opinion|majority believes|trending|viral|mainstream)\b',
        'false_dichotomy': r'\b(either|or|versus|vs\.|against|choose between)\b',
        'conspiracy_terms': r'\b(conspiracy|cover-up|secret agenda|hidden truth|real story|what they don\'t want you to know)\b'
    }

    # Count matches for each indicator
    matches = {}
    total_indicators = 0
    logger.debug("Starting propaganda analysis")
    logger.debug(f"Content length for analysis: {len(content)}")

    # Pattern-based analysis
    for indicator_type, pattern in propaganda_indicators.items():
        matches[indicator_type] = len(re.findall(pattern, content.lower()))
        total_indicators += matches[indicator_type]
        logger.debug(f"Indicator {indicator_type}: {matches[indicator_type]} matches")

    # Calculate base propaganda score
    words = len(content.split())
    indicator_density = (total_indicators / words) * 100 if words > 0 else 0
    pattern_score = min(int(indicator_density * 20), 100)  # Scale and cap at 100

    # Get AI analysis if available
    ai_analysis = analyze_with_gemini(content)
    final_score = pattern_score

    if ai_analysis:
        try:
            # Combine both scores with AI analysis weighted more heavily
            final_score = int((pattern_score * 0.4) + (ai_analysis.get('propaganda_likelihood', pattern_score) * 0.6))
            additional_analysis = ai_analysis.get('detected_techniques', [])
            ai_correction = ai_analysis.get('suggested_corrections', None)
        except (AttributeError, TypeError):
            logger.error("Failed to process AI analysis result")
            additional_analysis = []
            ai_correction = None
    else:
        additional_analysis = []
        ai_correction = None

    logger.debug(f"Words: {words}, Total indicators: {total_indicators}")
    logger.debug(f"Final propaganda score: {final_score}")

    # Generate comprehensive analysis
    detected_indicators = [k for k, v in matches.items() if v > 0]
    if additional_analysis:
        detected_indicators.extend(additional_analysis)

    if final_score < 30:
        analysis = "This article appears to be factual and well-balanced. The reporting is objective and supported by verifiable sources."
        correction = ai_correction if ai_correction else None
    elif final_score < 70:
        analysis = f"This article shows some signs of potential bias. Found indicators: {', '.join(detected_indicators)}."
        correction = ai_correction if ai_correction else "Consider consulting multiple sources for a more balanced perspective on this topic."
    else:
        analysis = f"High likelihood of biased content. Multiple propaganda indicators detected: {', '.join(detected_indicators)}."
        correction = ai_correction if ai_correction else "For accurate information on this topic, please consult established fact-checking websites and verified news sources."

    return {
        "propaganda_score": final_score,
        "analysis": analysis,
        "correction": correction,
        "detected_techniques": detected_indicators
    }