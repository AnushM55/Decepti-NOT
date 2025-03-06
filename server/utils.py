import trafilatura
from typing import Dict, Optional
import logging

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

def analyze_propaganda(content: str) -> Dict:
    """
    Mock AI analysis function that looks for common propaganda indicators
    This implementation provides consistent responses based on content analysis
    """
    import re

    # Simple heuristics for propaganda detection
    propaganda_indicators = {
        'emotional_language': r'\b(shocking|outrageous|terrible|amazing|incredible)\b',
        'absolutist_terms': r'\b(always|never|everyone|nobody)\b',
        'unverified_claims': r'\b(sources say|reportedly|allegedly|claims)\b',
        'loaded_words': r'\b(regime|puppet|radical|extremist)\b'
    }

    # Count matches for each indicator
    matches = {}
    total_indicators = 0
    logger.debug("Starting propaganda analysis")
    logger.debug(f"Content length for analysis: {len(content)}")

    for indicator_type, pattern in propaganda_indicators.items():
        matches[indicator_type] = len(re.findall(pattern, content.lower()))
        total_indicators += matches[indicator_type]
        logger.debug(f"Indicator {indicator_type}: {matches[indicator_type]} matches")

    # Calculate propaganda score (0-100)
    words = len(content.split())
    indicator_density = (total_indicators / words) * 100 if words > 0 else 0
    propaganda_score = min(int(indicator_density * 20), 100)  # Scale and cap at 100

    logger.debug(f"Words: {words}, Total indicators: {total_indicators}")
    logger.debug(f"Final propaganda score: {propaganda_score}")

    # Generate analysis based on score
    if propaganda_score < 30:
        analysis = "This article appears to be factual and well-balanced. The reporting is objective and supported by verifiable sources."
        correction = None
    elif propaganda_score < 70:
        analysis = f"This article shows some signs of potential bias. Found indicators: {', '.join(k for k,v in matches.items() if v > 0)}."
        correction = "Consider consulting multiple sources for a more balanced perspective on this topic."
    else:
        analysis = f"High likelihood of biased content. Multiple propaganda indicators detected: {', '.join(k for k,v in matches.items() if v > 0)}."
        correction = "For accurate information on this topic, please consult established fact-checking websites and verified news sources."

    return {
        "propaganda_score": propaganda_score,
        "analysis": analysis,
        "correction": correction
    }