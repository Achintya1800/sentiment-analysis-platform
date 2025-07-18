"""
Enhanced Sentiment Analysis with Word-Level Insights
Shows specific words/phrases that contribute to positive and negative sentiment.
"""

import requests
import json
import logging
from typing import Dict, Any, List, Tuple
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def analyze_sentiment_with_detailed_insights(text: str, api_key: str) -> Dict[str, Any]:
    """
    Analyze sentiment with detailed word-level insights and explanations.
    
    Args:
        text (str): Text content to analyze
        api_key (str): Google Cloud API key
        
    Returns:
        Dict[str, Any]: Enhanced sentiment analysis results with word insights
    """
    try:
        # First, get the standard sentiment analysis
        base_result = analyze_sentiment_with_google(text, api_key)
        
        if 'error' in base_result:
            return base_result
        
        # Get detailed entity sentiment analysis
        entity_result = analyze_entity_sentiment(text, api_key)
        
        # Analyze text for specific positive/negative indicators
        word_insights = analyze_word_level_sentiment(text)
        
        # Combine results
        enhanced_result = base_result.copy()
        enhanced_result.update({
            'positive_words': word_insights['positive_words'],
            'negative_words': word_insights['negative_words'],
            'positive_phrases': word_insights['positive_phrases'],
            'negative_phrases': word_insights['negative_phrases'],
            'sentiment_explanation': generate_sentiment_explanation(base_result, word_insights),
            'entity_sentiment': entity_result.get('entities', []),
            'detailed_breakdown': generate_detailed_breakdown(base_result, word_insights)
        })
        
        return enhanced_result
        
    except Exception as e:
        logger.error(f"Enhanced sentiment analysis failed: {str(e)}")
        return {'error': f'Enhanced analysis failed: {str(e)}'}

