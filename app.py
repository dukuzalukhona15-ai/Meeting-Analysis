from flask import Flask, request, render_template, send_file
from werkzeug.utils import secure_filename
import os
import time
import logging
import requests
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
import cohere
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO
import textwrap

load_dotenv()

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB limit
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///meetings.db'

# Ensure upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

db = SQLAlchemy(app)

# API keys
assemblyai_key = os.getenv('ASSEMBLYAI_API_KEY')

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Meeting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100))
    transcription = db.Column(db.Text)
    summary = db.Column(db.Text)
    sentiment = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

def transcribe_audio(file_path):
    headers = {'authorization': assemblyai_key}
    with open(file_path, 'rb') as f:
        upload_response = requests.post('https://api.assemblyai.com/v2/upload', headers=headers, data=f)
    if upload_response.status_code != 200:
        raise Exception(f"Upload failed: {upload_response.text}")
    upload_data = upload_response.json()
    upload_url = upload_data['upload_url']
    transcript_request = requests.post('https://api.assemblyai.com/v2/transcript', json={'audio_url': upload_url}, headers=headers)
    if transcript_request.status_code != 200:
        raise Exception(f"Transcript request failed: {transcript_request.text}")
    transcript_data = transcript_request.json()
    transcript_id = transcript_data['id']
    while True:
        status_response = requests.get(f'https://api.assemblyai.com/v2/transcript/{transcript_id}', headers=headers)
        if status_response.status_code != 200:
            raise Exception(f"Status check failed: {status_response.text}")
        status_data = status_response.json()
        if status_data['status'] == 'completed':
            return status_data['text']
        elif status_data['status'] == 'error':
            raise Exception(f"Transcription failed: {status_data['error']}")
        time.sleep(2)

def summarize_text(text):
    # Use Cohere Chat API for summarization
    co = cohere.Client(os.getenv('COHERE_API_KEY'))
    response = co.chat(
        message=f"Summarize the following meeting transcript and extract action items:\n\n{text}",
        model='command-a-03-2025',
        temperature=0.3
    )
    summary = response.text
    return summary

def analyze_sentiment(text):
    try:
        # Truncate text if too long (sentiment model max ~512 tokens, approx 2000 chars)
        if len(text) > 2000:
            text = text[:2000] + "..."
        headers = {'Authorization': f'Bearer {os.getenv("HUGGINGFACE_API_KEY")}'}
        response = requests.post('https://api-inference.huggingface.co/models/cardiffnlp/twitter-roberta-base-sentiment', headers=headers, json={'inputs': text})
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                if isinstance(data[0], list) and len(data[0]) > 0:
                    # Find the label with the highest score
                    results = data[0]
                    best_result = max(results, key=lambda x: x['score'])
                    label = best_result['label']
                    if label == 'LABEL_0':
                        sentiment = 'negative'
                    elif label == 'LABEL_1':
                        sentiment = 'neutral'
                    else:
                        sentiment = 'positive'
                    return f"The overall sentiment is {sentiment}."
                elif 'label' in data[0]:
                    result = data[0]
                    label = result['label']
                    if label == 'LABEL_0':
                        sentiment = 'negative'
                    elif label == 'LABEL_1':
                        sentiment = 'neutral'
                    else:
                        sentiment = 'positive'
                    return f"The overall sentiment is {sentiment}."
            elif 'error' in data:
                return "Sentiment analysis unavailable: Invalid API key or service error."
            else:
                return "Sentiment analysis unavailable: Unexpected response."
        else:
            return "Sentiment analysis unavailable: API request failed."
    except Exception as e:
        return f"Sentiment analysis unavailable: {str(e)}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    try:
        if 'audio' not in request.files:
            return render_template('error.html', error="No file part")
        file = request.files['audio']
        if file.filename == '':
            return render_template('error.html', error="No selected file")
        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # Transcribe using AssemblyAI
            transcription = transcribe_audio(filepath)

            # Summarize using Cohere
            summary = summarize_text(transcription)

            # Analyze sentiment
            sentiment = analyze_sentiment(transcription)

            # Save to database
            meeting = Meeting(filename=filename, transcription=transcription, summary=summary, sentiment=sentiment)
            db.session.add(meeting)
            db.session.commit()

            # Clean up uploaded file
            os.remove(filepath)

            return render_template('results.html', transcription=transcription, summary=summary, sentiment=sentiment, meeting_id=meeting.id)
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        return render_template('error.html', error=str(e))

@app.route('/download/<int:meeting_id>')
def download(meeting_id):
    meeting = Meeting.query.get_or_404(meeting_id)
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    left_margin = 50
    right_margin = 50
    usable_width = width - left_margin - right_margin
    line_height = 14
    max_lines_per_page = int((height - 150) / line_height)

    def draw_wrapped_text(text, start_y):
        wrapped_lines = []
        for paragraph in text.split('\n'):
            wrapped_lines.extend(textwrap.wrap(paragraph, width=95))
            wrapped_lines.append('')  # Add blank line between paragraphs
        y = start_y
        line_count = 0
        for line in wrapped_lines:
            if line_count >= max_lines_per_page:
                c.showPage()
                y = height - 100
                line_count = 0
            c.drawString(left_margin, y, line)
            y -= line_height
            line_count += 1
        return y

    c.setFont("Helvetica-Bold", 16)
    c.drawString(left_margin, height - 50, "Meeting Analysis Results")

    c.setFont("Helvetica-Bold", 12)
    c.drawString(left_margin, height - 80, "Transcription:")
    c.setFont("Helvetica", 10)
    y = height - 100
    y = draw_wrapped_text(meeting.transcription, y - line_height)

    c.showPage()
    c.setFont("Helvetica-Bold", 12)
    c.drawString(left_margin, height - 50, "Summary and Action Items:")
    c.setFont("Helvetica", 10)
    y = height - 70
    y = draw_wrapped_text(meeting.summary, y - line_height)

    c.showPage()
    c.setFont("Helvetica-Bold", 12)
    c.drawString(left_margin, height - 50, "Sentiment Analysis:")
    c.setFont("Helvetica", 10)
    c.drawString(left_margin, height - 70, meeting.sentiment)

    c.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f'meeting_results_{meeting_id}.pdf', mimetype='application/pdf')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
