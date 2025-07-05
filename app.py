from flask import Flask, render_template, request, jsonify
import PyPDF2
import requests
import json
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

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
        
        # Remove any problematic characters
        text = ''.join(char for char in text if ord(char) < 128)
        
        payload = {
            "document": {
                "type": "PLAIN_TEXT",
                "content": text
            },
            "encodingType": "UTF8"
        }
        
        headers = {"Content-Type": "application/json"}
        
        print(f"=== DEBUG INFO ===")
        print(f"Sending text: '{text[:100]}...'")
        
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        
        print(f"API Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            # Get document-level sentiment
            document_sentiment = result.get('documentSentiment', {})
            doc_score = document_sentiment.get('score', 0)
            doc_magnitude = document_sentiment.get('magnitude', 0)
            
            print(f"Document Score: {doc_score}, Document Magnitude: {doc_magnitude}")
            
            # If document score is 0, calculate from individual sentences
            if doc_score == 0 and 'sentences' in result:
                print("Document score is 0, calculating from sentences...")
                sentence_scores = []
                
                for sentence in result['sentences']:
                    sent_sentiment = sentence.get('sentiment', {})
                    sent_score = sent_sentiment.get('score', 0)
                    if sent_score != 0:
                        sentence_scores.append(sent_score)
                        print(f"Sentence score: {sent_score}")
                
                if sentence_scores:
                    # Average of sentence scores
                    avg_score = sum(sentence_scores) / len(sentence_scores)
                    print(f"Calculated average score from sentences: {avg_score}")
                    doc_score = avg_score
                    doc_magnitude = sum(abs(s) for s in sentence_scores) / len(sentence_scores)
            
            # Convert to float
            score = float(doc_score)
            magnitude = float(doc_magnitude)
            
            print(f"Final Score: {score}, Final Magnitude: {magnitude}")
            
            # More sensitive sentiment calculation
            if score > 0.02:  # Lower threshold for positive
                overall_sentiment = "Positive"
                positive_percentage = 60 + (score * 200)  # Amplify the effect
                negative_percentage = 40 - (score * 200)
            elif score < -0.02:  # Lower threshold for negative  
                overall_sentiment = "Negative"
                positive_percentage = 40 + (score * 200)  # score is negative, so this reduces positive%
                negative_percentage = 60 - (score * 200)  # score is negative, so this increases negative%
            else:
                overall_sentiment = "Neutral"
                positive_percentage = 50 + (score * 100)
                negative_percentage = 50 - (score * 100)
                
            # Ensure bounds
            positive_percentage = max(5, min(95, positive_percentage))
            negative_percentage = max(5, min(95, negative_percentage))
            neutral_percentage = max(0, 100 - positive_percentage - negative_percentage)
            
            print(f"Final Result - {overall_sentiment}: Pos {positive_percentage}%, Neg {negative_percentage}%")
            print(f"=== END DEBUG ===")
            
            return {
                'overall_sentiment': overall_sentiment,
                'positive_percentage': round(positive_percentage, 1),
                'negative_percentage': round(negative_percentage, 1), 
                'neutral_percentage': round(neutral_percentage, 1),
                'confidence_score': round(abs(score), 3),
                'magnitude': round(magnitude, 3),
                'google_raw_score': score
            }
            
        else:
            print(f"API Error: {response.status_code} - {response.text}")
            return {'error': f'Google API Error: {response.status_code}'}
            
    except Exception as e:
        print(f"Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': f'API request failed: {str(e)}'}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
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
        
        print(f"Extracted text: {text[:200]}...")  # Debug extracted text
        
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
            'filename': file.filename
        })
        
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'})

if __name__ == '__main__':
    app.run(debug=True)