def analyze_sentiment_with_google(text: str, api_key: str) -> Dict[str, Any]:
    """
    Standard Google Cloud sentiment analysis (your existing function).
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
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            return _process_sentiment_response(result, text)
        else:
            return {'error': f'Google API Error: {response.status_code}'}
            
    except Exception as e:
        return {'error': f'API request failed: {str(e)}'}

def analyze_entity_sentiment(text: str, api_key: str) -> Dict[str, Any]:
    """
    Analyze sentiment of specific entities in the text.
    """
    try:
        url = f"https://language.googleapis.com/v1/documents:analyzeEntitySentiment?key={api_key}"
        
        text = _preprocess_text_for_api(text)
        
        payload = {
            "document": {
                "type": "PLAIN_TEXT",
                "content": text
            },
            "encodingType": "UTF8"
        }
        
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.warning(f"Entity sentiment analysis failed: {response.status_code}")
            return {'entities': []}
            
    except Exception as e:
        logger.warning(f"Entity sentiment analysis error: {str(e)}")
        return {'entities': []}

def analyze_word_level_sentiment(text: str) -> Dict[str, List[str]]:
    """
    Analyze individual words and phrases for sentiment indicators.
    """
    # Define sentiment word lists
    positive_words = [
        'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 
        'love', 'like', 'enjoy', 'happy', 'satisfied', 'pleased', 'perfect',
        'best', 'awesome', 'brilliant', 'outstanding', 'impressive', 'beautiful',
        'quality', 'recommend', 'worth', 'value', 'comfortable', 'easy'
    ]
    
    negative_words = [
        'bad', 'terrible', 'awful', 'horrible', 'disgusting', 'hate', 'dislike',
        'disappointed', 'frustrated', 'angry', 'furious', 'worst', 'poor',
        'waste', 'money', 'regret', 'problem', 'issue', 'broken', 'useless',
        'cheap', 'uncomfortable', 'difficult', 'annoying', 'ridiculous'
    ]
    
    # Convert text to lowercase for analysis
    text_lower = text.lower()
    words = re.findall(r'\b\w+\b', text_lower)
    
    # Find positive and negative words
    found_positive = []
    found_negative = []
    
    for word in positive_words:
        if word in text_lower:
            # Count occurrences and find context
            count = text_lower.count(word)
            context = _find_word_context(text, word)
            found_positive.append({
                'word': word,
                'count': count,
                'context': context[:100] + '...' if len(context) > 100 else context
            })
    
    for word in negative_words:
        if word in text_lower:
            count = text_lower.count(word)
            context = _find_word_context(text, word)
            found_negative.append({
                'word': word,
                'count': count,
                'context': context[:100] + '...' if len(context) > 100 else context
            })
    
    # Find sentiment phrases
    positive_phrases = _find_sentiment_phrases(text, positive=True)
    negative_phrases = _find_sentiment_phrases(text, positive=False)
    
    return {
        'positive_words': found_positive,
        'negative_words': found_negative,
        'positive_phrases': positive_phrases,
        'negative_phrases': negative_phrases
    }

def _find_word_context(text: str, word: str, context_length: int = 50) -> str:
    """
    Find the context around a specific word in the text.
    """
    import re
    
    # Case-insensitive search for word boundaries
    pattern = r'\b' + re.escape(word) + r'\b'
    match = re.search(pattern, text, re.IGNORECASE)
    
    if match:
        start = max(0, match.start() - context_length)
        end = min(len(text), match.end() + context_length)
        return text[start:end].strip()
    
    return f"...{word}..."

def _find_sentiment_phrases(text: str, positive: bool = True) -> List[str]:
    """
    Find common sentiment phrases in the text.
    """
    if positive:
        phrases = [
            'love it', 'really good', 'highly recommend', 'works great',
            'very satisfied', 'excellent quality', 'money well spent',
            'perfect for', 'really happy', 'great value'
        ]
    else:
        phrases = [
            'waste of money', 'completely useless', 'terrible quality',
            'deeply regret', 'absolutely furious', 'worst product',
            'total disappointment', 'complete waste', 'hands down the worst',
            'awful experience', 'really disappointed'
        ]
    
    found_phrases = []
    text_lower = text.lower()
    
    for phrase in phrases:
        if phrase in text_lower:
            context = _find_word_context(text, phrase, 30)
            found_phrases.append({
                'phrase': phrase,
                'context': context
            })
    
    return found_phrases

def generate_sentiment_explanation(base_result: Dict[str, Any], word_insights: Dict[str, List]) -> Dict[str, str]:
    """
    Generate explanations for why the sentiment percentages were calculated.
    """
    positive_pct = base_result.get('positive_percentage', 0)
    negative_pct = base_result.get('negative_percentage', 0)
    overall = base_result.get('overall_sentiment', 'Neutral')
    
    positive_words_count = len(word_insights['positive_words'])
    negative_words_count = len(word_insights['negative_words'])
    
    explanations = {}
    
    # Positive explanation
    if positive_pct > 0:
        pos_words = [item['word'] for item in word_insights['positive_words']]
        explanations['positive_explanation'] = (
            f"The {positive_pct}% positive sentiment comes from {positive_words_count} positive indicators "
            f"found in the text. Key positive words include: {', '.join(pos_words[:5])}. "
            f"However, these are overshadowed by stronger negative sentiment."
        )
    
    # Negative explanation
    if negative_pct > 0:
        neg_words = [item['word'] for item in word_insights['negative_words']]
        explanations['negative_explanation'] = (
            f"The {negative_pct}% negative sentiment is driven by {negative_words_count} negative indicators "
            f"such as: {', '.join(neg_words[:5])}. These words create a strongly negative overall tone."
        )
    
    # Overall explanation
    explanations['overall_explanation'] = (
        f"The document is classified as '{overall}' because "
        f"{'negative sentiment significantly outweighs positive sentiment' if overall == 'Negative' else 'positive and negative sentiments are balanced' if overall == 'Neutral' else 'positive sentiment dominates the text'}."
    )
    
    return explanations

def generate_detailed_breakdown(base_result: Dict[str, Any], word_insights: Dict[str, List]) -> Dict[str, Any]:
    """
    Generate a detailed breakdown of the sentiment analysis.
    """
    return {
        'sentiment_score': base_result.get('google_raw_score', 0),
        'confidence': base_result.get('confidence_score', 0),
        'magnitude': base_result.get('magnitude', 0),
        'positive_indicators': len(word_insights['positive_words']),
        'negative_indicators': len(word_insights['negative_words']),
        'positive_phrases_found': len(word_insights['positive_phrases']),
        'negative_phrases_found': len(word_insights['negative_phrases']),
        'dominant_sentiment': 'negative' if base_result.get('negative_percentage', 0) > base_result.get('positive_percentage', 0) else 'positive'
    }

def _preprocess_text_for_api(text: str) -> str:
    """
    Preprocess text for Google Cloud API.
    """
    text = text.strip()
    if len(text) > 1000:
        text = text[:1000]
    text = ''.join(char for char in text if ord(char) < 128)
    return text

def _process_sentiment_response(api_response: Dict[str, Any], original_text: str) -> Dict[str, Any]:
    """
    Process Google Cloud API response (your existing function).
    """
    try:
        document_sentiment = api_response.get('documentSentiment', {})
        doc_score = float(document_sentiment.get('score', 0))
        doc_magnitude = float(document_sentiment.get('magnitude', 0))
        
        # If document score is near zero, calculate from sentences
        if abs(doc_score) < 0.01 and 'sentences' in api_response:
            sentence_scores = []
            for sentence in api_response['sentences']:
                sent_sentiment = sentence.get('sentiment', {})
                sent_score = sent_sentiment.get('score', 0)
                if sent_score != 0:
                    sentence_scores.append(float(sent_score))
            
            if sentence_scores:
                doc_score = sum(sentence_scores) / len(sentence_scores)
        
        # Calculate sentiment classification
        if doc_score > 0.02:
            overall_sentiment = "Positive"
            positive_percentage = 60 + (doc_score * 200)
            negative_percentage = 40 - (doc_score * 200)
        elif doc_score < -0.02:
            overall_sentiment = "Negative"
            positive_percentage = 40 + (doc_score * 200)
            negative_percentage = 60 - (doc_score * 200)
        else:
            overall_sentiment = "Neutral"
            positive_percentage = 50 + (doc_score * 100)
            negative_percentage = 50 - (doc_score * 100)
        
        # Ensure bounds
        positive_percentage = max(5, min(95, positive_percentage))
        negative_percentage = max(5, min(95, negative_percentage))
        neutral_percentage = max(0, 100 - positive_percentage - negative_percentage)
        
        return {
            'overall_sentiment': overall_sentiment,
            'positive_percentage': round(positive_percentage, 1),
            'negative_percentage': round(negative_percentage, 1),
            'neutral_percentage': round(neutral_percentage, 1),
            'confidence_score': round(abs(doc_score), 3),
            'magnitude': round(doc_magnitude, 3),
            'google_raw_score': doc_score
        }
        
    except Exception as e:
        return {'error': f'Failed to process sentiment data: {str(e)}'}