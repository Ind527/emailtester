import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Dict, Optional
import time
from datetime import datetime

class EmailSender:
    def __init__(self, credentials: Dict):
        self.smtp_server = credentials['smtp_server']
        self.smtp_port = credentials['smtp_port']
        self.email = credentials['email']
        self.password = credentials['password']
    
    def send_single_email(self, recipient: str, subject: str, message: str, 
                         is_html: bool = False, attachments: Optional[List] = None) -> Dict:
        """
        Send a single email
        """
        result = {
            'recipient': recipient,
            'success': False,
            'error': None,
            'sent_time': None
        }
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.email
            msg['To'] = recipient
            msg['Subject'] = subject
            
            # Add body to email
            if is_html:
                msg.attach(MIMEText(message, 'html'))
            else:
                msg.attach(MIMEText(message, 'plain'))
            
            # Add attachments if any
            if attachments:
                for attachment in attachments:
                    self._add_attachment(msg, attachment)
            
            # Create SMTP session
            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.email, self.password)
                
                # Send email
                server.send_message(msg)
                
                result['success'] = True
                result['sent_time'] = datetime.now().isoformat()
                
        except smtplib.SMTPAuthenticationError:
            result['error'] = "Authentication failed. Check email credentials."
        except smtplib.SMTPRecipientsRefused:
            result['error'] = "Recipient email address was refused by server."
        except smtplib.SMTPSenderRefused:
            result['error'] = "Sender email address was refused by server."
        except smtplib.SMTPDataError:
            result['error'] = "SMTP data error occurred."
        except smtplib.SMTPConnectError:
            result['error'] = "Failed to connect to SMTP server."
        except smtplib.SMTPServerDisconnected:
            result['error'] = "SMTP server disconnected unexpectedly."
        except Exception as e:
            result['error'] = f"Unexpected error: {str(e)}"
        
        return result
    
    def send_bulk_email(self, recipients: List[str], subject: str, message: str, 
                       is_html: bool = False, delay: float = 0.5) -> List[Dict]:
        """
        Send email to multiple recipients with optional delay between sends
        """
        results = []
        
        for i, recipient in enumerate(recipients):
            result = self.send_single_email(recipient, subject, message, is_html)
            results.append(result)
            
            # Add delay between sends to avoid being flagged as spam
            if i < len(recipients) - 1 and delay > 0:
                time.sleep(delay)
        
        return results
    
    def _add_attachment(self, msg: MIMEMultipart, file_path: str):
        """
        Add attachment to email message
        """
        try:
            with open(file_path, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
            
            encoders.encode_base64(part)
            
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {file_path.split("/")[-1]}',
            )
            
            msg.attach(part)
        except Exception as e:
            print(f"Failed to attach file {file_path}: {str(e)}")
    
    def test_connection(self) -> Dict:
        """
        Test SMTP connection and credentials
        """
        result = {
            'success': False,
            'error': None
        }
        
        try:
            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.email, self.password)
                
                result['success'] = True
                
        except smtplib.SMTPAuthenticationError:
            result['error'] = "Authentication failed. Check your email and password."
        except smtplib.SMTPConnectError:
            result['error'] = f"Cannot connect to SMTP server {self.smtp_server}:{self.smtp_port}"
        except Exception as e:
            result['error'] = f"Connection test failed: {str(e)}"
        
        return result

class EmailTemplate:
    """
    Simple email template system
    """
    
    @staticmethod
    def create_welcome_template(name: str, company: str) -> str:
        return f"""
        <html>
        <body>
        <h2>Welcome {name}!</h2>
        <p>Thank you for joining {company}. We're excited to have you on board!</p>
        <p>If you have any questions, please don't hesitate to reach out.</p>
        <br>
        <p>Best regards,<br>The {company} Team</p>
        </body>
        </html>
        """
    
    @staticmethod
    def create_newsletter_template(title: str, content: str, unsubscribe_link: str) -> str:
        return f"""
        <html>
        <body>
        <h1>{title}</h1>
        <div>{content}</div>
        <hr>
        <p><small>
        Don't want to receive these emails? 
        <a href="{unsubscribe_link}">Unsubscribe here</a>
        </small></p>
        </body>
        </html>
        """
    
    @staticmethod
    def create_notification_template(subject: str, message: str, action_url: Optional[str] = None) -> str:
        template = f"""
        <html>
        <body>
        <h2>{subject}</h2>
        <p>{message}</p>
        """
        
        if action_url:
            template += f'<p><a href="{action_url}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Take Action</a></p>'
        
        template += """
        </body>
        </html>
        """
        
        return template
