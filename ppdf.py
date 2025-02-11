import os
import json
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
from typing import Dict, List
from pathlib import Path
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
LOGO_URL="https://i.ibb.co/27BWhrpG/images.jpg"

# Email configuration
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SENDER_EMAIL = os.getenv('SENDER_EMAIL')
SENDER_PASSWORD = os.getenv('SENDER_PASSWORD')

class MeetingReportEmailer:
    def __init__(self, meeting_logs_dir: str = "meeting_logs"):
        self.meeting_logs_dir = Path(meeting_logs_dir)
        
    def parse_meeting_log(self, log_path: Path) -> Dict:
        """Parse a meeting log file into a structured format"""
        meeting_data = {
            'meeting_info': {},
            'questions_and_responses': []
        }
        
        current_section = None
        
        with open(log_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                    
                if line.startswith('==='):
                    current_section = line.strip('= ')
                    continue
                    
                if ':' in line:
                    key, value = map(str.strip, line.split(':', 1))
                    if current_section == 'Meeting Summary':
                        meeting_data['meeting_info'][key.lower()] = value
                    elif current_section == 'Questions and Responses':
                        if key.startswith('Q'):
                            meeting_data['questions_and_responses'].append({'question': value})
                        elif key.startswith('A') and meeting_data['questions_and_responses']:
                            meeting_data['questions_and_responses'][-1]['answer'] = value
                            
        return meeting_data

    def generate_html_content(self, meeting_data: Dict) -> str:
        """Generate HTML content with embedded CSS for the email"""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                :root {
                    --primary-color: #1a365d;
                    --secondary-color: #2c5282;
                    --accent-color: #2b6cb0;
                    --background-color: #f7fafc;
                    --text-color: #2d3748;
                    --border-color: #e2e8f0;
                    --success-color: #2f855a;
                }
                
                body {
                    font-family: 'Helvetica Neue', Arial, sans-serif;
                    line-height: 1.8;
                    color: var(--text-color);
                    max-width: 900px;
                    margin: 0 auto;
                    background-color: var(--background-color);
                    padding: 20px;
                }
                
                .container {
                    background-color: white;
                    border-radius: 8px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    overflow: hidden;
                }
                
                .logo-section {
                    background-color: var(--primary-color);
                    padding: 30px;
                    text-align: center;
                    border-bottom: 4px solid var(--accent-color);
                }
                
                .logo-section img {
                    max-width: 240px;
                    height: auto;
                }
                
                .header-info {
                    text-align: center;
                    color: white;
                    margin-top: 15px;
                    font-size: 0.9em;
                }
                
                .content-section {
                    padding: 30px;
                    margin: 20px;
                    background-color: white;
                    border-radius: 6px;
                    border: 1px solid var(--border-color);
                }
                
                .section-title {
                    color: var(--primary-color);
                    font-size: 1.5em;
                    font-weight: 600;
                    margin-bottom: 20px;
                    padding-bottom: 10px;
                    border-bottom: 2px solid var(--accent-color);
                    letter-spacing: 0.5px;
                }
                
                .questions-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                    gap: 20px;
                    margin-top: 20px;
                }
                
                .question-card {
                    background-color: white;
                    padding: 20px;
                    border-radius: 6px;
                    border: 1px solid var(--border-color);
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
                    transition: transform 0.2s ease;
                }
                
                .question-card:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                }
                
                .meeting-info-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 20px;
                }
                
                .info-item {
                    padding: 15px;
                    background-color: var(--background-color);
                    border-radius: 6px;
                    margin-bottom: 10px;
                }
                
                .info-item strong {
                    color: var(--secondary-color);
                    display: block;
                    margin-bottom: 5px;
                    font-size: 0.9em;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }
                
                .qa-item {
                    margin-bottom: 30px;
                    border-left: 4px solid var(--accent-color);
                    padding-left: 20px;
                }
                
                .question {
                    background-color: var(--background-color);
                    padding: 15px 20px;
                    border-radius: 6px;
                    margin-bottom: 10px;
                    font-weight: 500;
                }
                
                .answer {
                    padding: 15px 20px;
                    border-radius: 6px;
                    background-color: white;
                    border: 1px solid var(--border-color);
                    margin-left: 20px;
                }
                
                .discussion-stats {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 20px;
                    margin-bottom: 20px;
                }
                
                .stat-card {
                    background-color: var(--background-color);
                    padding: 20px;
                    border-radius: 6px;
                    text-align: center;
                }
                
                .stat-value {
                    font-size: 1.5em;
                    color: var(--primary-color);
                    font-weight: bold;
                    margin-bottom: 5px;
                }
                
                .stat-label {
                    color: var(--secondary-color);
                    font-size: 0.9em;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }
                
                footer {
                    text-align: center;
                    padding: 20px;
                    color: var(--secondary-color);
                    font-size: 0.9em;
                    border-top: 1px solid var(--border-color);
                }
            </style>
        </head>
        <body>
            <div class="container">
        """
        
        # Add logo section with header info
        html_content += f"""
        <div class="logo-section">
                        <img src="{LOGO_URL}" alt="Company Logo" style="max-width: 240px; height: auto;">
                        <div class="header-info">
                            <h1 style="margin: 10px 0;">Meeting Summary Report</h1>

                        </div>
                    </div>
        """
        
        # Add key questions section
        html_content += """
            <div class="content-section">
                <h2 class="section-title">Key Discussion Points</h2>
                <div class="questions-grid">
        """
        
        for i, qa in enumerate(meeting_data['questions_and_responses'], 1):
            html_content += f"""
                <div class="question-card">
                    <strong style="color: var(--primary-color);">Topic {i}</strong>
                    <p>{qa['question']}</p>
                </div>
            """
        
        html_content += """
                </div>
            </div>
        """
        
        # Add meeting summary section
        html_content += """
            <div class="content-section">
                <h2 class="section-title">Meeting Summary</h2>
                <div class="meeting-info-grid">
        """
        
        for key, value in meeting_data['meeting_info'].items():
            html_content += f"""
                <div class="info-item">
                    <strong>{key.title()}</strong>
                    <span>{value}</span>
                </div>
            """
        
        html_content += """
                </div>
            </div>
        """
        
        # Add discussion overview section
        
        
        # Add detailed Q&A section
        html_content += """
            <div class="content-section">
                <h2 class="section-title">Detailed Discussion Points</h2>
        """
        
        for i, qa in enumerate(meeting_data['questions_and_responses'], 1):
            html_content += f"""
                <div class="qa-item">
                    <div class="question">
                        <strong style="color: var(--primary-color);">Topic {i}:</strong> {qa['question']}
                    </div>
                    <div class="answer">
                        <strong style="color: var(--success-color);">Response:</strong> {qa['answer']}
                    </div>
                </div>
            """
        
        html_content += """
            </div>
            <footer>
                <p>This is an automated meeting summary report. Please contact the meeting organizer for any clarifications.</p>
            </footer>
            </div>
        </body>
        </html>
        """
        
        return html_content

    def send_email(self, recipient_email: str, html_content: str, subject: str = "Meeting Summary Report"):
        """Send the HTML email"""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = SENDER_EMAIL
            msg['To'] = recipient_email

            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)

            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SENDER_EMAIL, SENDER_PASSWORD)
                server.send_message(msg)
                
            logger.info(f"Email sent successfully to {recipient_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False

    def process_and_send_report(self, log_file: str) -> bool:
        """Process a meeting log file and send the report"""
    
        recipient_email="workbusinesskeshav@gmail.com"
        try:
            log_path = self.meeting_logs_dir / log_file
            if not log_path.exists():
                logger.error(f"Log file not found: {log_path}")
                return False
                
            meeting_data = self.parse_meeting_log(log_path)
            html_content = self.generate_html_content(meeting_data)
            
            return self.send_email(
                recipient_email,
                html_content,
                f"Meeting Summary - {meeting_data['meeting_info'].get('date', 'Undated')}"
            )
            
        except Exception as e:
            logger.error(f"Error processing meeting report: {str(e)}")
            return False
#emailer = MeetingReportEmailer(meeting_logs_dir="meeting_logs")

# Call process_and_send_report with your log file name
#result = emailer.process_and_send_report("meeting_Rrahul Sethi_20250208_144000.txt")

# Check if the email was sent successfully
