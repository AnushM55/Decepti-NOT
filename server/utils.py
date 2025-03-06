import trafilatura
from typing import Dict, Optional
import logging
import json
import os
import google.generativeai as genai
from datetime import datetime

logger = logging.getLogger(__name__)

def extract_article_content(url: str, content: str) -> Optional[Dict]:
    """
    Extract clean article content using trafilatura with enhanced metadata
    """
    try:
        # First try using the provided content directly
        logger.debug("Attempting to extract content directly from provided text")
        if content and len(content.strip()) > 0:  # Basic check for non-empty content
            logger.debug("Using provided content directly")
            return {
                "text": content.strip(),
                "source": "direct_input",
                "length": len(content.strip())
            }

        # If no direct content, try URL-based extraction
        logger.debug(f"No direct content, attempting to extract from URL: {url}")
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            extracted = trafilatura.extract(downloaded, include_formatting=True, include_links=True, 
                                         include_images=True, include_tables=True, 
                                         output_format='json')
            if extracted:
                extracted_dict = json.loads(extracted)
                logger.debug("Successfully extracted content from URL")
                logger.debug(f"Extracted content length: {len(extracted_dict.get('text', ''))}")
                return {
                    "text": extracted_dict.get('text', ''),
                    "title": extracted_dict.get('title', ''),
                    "author": extracted_dict.get('author', ''),
                    "date": extracted_dict.get('date', ''),
                    "source": url,
                    "length": len(extracted_dict.get('text', ''))
                }
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

def analyze_propaganda(content: Dict) -> Dict:
    """
    Enhanced propaganda analysis with detailed pattern locations and context
    """
    import re

    # Expanded propaganda indicators with more sophisticated patterns remain unchanged
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

    text_content = content['text']

    # Store detailed matches with context
    detailed_matches = {}
    total_indicators = 0

    logger.debug("Starting detailed propaganda analysis")
    logger.debug(f"Content length for analysis: {len(text_content)}")

    # Pattern-based analysis with context
    for indicator_type, pattern in propaganda_indicators.items():
        matches = list(re.finditer(pattern, text_content.lower()))
        total_indicators += len(matches)

        if matches:
            detailed_matches[indicator_type] = []
            for match in matches:
                # Get surrounding context (50 characters before and after)
                start = max(0, match.start() - 50)
                end = min(len(text_content), match.end() + 50)
                context = text_content[start:end]

                detailed_matches[indicator_type].append({
                    "matched_text": match.group(),
                    "context": f"...{context}...",
                    "position": match.start()
                })

        logger.debug(f"Indicator {indicator_type}: {len(matches)} matches")

    # Calculate base propaganda score
    words = len(text_content.split())
    indicator_density = (total_indicators / words) * 100 if words > 0 else 0
    pattern_score = min(int(indicator_density * 20), 100)  # Scale and cap at 100

    # Get AI analysis if available
    ai_analysis = analyze_with_gemini(text_content)
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
    detected_indicators = list(detailed_matches.keys())
    if additional_analysis:
        detected_indicators.extend(additional_analysis)

    # Create detailed response
    response = {
        "metadata": {
            "title": content.get('title', ''),
            "author": content.get('author', ''),
            "date": content.get('date', ''),
            "source": content.get('source', ''),
            "word_count": words
        },
        "propaganda_score": final_score,
        "detailed_matches": detailed_matches,
        "detected_techniques": detected_indicators,
        "analysis": "",
        "correction": None
    }

    # Add appropriate analysis and correction based on score
    if final_score < 30:
        response["analysis"] = "This article appears to be factual and well-balanced. The reporting is objective and supported by verifiable sources."
        response["correction"] = ai_correction if ai_correction else None
    elif final_score < 70:
        response["analysis"] = f"This article shows some signs of potential bias. Found {len(detected_indicators)} different types of propaganda techniques."
        response["correction"] = ai_correction if ai_correction else "Consider consulting multiple sources for a more balanced perspective on this topic."
    else:
        response["analysis"] = f"High likelihood of biased content. Found {len(detected_indicators)} different propaganda techniques with {total_indicators} total instances."
        response["correction"] = ai_correction if ai_correction else "For accurate information on this topic, please consult established fact-checking websites and verified news sources."

    return response