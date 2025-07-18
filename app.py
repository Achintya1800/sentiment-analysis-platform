from flask import Flask, render_template, request, jsonify
import os
from werkzeug.utils import secure_filename
import PyPDF2
import requests
import json
import re
import logging

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_text_from_pdf(pdf_file):
    """Extract text from uploaded PDF file"""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        return None

def analyze_sentiment_with_enhanced_insights(text, api_key):
    """
    Analyze sentiment with detailed word-level insights and explanations.
    """
    try:
        # Get basic sentiment analysis
        base_result = analyze_sentiment_with_google(text, api_key)
        
        if 'error' in base_result:
            return base_result
        
        # Analyze word-level sentiment
        word_insights = analyze_word_level_sentiment(text)
        
        # Generate explanations
        explanations = generate_sentiment_explanations(base_result, word_insights)
        
        # Combine results
        enhanced_result = base_result.copy()
        enhanced_result.update({
            'positive_words': word_insights['positive_words'],
            'negative_words': word_insights['negative_words'],
            'positive_phrases': word_insights['positive_phrases'],
            'negative_phrases': word_insights['negative_phrases'],
            'sentiment_explanation': explanations
        })
        
        return enhanced_result
        
    except Exception as e:
        logger.error(f"Enhanced sentiment analysis failed: {str(e)}")
        return {'error': f'Enhanced analysis failed: {str(e)}'}

def analyze_sentiment_with_google(text, api_key):
    """Standard Google Cloud sentiment analysis"""
    try:
        url = f"https://language.googleapis.com/v1/documents:analyzeSentiment?key={api_key}"
        
        # Clean and limit text length
        text = text.strip()
        if len(text) > 1000:
            text = text[:1000]
        
        # Remove problematic characters
        text = ''.join(char for char in text if ord(char) < 128)
        
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
            document_sentiment = result.get('documentSentiment', {})
            doc_score = float(document_sentiment.get('score', 0))
            doc_magnitude = float(document_sentiment.get('magnitude', 0))
            
            # If document score is near zero, calculate from sentences
            if abs(doc_score) < 0.01 and 'sentences' in result:
                sentence_scores = []
                for sentence in result['sentences']:
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
        else:
            return {'error': f'Google API Error: {response.status_code}'}
            
    except Exception as e:
        return {'error': f'API request failed: {str(e)}'}

def analyze_word_level_sentiment(text):
    """
    Analyze individual words and phrases for sentiment indicators.
    """
    # Define comprehensive sentiment word lists
    positive_words = [
        'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 
        'love', 'like', 'enjoy', 'happy', 'satisfied', 'pleased', 'perfect',
        'best', 'awesome', 'brilliant', 'outstanding', 'impressive', 'beautiful',
        'quality', 'recommend', 'worth', 'value', 'comfortable', 'easy',
        'superb', 'magnificent', 'delightful', 'marvelous', 'exceptional'
    ]
    
    negative_words = [
        'bad', 'terrible', 'awful', 'horrible', 'disgusting', 'hate', 'dislike',
        'disappointed', 'frustrated', 'angry', 'furious', 'worst', 'poor',
        'waste', 'money', 'regret', 'problem', 'issue', 'broken', 'useless',
        'cheap', 'uncomfortable', 'difficult', 'annoying', 'ridiculous',
        'pathetic', 'dreadful', 'appalling', 'atrocious', 'abysmal'
    ]
    
    text_lower = text.lower()
    
    # Find positive words with context
    found_positive = []
    for word in positive_words:
        if word in text_lower:
            count = text_lower.count(word)
            context = find_word_context(text, word)
            found_positive.append({
                'word': word,
                'count': count,
                'context': context
            })
    
    # Find negative words with context
    found_negative = []
    for word in negative_words:
        if word in text_lower:
            count = text_lower.count(word)
            context = find_word_context(text, word)
            found_negative.append({
                'word': word,
                'count': count,
                'context': context
            })
    
    # Find sentiment phrases
    positive_phrases = find_sentiment_phrases(text, positive=True)
    negative_phrases = find_sentiment_phrases(text, positive=False)
    
    return {
        'positive_words': found_positive,
        'negative_words': found_negative,
        'positive_phrases': positive_phrases,
        'negative_phrases': negative_phrases
    }

def find_word_context(text, word, context_length=50):
    """Find the context around a specific word in the text."""
    pattern = r'\b' + re.escape(word) + r'\b'
    match = re.search(pattern, text, re.IGNORECASE)
    
    if match:
        start = max(0, match.start() - context_length)
        end = min(len(text), match.end() + context_length)
        context = text[start:end].strip()
        return context
    
    return f"...{word}..."

