# TODO: Implement PDF Download Button for Meeting Results

- [x] Update requirements.txt to include 'reportlab' for PDF generation
- [x] Modify app.py: In /process route, pass meeting.id to results.html template as 'meeting_id'
- [x] Modify app.py: Add new /download/<int:meeting_id> route to generate and send PDF
- [x] Modify results.html: Add download button linking to /download/{{ meeting_id }}
- [x] Install new dependency: Run pip install reportlab
- [ ] Test the download functionality
