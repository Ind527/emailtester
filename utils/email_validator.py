import re
import dns.resolver
import smtplib
import socket
from email_validator import validate_email, EmailNotValidError
from typing import Dict, List
import time

class EmailValidator:
    def __init__(self):
        self.mx_cache = {}
        self.smtp_timeout = 10
        
    def validate_single_email(self, email: str) -> Dict:
        """
        Validate a single email address with comprehensive checks
        """
        result = {
            'email': email,
            'is_valid': False,
            'confidence': 0.0,
            'syntax_valid': False,
            'domain_valid': False,
            'mx_valid': False,
            'smtp_valid': False,
            'error': None
        }
        
        try:
            # Step 1: Syntax validation using email-validator
            try:
                valid_email = validate_email(email)
                result['syntax_valid'] = True
                result['confidence'] += 25
                email = valid_email.email
            except EmailNotValidError as e:
                result['error'] = f"Syntax error: {str(e)}"
                return result
            
            # Step 2: Domain existence check
            domain = email.split('@')[1]
            if self._check_domain_exists(domain):
                result['domain_valid'] = True
                result['confidence'] += 25
            else:
                result['error'] = "Domain does not exist"
                return result
            
            # Step 3: MX record check
            mx_records = self._get_mx_records(domain)
            if mx_records:
                result['mx_valid'] = True
                result['confidence'] += 25
            else:
                result['error'] = "No MX records found"
                result['confidence'] += 10  # Domain exists but no MX
            
            # Step 4: SMTP verification (optional, can be slow)
            if mx_records:
                smtp_result = self._check_smtp_deliverability(email, mx_records[0])
                if smtp_result['valid']:
                    result['smtp_valid'] = True
                    result['confidence'] += 25
                elif smtp_result['error']:
                    result['error'] = f"SMTP check: {smtp_result['error']}"
                    result['confidence'] += 10  # Inconclusive
            
            # Final validation decision
            result['is_valid'] = result['confidence'] >= 75
            
        except Exception as e:
            result['error'] = f"Validation error: {str(e)}"
        
        return result
    
    def _check_domain_exists(self, domain: str) -> bool:
        """Check if domain exists via DNS lookup"""
        try:
            dns.resolver.resolve(domain, 'A')
            return True
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, Exception):
            try:
                # Try AAAA record for IPv6
                dns.resolver.resolve(domain, 'AAAA')
                return True
            except:
                return False
    
    def _get_mx_records(self, domain: str) -> List[str]:
        """Get MX records for domain"""
        if domain in self.mx_cache:
            return self.mx_cache[domain]
        
        try:
            mx_records = dns.resolver.resolve(domain, 'MX')
            # Sort by preference and get exchange hostnames
            sorted_mx = sorted(mx_records, key=lambda x: getattr(x, 'preference', 0))
            mx_list = [str(getattr(mx, 'exchange', mx)).rstrip('.') for mx in sorted_mx]
            self.mx_cache[domain] = mx_list
            return mx_list
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, Exception):
            self.mx_cache[domain] = []
            return []
    
    def _check_smtp_deliverability(self, email: str, mx_server: str) -> Dict:
        """Check if email exists via SMTP verification"""
        result = {'valid': False, 'error': None}
        
        try:
            # Connect to SMTP server
            server = smtplib.SMTP(timeout=self.smtp_timeout)
            server.connect(mx_server, 25)
            server.helo('example.com')
            
            # Try to start mail transaction
            code, message = server.mail('test@example.com')
            if code != 250:
                result['error'] = f"MAIL command failed: {message}"
                server.quit()
                return result
            
            # Check if recipient exists
            code, message = server.rcpt(email)
            server.quit()
            
            if code == 250:
                result['valid'] = True
            elif code in [450, 451, 452]:
                result['error'] = "Temporary failure, mailbox may exist"
            elif code in [550, 551, 552, 553]:
                result['error'] = "Mailbox does not exist or rejected"
            else:
                result['error'] = f"SMTP error {code}: {message}"
                
        except socket.timeout:
            result['error'] = "SMTP connection timeout"
        except socket.gaierror:
            result['error'] = "Cannot connect to mail server"
        except smtplib.SMTPConnectError:
            result['error'] = "Cannot connect to SMTP server"
        except smtplib.SMTPServerDisconnected:
            result['error'] = "SMTP server disconnected"
        except Exception as e:
            result['error'] = f"SMTP check failed: {str(e)}"
        
        return result
    
    def validate_bulk_emails(self, emails: List[str], progress_callback=None) -> List[Dict]:
        """Validate multiple emails with progress tracking"""
        results = []
        
        for i, email in enumerate(emails):
            result = self.validate_single_email(email)
            results.append(result)
            
            if progress_callback:
                progress_callback(i + 1, len(emails), email)
            
            # Small delay to avoid overwhelming servers
            time.sleep(0.1)
        
        return results
