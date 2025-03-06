from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import os
from server.utils import extract_article_content, analyze_propaganda

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for Chrome extension

@app.route('/')
def health_check():
    return jsonify({"status": "healthy", "message": "Server is running"}), 200

@app.route('/analyze', methods=['POST'])
def analyze_article():
    try:
        logger.debug("Received analyze request")
        data = request.get_json()
        logger.debug(f"Request data: {data}")

        if not data or 'url' not in data or 'content' not in data:
            logger.error("Missing required fields in request")
            return jsonify({
                'error': 'Missing required fields'
            }), 400

        url = data['url']
        content = data['content']
        logger.debug(f"Processing URL: {url}")

        # Extract clean content from the article
        article_content = extract_article_content(url, content)

        if not article_content:
            logger.error("Failed to extract article content")
            return jsonify({
                'error': 'Failed to extract article content'
            }), 400

        logger.debug("Content extracted successfully, performing analysis")
        # Analyze the content for propaganda
        analysis_result = analyze_propaganda(article_content)
        logger.debug(f"Analysis completed: {analysis_result}")

        return jsonify(analysis_result)

    except Exception as e:
        logger.error(f"Error analyzing article: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Internal server error'
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)