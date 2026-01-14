import unittest
import os
from app import app, db, Meeting
from io import BytesIO

class MeetingAnalysisAppTestCase(unittest.TestCase):
    def setUp(self):
        # Configure app for testing
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app = app.test_client()
        with app.app_context():
            db.create_all()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_homepage_loads(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Upload', response.data)

    def test_upload_no_file(self):
        response = self.app.post('/process', data={})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'No file part', response.data)

    def test_upload_empty_file(self):
        data = {'audio': (BytesIO(b''), '')}
        response = self.app.post('/process', data=data, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'No selected file', response.data)

    # Note: The following test requires valid API keys and internet access.
    # It tests the full upload, transcription, summarization, sentiment flow.
    # You may want to mock external API calls for isolated unit testing.

    # def test_full_process_flow(self):
    #     with open('tests/sample_audio.wav', 'rb') as f:
    #         data = {'audio': (f, 'sample_audio.wav')}
    #         response = self.app.post('/process', data=data, content_type='multipart/form-data')
    #         self.assertEqual(response.status_code, 200)
    #         self.assertIn(b'Transcription', response.data)
    #         self.assertIn(b'Summary', response.data)
    #         self.assertIn(b'Sentiment', response.data)

    def test_download_pdf_not_found(self):
        response = self.app.get('/download/999')
        self.assertEqual(response.status_code, 404)

if __name__ == '__main__':
    unittest.main()
