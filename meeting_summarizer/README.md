# Meeting Summarizer

## Project Overview
This is a Flask-based web application that allows users to upload audio recordings of meetings, transcribes the audio using AssemblyAI, summarizes the transcription using Cohere, and performs sentiment analysis using HuggingFace API. The results can be viewed on the web interface and downloaded as a PDF report.

## Prerequisites
- Python 3.8 or higher
- Virtual environment tool (optional but recommended)
- API keys for:
  - AssemblyAI (for transcription)
  - Cohere (for summarization)
  - HuggingFace (for sentiment analysis)

## Setup Instructions

1. Clone the repository:
   ```bash
   git clone https://github.com/Kgoliath/meeting_summarizer.git
   cd meeting_summarizer
   ```

2. (Optional) Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root with the following environment variables:
   ```
   ASSEMBLYAI_API_KEY=your_assemblyai_api_key
   COHERE_API_KEY=your_cohere_api_key
   HUGGINGFACE_API_KEY=your_huggingface_api_key
   ```

5. Initialize the database:
   ```bash
   python
   >>> from app import db, app
   >>> with app.app_context():
   ...     db.create_all()
   ... 
   >>> exit()
   ```

## Running the Application

Start the Flask development server by running:

```bash
python app.py
```

The app will be accessible at `http://127.0.0.1:5000/` in your web browser.

## Usage

- Upload an audio file of a meeting on the homepage.
- The app will transcribe, summarize, and analyze sentiment.
- View the results on the results page.
- Download a PDF report of the meeting analysis.

## Notes

- Ensure your API keys are valid and have sufficient quota.
- The app limits upload size to 100MB.
- The `.env` file is excluded from version control for security.
