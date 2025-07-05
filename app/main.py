from flask import Flask, render_template, request, jsonify
import os
from werkzeug.utils import secure_filename
import PyPDF2
import requests
import json

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def extract_text_from_pdf(pdf_file):
    """Extract text from uploaded PDF file"""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        return None

def analyze_sentiment_with_google(text, api_key):
    """Analyze sentiment using Google Cloud Natural Language API"""
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

@app.route('/')
def home():
    """Render the main sentiment analysis interface."""
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    """Analyze sentiment of uploaded PDF document."""
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
        
        # Analyze sentiment
        sentiment_result = analyze_sentiment_with_google(text, api_key)
        
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
        return jsonify({'error': f'An error occurred: {str(e)}'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)