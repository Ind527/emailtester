import re
import requests
import trafilatura
from urllib.parse import urljoin, urlparse
import time
from typing import List, Dict, Set
import dns.resolver
import urllib3


class EmailDiscovery:
    def __init__(self):
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        self.common_pages = [
            '',
            '/contact',
            '/contact-us',
            '/about',
            '/about-us',
            '/team',
            '/staff',
            '/people',
            '/leadership',
            '/management',
            '/careers',
            '/jobs',
            '/support',
            '/help'
        ]
        
        # Setup request session with proper headers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        self.session.verify = False  # Handle SSL issues for some sites
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)  # Disable SSL warnings
        
    def discover_emails_from_domain(self, domain: str, max_pages: int = 5) -> Dict:
        """
        Discover email addresses from a domain website
        """
        if not domain.startswith(('http://', 'https://')):
            domain = f"https://{domain}"
            
        result = {
            'domain': domain,
            'emails_found': set(),
            'pages_scanned': [],
            'common_patterns': set(),
            'status': 'success'
        }
        
        try:
            # Check if domain is reachable with better method
            response = self.session.get(domain, timeout=15, allow_redirects=True)
            if response.status_code >= 400:
                result['status'] = 'domain_unreachable'
                result['error'] = f'HTTP {response.status_code}: {response.reason}'
                return result
                
        except requests.exceptions.SSLError:
            # Try with HTTP if HTTPS fails
            try:
                http_domain = domain.replace('https://', 'http://')
                response = self.session.get(http_domain, timeout=15, allow_redirects=True)
                if response.status_code >= 400:
                    result['status'] = 'domain_unreachable'
                    result['error'] = f'HTTP {response.status_code}: {response.reason}'
                    return result
                domain = http_domain  # Use HTTP version if HTTPS fails
            except Exception as e:
                result['status'] = 'domain_unreachable'
                result['error'] = f'SSL Error and HTTP fallback failed: {str(e)}'
                return result
        except requests.exceptions.Timeout:
            result['status'] = 'domain_unreachable'
            result['error'] = 'Connection timeout - domain took too long to respond'
            return result
        except requests.exceptions.ConnectionError:
            result['status'] = 'domain_unreachable'
            result['error'] = 'Connection failed - unable to reach domain'
            return result
        except Exception as e:
            result['status'] = 'domain_unreachable'
            result['error'] = f'Unexpected error: {str(e)}'
            return result
        
        pages_to_scan = []
        base_domain = urlparse(domain).netloc
        
        # Add main page and common pages
        for page in self.common_pages[:max_pages]:
            page_url = urljoin(domain, page)
            pages_to_scan.append(page_url)
        
        # Scan each page
        for page_url in pages_to_scan:
            try:
                emails = self._extract_emails_from_page(page_url)
                if emails:
                    result['emails_found'].update(emails)
                    result['pages_scanned'].append(page_url)
                
                # Add delay to be respectful
                time.sleep(1)
                
            except Exception as e:
                continue
        
        # Generate common email patterns based on domain
        result['common_patterns'] = self._generate_email_patterns(base_domain)
        
        # Convert sets to lists for JSON serialization
        result['emails_found'] = list(result['emails_found'])
        result['common_patterns'] = list(result['common_patterns'])
        
        return result
    
    def _extract_emails_from_page(self, url: str) -> Set[str]:
        """
        Extract emails from a single webpage
        """
        emails = set()
        
        try:
            # Try to fetch content using our configured session first
            response = self.session.get(url, timeout=10, allow_redirects=True)
            if response.status_code == 200:
                # Extract emails from raw HTML
                html_emails = self.email_pattern.findall(response.text)
                emails.update(html_emails)
                
                # Use trafilatura for clean text extraction
                text_content = trafilatura.extract(response.text)
                if text_content:
                    found_emails = self.email_pattern.findall(text_content)
                    emails.update(found_emails)
            else:
                # Fallback to trafilatura's fetch method
                downloaded = trafilatura.fetch_url(url)
                if downloaded:
                    text_content = trafilatura.extract(downloaded)
                    if text_content:
                        found_emails = self.email_pattern.findall(text_content)
                        emails.update(found_emails)
                    
                    # Also check raw HTML
                    html_emails = self.email_pattern.findall(downloaded)
                    emails.update(html_emails)
                
        except Exception as e:
            # If our method fails, try trafilatura fallback
            try:
                downloaded = trafilatura.fetch_url(url)
                if downloaded:
                    text_content = trafilatura.extract(downloaded)
                    if text_content:
                        found_emails = self.email_pattern.findall(text_content)
                        emails.update(found_emails)
                    
                    html_emails = self.email_pattern.findall(downloaded)
                    emails.update(html_emails)
            except:
                pass
        
        # Filter out common false positives
        filtered_emails = set()
        for email in emails:
            if self._is_valid_email_discovery(email):
                filtered_emails.add(email.lower())
        
        return filtered_emails
    
    def _is_valid_email_discovery(self, email: str) -> bool:
        """
        Basic filtering for email discovery
        """
        # Filter out common false positives
        false_positives = [
            'example@example.com',
            'test@test.com',
            'admin@admin.com',
            'user@user.com',
            'info@info.com',
            'contact@contact.com'
        ]
        
        if email.lower() in false_positives:
            return False
            
        # Filter out emails with common placeholder domains
        placeholder_domains = ['example.com', 'test.com', 'domain.com', 'yoursite.com']
        domain = email.split('@')[1].lower()
        
        if domain in placeholder_domains:
            return False
            
        return True
    
    def _generate_email_patterns(self, domain: str) -> Set[str]:
        """
        Generate common email patterns for a domain
        """
        patterns = set()
        
        # Common email prefixes
        common_prefixes = [
            'info',
            'contact',
            'hello',
            'hi',
            'support',
            'sales',
            'admin',
            'office',
            'team',
            'help',
            'service',
            'marketing',
            'hr',
            'careers',
            'jobs'
        ]
        
        for prefix in common_prefixes:
            patterns.add(f"{prefix}@{domain}")
        
        return patterns
    
    def verify_email_patterns(self, patterns: List[str], validator) -> Dict:
        """
        Verify discovered email patterns using the email validator
        """
        results = []
        
        for email in patterns:
            try:
                result = validator.validate_single_email(email)
                results.append({
                    'email': email,
                    'is_valid': result['is_valid'],
                    'confidence': result['confidence'],
                    'details': result
                })
            except Exception as e:
                results.append({
                    'email': email,
                    'is_valid': False,
                    'confidence': 0,
                    'error': str(e)
                })
        
        return {
            'total_checked': len(results),
            'valid_emails': [r for r in results if r['is_valid']],
            'invalid_emails': [r for r in results if not r['is_valid']],
            'results': results
        }