def find_sentiment_phrases(text, positive=True):
    """Find common sentiment phrases in the text."""
    if positive:
        phrases = [
            'love it', 'really good', 'highly recommend', 'works great',
            'very satisfied', 'excellent quality', 'money well spent',
            'perfect for', 'really happy', 'great value', 'amazing quality'
        ]
    else:
        phrases = [
            'waste of money', 'completely useless', 'terrible quality',
            'deeply regret', 'absolutely furious', 'worst product',
            'total disappointment', 'complete waste', 'hands down the worst',
            'awful experience', 'really disappointed', 'absolute garbage'
        ]
    
    found_phrases = []
    text_lower = text.lower()
    
    for phrase in phrases:
        if phrase in text_lower:
            context = find_word_context(text, phrase, 30)
            found_phrases.append({
                'phrase': phrase,
                'context': context
            })
    
    return found_phrases

def generate_sentiment_explanations(base_result, word_insights):
    """Generate explanations for why the sentiment percentages were calculated."""
    positive_pct = base_result.get('positive_percentage', 0)
    negative_pct = base_result.get('negative_percentage', 0)
    overall = base_result.get('overall_sentiment', 'Neutral')
    
    positive_words_count = len(word_insights['positive_words'])
    negative_words_count = len(word_insights['negative_words'])
    
    explanations = {}
    
    # Positive explanation
    if positive_words_count > 0:
        pos_words = [item['word'] for item in word_insights['positive_words'][:5]]
        explanations['positive_explanation'] = (
            f"The {positive_pct}% positive sentiment is based on {positive_words_count} positive indicators "
            f"found in the text, including words like: {', '.join(pos_words)}. "
            f"These words contribute to the overall positive tone, though they may be overshadowed by negative elements."
        )
    else:
        explanations['positive_explanation'] = (
            f"The {positive_pct}% positive sentiment comes from neutral language and context, "
            f"with no specific positive words detected."
        )
    
    # Negative explanation
    if negative_words_count > 0:
        neg_words = [item['word'] for item in word_insights['negative_words'][:5]]
        explanations['negative_explanation'] = (
            f"The {negative_pct}% negative sentiment is driven by {negative_words_count} negative indicators "
            f"including words such as: {', '.join(neg_words)}. "
            f"These words create a strongly negative impression and dominate the overall tone."
        )
    else:
        explanations['negative_explanation'] = (
            f"The {negative_pct}% negative sentiment is inferred from the overall context and tone, "
            f"even without specific negative words being detected."
        )
    
    # Overall explanation
    if overall == 'Negative':
        explanations['overall_explanation'] = (
            f"The document is classified as '{overall}' because negative sentiment significantly "
            f"outweighs positive sentiment ({negative_pct}% vs {positive_pct}%). "
            f"The negative indicators have a stronger impact on the overall tone."
        )
    elif overall == 'Positive':
        explanations['overall_explanation'] = (
            f"The document is classified as '{overall}' because positive sentiment dominates "
            f"the text ({positive_pct}% vs {negative_pct}%). "
            f"The positive indicators create an overall favorable impression."
        )
    else:
        explanations['overall_explanation'] = (
            f"The document is classified as '{overall}' because positive and negative sentiments "
            f"are relatively balanced ({positive_pct}% positive vs {negative_pct}% negative)."
        )
    
    return explanations

@app.route('/')
def home():
    """Render the enhanced sentiment analysis interface."""
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    """Analyze sentiment of uploaded PDF document with enhanced insights."""
    try:
        if 'pdf_file' not in request.files:
            return jsonify({'error': 'No PDF file uploaded'})
        
        file = request.files['pdf_file']
        api_key = request.form.get('api_key')
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'})
        
        if not api_key:
            return jsonify({'error': 'API key is required'})
        
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({'error': 'Please upload a PDF file'})
        
        # Extract text
        text = extract_text_from_pdf(file)
        
        if not text:
            return jsonify({'error': 'Could not extract text from PDF'})
        
        if len(text.strip()) < 10:
            return jsonify({'error': 'PDF contains insufficient text for analysis'})
        
        # Analyze sentiment with enhanced insights
        sentiment_result = analyze_sentiment_with_enhanced_insights(text, api_key)
        
        if 'error' in sentiment_result:
            return jsonify({'error': sentiment_result['error']})
        
        return jsonify({
            'success': True,
            'extracted_text': text[:300] + '...' if len(text) > 300 else text,
            'word_count': len(text.split()),
            'character_count': len(text),
            'sentiment_analysis': sentiment_result,
            'filename': secure_filename(file.filename)
        })
        
    except Exception as e:
        logger.error(f"Analysis error: {str(e)}")
        return jsonify({'error': f'An error occurred: {str(e)}'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)