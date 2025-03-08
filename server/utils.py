import trafilatura
from typing import Dict, Optional
import logging
import json
import os
import re
import google.generativeai as genai
from datetime import datetime
import json_repair 
logger = logging.getLogger(__name__)

def extract_article_content(url: str, content: str) -> Optional[Dict]:
    """Extract and clean article content with metadata using trafilatura."""
    try:
        # Direct content handling
        if content and (clean_content := content.strip()):
            logger.debug("Using provided content directly")
            return {
                "text": clean_content,
                "source": "direct_input",
                "length": len(clean_content)
            }

        # URL-based extraction
        logger.debug(f"Attempting URL extraction: {url}")
        if downloaded := trafilatura.fetch_url(url):
            extracted = trafilatura.extract(
                downloaded,
                include_formatting=True,
                include_links=True,
                include_images=True,
                include_tables=True,
                output_format='json'
            )
            
            if extracted:
                data = json.loads(extracted)
                logger.debug(f"Successful extraction - Length: {len(data.get('text', ''))}")
                return {
                    "text": data.get('text', ''),
                    "title": data.get('title', ''),
                    "author": data.get('author', ''),
                    "date": data.get('date', ''),
                    "source": url,
                    "length": len(data.get('text', ''))
                }
        
        logger.error(f"Extraction failed for URL: {url}")
        return None

    except Exception as e:
        logger.error(f"Extraction error: {str(e)}", exc_info=True)
        return None

def analyze_with_gemini(content: str) -> Optional[Dict]:
    """Analyze content for propaganda using Google Gemini Pro API."""
    if not (api_key := os.environ.get("GEMINI_API_KEY")):
        logger.warning("Missing Gemini API key - skipping analysis")
        return None

    try:
        genai.configure(api_key=api_key)
        
        # List models to verify availability (uncomment to check)
        # list_available_models()
        
        # Use the correct model name from your available models
        model = genai.GenerativeModel('gemini-2.0-flash')  # UPDATED MODEL NAME
        
        prompt = """
        Analyze the text for propaganda and bias. For each point, provide specific examples.

        Text: {content}

        Return JSON with:
        - propaganda_likelihood (0-100)
        - detected_techniques (name, example, explanation)
        - overall_analysis
        - suggested_corrections

        Focus on:
        1. Emotional manipulation
        2. Logical fallacies
        3. Misleading statements
        4. Loaded language
        5. False equivalencies
        6. Oversimplification
        7. Fear/anger appeal
        8. Unsupported claims

        PROVIDE ONLY VALID JSON RESPONSE (including valid json formatting tags for special characters.
        """.replace("{content}", content)

        response = model.generate_content(prompt)
        
        if response and response.candidates:
            content = response.candidates[0].content.parts[0].text
            #return json.loads(content[content.find('\n')+1:content.rfind('\n')])
            return json_repair.loads(content)
        else:
            logger.error("Empty or invalid response from Gemini API")
            return None

    except Exception as e:
        logger.error(f"Gemini analysis failed: {str(e)}", exc_info=True)
        return None

"""Analyze content for propaganda using Google Gemini Pro API.
def analyze_with_gemini(content: str) -> Optional[Dict]:
    if not (api_key := os.environ.get("GEMINI_API_KEY")):
        logger.warning("Missing Gemini API key - skipping analysis")
        return None

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        
        prompt = """
"""
        Analyze the text for propaganda and bias. For each point, provide specific examples.

        Text: {content}

        Return JSON with:
        - propaganda_likelihood (0-100)
        - detected_techniques (name, example, explanation)
        - overall_analysis
        - suggested_corrections

        Focus on:
        1. Emotional manipulation
        2. Logical fallacies
        3. Misleading statements
        4. Loaded language
        5. False equivalencies
        6. Oversimplification
        7. Fear/anger appeal
        8. Unsupported claims

        ONLY VALID JSON RESPONSE.
""" """.replace("{content}", content)

        response = model.generate_content(prompt).text
        return json.loads(response) if response else None

    except Exception as e:
        logger.error(f"Gemini analysis failed in analyze_with_gemini : {str(e)}", exc_info=True)
        return None
"""
def analyze_propaganda(content: Dict) -> Dict:
    """Perform propaganda analysis using pattern matching and AI insights."""
    PROPAGANDA_PATTERNS = {
        'emotional_language': r'\b(shocking|outrageous|terrible|amazing)\b',
        'absolutist_terms': r'\b(always|never|everyone|nobody)\b',
        'unverified_claims': r'\b(sources say|reportedly|allegedly)\b',
        'loaded_words': r'\b(regime|puppet|radical|extremist)\b',
        'fear_mongering': r'\b(crisis|catastrophe|disaster)\b',
        'oversimplification': r'\b(simply|obviously|clearly)\b',
        'ad_hominem': r'\b(stupid|ignorant|foolish)\b',
        'bandwagon': r'\b(everyone knows|popular opinion)\b',
        'false_dichotomy': r'\b(either|or|versus|vs\.)\b',
        'conspiracy_terms': r'\b(conspiracy|cover-up)\b'
    }

    text = content['text']
    analysis = {
        "metadata": {
            "title": content.get('title', ''),
            "author": content.get('author', ''),
            "date": content.get('date', ''),
            "source": content.get('source', ''),
            "word_count": len(text.split())
        },
        "propaganda_score": 0,
        "detailed_matches": {},
        "detected_techniques": [],
        "analysis": "",
        "correction": None
    }

    # Pattern-based analysis
    total_matches = 0
    for pattern_name, regex in PROPAGANDA_PATTERNS.items():
        matches = list(re.finditer(regex, text.lower()))
        total_matches += len(matches)
        
        if matches:
            analysis['detailed_matches'][pattern_name] = [
                {
                    "match": m.group(),
                    "context": f"...{text[max(0, m.start()-50):m.end()+50]}...",
                    "position": m.start()
                } for m in matches
            ]

    # Score calculation
    word_count = analysis['metadata']['word_count']
    pattern_score = min(int((total_matches / word_count) * 2000), 100) if word_count else 0

    # AI analysis integration
    ai_result = analyze_with_gemini(text)
    ai_score = ai_result.get('propaganda_likelihood', 0) if ai_result else 0
    final_score = int(pattern_score * 0.4 + ai_score * 0.6) if ai_result else pattern_score

    # Generate response
    analysis.update({
        "propaganda_score": final_score,
        "detected_techniques": list(analysis['detailed_matches'].keys()) + 
                             (ai_result.get('detected_techniques', []) if ai_result else []),
        "analysis": get_analysis_summary(final_score, total_matches, len(analysis['detailed_matches'])),
        "correction": ai_result.get('suggested_corrections', "No suggestions available") if ai_result else None
    })

    return analysis

def get_analysis_summary(score: int, total_matches: int, technique_count: int) -> str:
    """Generate analysis summary based on propaganda score."""
    if score < 30:
        return "Factual and well-balanced content with minimal bias indicators."
    elif score < 70:
        return f"Moderate bias potential ({technique_count} techniques, {total_matches} matches)."
    else:
        return f"High propaganda likelihood ({technique_count} techniques, {total_matches} matches)."
