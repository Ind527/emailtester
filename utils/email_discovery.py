import re
import requests
import trafilatura
from urllib.parse import urljoin, urlparse
import time
import random
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
        
        # Setup request session with comprehensive headers to avoid detection
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9,id;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'DNT': '1',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"'
        })
        self.session.verify = False  # Handle SSL issues for some sites
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)  # Disable SSL warnings
        
        # Alternative user agents for rotation
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
        ]
        
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
        
        # Try multiple strategies to access the domain
        access_successful = False
        final_domain = domain
        
        strategies = [
            {'method': 'GET', 'ua_rotate': False},
            {'method': 'GET', 'ua_rotate': True},
            {'method': 'HEAD', 'ua_rotate': True},
        ]
        
        for strategy in strategies:
            if access_successful:
                break
                
            try:
                # Add random delay to appear more human-like
                time.sleep(random.uniform(1, 3))
                
                # Rotate user agent if requested
                if strategy['ua_rotate']:
                    self.session.headers['User-Agent'] = random.choice(self.user_agents)
                
                # Add referrer to look more natural
                self.session.headers['Referer'] = 'https://www.google.com/'
                
                if strategy['method'] == 'HEAD':
                    response = self.session.head(domain, timeout=15, allow_redirects=True)
                else:
                    response = self.session.get(domain, timeout=15, allow_redirects=True)
                
                if response.status_code == 200:
                    access_successful = True
                    final_domain = domain
                    break
                elif response.status_code == 403:
                    # Try with different approach for 403
                    continue
                elif response.status_code >= 400:
                    continue
                else:
                    access_successful = True
                    final_domain = domain
                    break
                    
            except requests.exceptions.SSLError:
                # Try with HTTP if HTTPS fails
                try:
                    http_domain = domain.replace('https://', 'http://')
                    time.sleep(random.uniform(1, 2))
                    
                    if strategy['method'] == 'HEAD':
                        response = self.session.head(http_domain, timeout=15, allow_redirects=True)
                    else:
                        response = self.session.get(http_domain, timeout=15, allow_redirects=True)
                    
                    if response.status_code == 200 or (response.status_code < 400 and response.status_code >= 300):
                        access_successful = True
                        final_domain = http_domain
                        break
                except Exception:
                    continue
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
                continue
            except Exception:
                continue
        
        if not access_successful:
            # Final fallback - try to at least verify domain exists via DNS
            try:
                parsed_domain = urlparse(domain).netloc
                dns.resolver.resolve(parsed_domain, 'A')
                # Domain exists but website might be protected, continue with limited scan
                result['error'] = 'Website protected by anti-bot measures, attempting limited scan'
            except Exception:
                result['status'] = 'domain_unreachable'
                result['error'] = 'Domain not accessible - website may be down or blocking automated access'
                return result
        
        # Update domain to use the successful one
        domain = final_domain
        
        pages_to_scan = []
        base_domain = urlparse(domain).netloc
        
        # Add main page and common pages
        for page in self.common_pages[:max_pages]:
            page_url = urljoin(domain, page)
            pages_to_scan.append(page_url)
        
        # Scan each page with anti-detection measures
        for i, page_url in enumerate(pages_to_scan):
            try:
                # Add random delay between pages to appear human-like
                if i > 0:
                    time.sleep(random.uniform(2, 5))
                
                # Rotate user agent occasionally
                if random.random() < 0.3:  # 30% chance to rotate
                    self.session.headers['User-Agent'] = random.choice(self.user_agents)
                
                emails = self._extract_emails_from_page(page_url)
                if emails:
                    result['emails_found'].update(emails)
                    result['pages_scanned'].append(page_url)
                
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
        Extract emails from a single webpage with anti-detection measures
        """
        emails = set()
        
        # Add referrer header to appear more natural
        original_referer = self.session.headers.get('Referer')
        parsed_url = urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        self.session.headers['Referer'] = base_url
        
        try:
            # Try multiple methods to get content
            methods = [
                {'use_session': True, 'timeout': 10},
                {'use_session': True, 'timeout': 15},
                {'use_trafilatura': True}
            ]
            
            for method in methods:
                if emails:  # If we already found emails, don't try other methods
                    break
                    
                try:
                    if method.get('use_session'):
                        response = self.session.get(url, timeout=method['timeout'], allow_redirects=True)
                        if response.status_code == 200:
                            # Extract emails from raw HTML
                            html_emails = self.email_pattern.findall(response.text)
                            emails.update(html_emails)
                            
                            # Use trafilatura for clean text extraction
                            text_content = trafilatura.extract(response.text)
                            if text_content:
                                found_emails = self.email_pattern.findall(text_content)
                                emails.update(found_emails)
                        elif response.status_code == 403:
                            # If we get 403, try different user agent
                            old_ua = self.session.headers['User-Agent']
                            self.session.headers['User-Agent'] = random.choice(self.user_agents)
                            time.sleep(random.uniform(1, 3))
                            continue
                    
                    elif method.get('use_trafilatura'):
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
                    
                except Exception:
                    continue
                    
        except Exception:
            pass
        finally:
            # Restore original referer
            if original_referer:
                self.session.headers['Referer'] = original_referer
        
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