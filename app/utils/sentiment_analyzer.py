"""
Sentiment Analysis Utilities
Handles Google Cloud Natural Language API integration for sentiment analysis.
"""

import requests
import json
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def analyze_sentiment_with_google(text: str, api_key: str) -> Dict[str, Any]:
    """
    Analyze sentiment using Google Cloud Natural Language API.
    
    Args:
        text (str): Text content to analyze
        api_key (str): Google Cloud API key
        
    Returns:
        Dict[str, Any]: Sentiment analysis results or error information
    """
    try:
        url = f"https://language.googleapis.com/v1/documents:analyzeSentiment?key={api_key}"
        
        # Preprocess text
        text = _preprocess_text_for_api(text)
        
        payload = {
            "document": {
                "type": "PLAIN_TEXT",
                "content": text
            },
            "encodingType": "UTF8"
        }
        
        headers = {"Content-Type": "application/json"}
        
        logger.info(f"Sending sentiment analysis request for {len(text)} characters")
        
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            return _process_sentiment_response(result, text)
        else:
            error_msg = f"Google API Error: {response.status_code}"
            logger.error(error_msg)
            return {'error': error_msg}
            
    except Exception as e:
        error_msg = f"Sentiment analysis failed: {str(e)}"
        logger.error(error_msg)
        return {'error': error_msg}

def _preprocess_text_for_api(text: str) -> str:
    """
    Preprocess text for Google Cloud API.
    
    Args:
        text (str): Raw text content
        
    Returns:
        str: Preprocessed text
    """
    # Clean and limit text length
    text = text.strip()
    if len(text) > 1000:
        text = text[:1000]
    
    # Remove problematic characters (keep ASCII only)
    text = ''.join(char for char in text if ord(char) < 128)
    
    return text

def _process_sentiment_response(api_response: Dict[str, Any], original_text: str) -> Dict[str, Any]:
    """
    Process Google Cloud API response and calculate sentiment percentages.
    
    Args:
        api_response (Dict[str, Any]): Raw API response
        original_text (str): Original text that was analyzed
        
    Returns:
        Dict[str, Any]: Processed sentiment results
    """
    try:
        # Get document-level sentiment
        document_sentiment = api_response.get('documentSentiment', {})
        doc_score = float(document_sentiment.get('score', 0))
        doc_magnitude = float(document_sentiment.get('magnitude', 0))
        
        logger.info(f"Document sentiment - Score: {doc_score}, Magnitude: {doc_magnitude}")
        
        # If document score is near zero, calculate from individual sentences
        if abs(doc_score) < 0.01 and 'sentences' in api_response:
            doc_score = _calculate_score_from_sentences(api_response['sentences'])
            logger.info(f"Calculated score from sentences: {doc_score}")
        
        # Calculate sentiment classification and percentages
        sentiment_data = _calculate_sentiment_percentages(doc_score)
        
        # Add technical details
        sentiment_data.update({
            'confidence_score': round(abs(doc_score), 3),
            'magnitude': round(doc_magnitude, 3),
            'google_raw_score': doc_score,
            'text_length': len(original_text)
        })
        
        logger.info(f"Final sentiment: {sentiment_data['overall_sentiment']} "
                   f"(Pos: {sentiment_data['positive_percentage']}%, "
                   f"Neg: {sentiment_data['negative_percentage']}%)")
        
        return sentiment_data
        
    except Exception as e:
        logger.error(f"Error processing sentiment response: {str(e)}")
        return {'error': f'Failed to process sentiment data: {str(e)}'}

def _calculate_score_from_sentences(sentences: list) -> float:
    """
    Calculate average sentiment score from individual sentences.
    
    Args:
        sentences (list): List of sentence sentiment data
        
    Returns:
        float: Average sentiment score
    """
    sentence_scores = []
    
    for sentence in sentences:
        sent_sentiment = sentence.get('sentiment', {})
        sent_score = sent_sentiment.get('score', 0)
        if sent_score != 0:
            sentence_scores.append(float(sent_score))
    
    if sentence_scores:
        avg_score = sum(sentence_scores) / len(sentence_scores)
        logger.debug(f"Calculated average from {len(sentence_scores)} sentences: {avg_score}")
        return avg_score
    
    return 0.0

def _calculate_sentiment_percentages(score: float) -> Dict[str, Any]:
    """
    Calculate sentiment classification and percentages based on score.
    
    Args:
        score (float): Sentiment score (-1.0 to 1.0)
        
    Returns:
        Dict[str, Any]: Sentiment classification and percentages
    """
    # Determine overall sentiment with sensitive thresholds
    if score > 0.02:
        overall_sentiment = "Positive"
        positive_percentage = 60 + (score * 200)
        negative_percentage = 40 - (score * 200)
    elif score < -0.02:
        overall_sentiment = "Negative"
        positive_percentage = 40 + (score * 200)  # score is negative
        negative_percentage = 60 - (score * 200)  # score is negative
    else:
        overall_sentiment = "Neutral"
        positive_percentage = 50 + (score * 100)
        negative_percentage = 50 - (score * 100)
    
    # Ensure percentages are within reasonable bounds
    positive_percentage = max(5, min(95, positive_percentage))
    negative_percentage = max(5, min(95, negative_percentage))
    neutral_percentage = max(0, 100 - positive_percentage - negative_percentage)
    
    return {
        'overall_sentiment': overall_sentiment,
        'positive_percentage': round(positive_percentage, 1),
        'negative_percentage': round(negative_percentage, 1),
        'neutral_percentage': round(neutral_percentage, 1)
    }