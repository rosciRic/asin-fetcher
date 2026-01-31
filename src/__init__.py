#!/usr/bin/env python
# vim:fileencoding=UTF-8

from __future__ import (unicode_literals, division, absolute_import, print_function)
from calibre.ebooks.metadata.sources.base import Source
from calibre.ebooks.metadata import MetaInformation
import urllib.parse
import time
import random
import re

class AmazonASINFetcher(Source):
    name = 'Amazon ASIN Fetcher'
    description = 'Multi-Store ASIN Fetcher (IT/COM/UK/DE/FR/ES) with smart validation'
    supported_platforms = ['windows', 'osx', 'linux']
    author = 'Community'
    version = (2, 0, 1)
    minimum_calibre_version = (5, 0, 0)
    
    capabilities = frozenset(['identify'])
    touched_fields = frozenset(['identifier:amazon', 'title', 'authors'])
    
    # Store configuration
    STORES = [
        'amazon.it', 'amazon.com', 'amazon.co.uk',
        'amazon.de', 'amazon.fr', 'amazon.es'
    ]
    
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
    ]

    def get_book_url(self, identifiers):
        asin = identifiers.get('amazon', None)
        return ('amazon', asin, f'https://www.amazon.it/dp/{asin}') if asin else None

    def _clean_query(self, title, authors):
        """Build and clean search query"""
        author_str = " ".join(authors) if authors else ""
        query = f"{title} {author_str} ebook"
        query = re.sub(r'[^\w\s]', ' ', query)
        return re.sub(r'\s+', ' ', query).strip()

    def _validate_asin(self, asin):
        """Validate ASIN format: B0 + 8 alphanumeric chars"""
        return bool(asin and re.match(r'^B0[A-Z0-9]{8}$', asin))

    def _extract_asin(self, html, url):
        """Extract ASIN using multiple methods"""
        # Method 1: JSON field
        match = re.search(r'asin["\s:]+([A-Z0-9]{10})', html, re.I)
        if match and self._validate_asin(match.group(1)):
            return match.group(1)
        
        # Method 2: data-asin attribute
        match = re.search(r'data-asin=["\']([A-Z0-9]{10})["\']', html, re.I)
        if match and self._validate_asin(match.group(1)):
            return match.group(1)
        
        # Method 3: URL pattern
        match = re.search(r'/(?:dp|gp/product)/(B0[A-Z0-9]{8})', url)
        if match and self._validate_asin(match.group(1)):
            return match.group(1)
        
        return None

    def _verify_relevance(self, title, authors, html):
        """Quick relevance check (0-100 score)"""
        html_lower = html.lower()
        title_lower = title.lower()
        
        # Title check (weight 70)
        title_words = [w for w in title_lower.split() if len(w) > 3]
        title_matches = sum(1 for w in title_words if w in html_lower)
        title_score = (title_matches / len(title_words) * 70) if title_words else 0
        
        # Author check (weight 30)
        author_score = 0
        if authors:
            author_words = [w for w in authors[0].lower().split() if len(w) > 2]
            author_matches = sum(1 for w in author_words if w in html_lower)
            author_score = (author_matches / len(author_words) * 30) if author_words else 0
        
        return int(title_score + author_score)

    def _search_store(self, domain, query, title, authors, br, timeout, log):
        """Search single Amazon store with retry"""
        log.info(f'Searching {domain}...')
        
        url = f"https://www.{domain}/s?k={urllib.parse.quote(query)}&i=digital-text"
        
        for attempt in range(2):  # 2 attempts
            try:
                # Set headers
                br.addheaders = [
                    ('User-Agent', random.choice(self.USER_AGENTS)),
                    ('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'),
                    ('Accept-Language', 'it-IT,it;q=0.9,en;q=0.8'),
                    ('Referer', 'https://www.google.com/')
                ]
                
                time.sleep(random.uniform(1.5, 3.0))
                
                # Search page
                response = br.open_novisit(url, timeout=timeout)
                html = response.read().decode('utf-8', errors='ignore')
                
                # Parse results
                from calibre.ebooks.BeautifulSoup import BeautifulSoup
                soup = BeautifulSoup(html, 'html.parser')
                
                # Find first result
                result = soup.find('div', attrs={'data-component-type': 's-search-result'})
                if not result:
                    result = soup.find('a', href=re.compile(r'/dp/B0[A-Z0-9]{8}'))
                
                if not result:
                    log.warning(f'No results on {domain}')
                    if attempt == 0:
                        time.sleep(random.uniform(2, 4))
                        continue
                    return None
                
                # Get detail URL
                link = result if result.name == 'a' else result.find('a', href=True)
                if not link:
                    return None
                    
                detail_url = link['href']
                if not detail_url.startswith('http'):
                    detail_url = f"https://www.{domain}{detail_url}"
                
                log.info(f'Found result, checking...')
                time.sleep(random.uniform(1.5, 2.5))
                
                # Get detail page
                response = br.open_novisit(detail_url, timeout=timeout)
                detail_html = response.read().decode('utf-8', errors='ignore')
                
                # Verify relevance
                score = self._verify_relevance(title, authors, detail_html)
                if score < 25:
                    log.warning(f'Low relevance score: {score}/100')
                    return None
                
                # Extract ASIN
                asin = self._extract_asin(detail_html, detail_url)
                if asin:
                    log.info(f'✓ Found ASIN: {asin} (score: {score}/100)')
                    return asin
                
                log.warning(f'ASIN not found on {domain}')
                return None
                
            except Exception as e:
                log.error(f'Error on {domain} (attempt {attempt + 1}): {str(e)}')
                if attempt == 0:
                    time.sleep(random.uniform(2, 4))
                    continue
                return None
        
        return None

    def identify(self, log, result_queue, abort, title=None, authors=None, identifiers={}, timeout=30):
        """Main identification entry point"""
        if not title:
            return
        
        log.info(f'Amazon ASIN Fetcher v{".".join(map(str, self.version))}')
        log.info(f'Title: {title}')
        log.info(f'Authors: {", ".join(authors) if authors else "N/A"}')
        
        query = self._clean_query(title, authors)
        log.info(f'Query: "{query}"')
        
        br = self.browser
        br.addheaders = []
        
        # Search stores
        for domain in self.STORES:
            if abort.is_set():
                return
            
            asin = self._search_store(domain, query, title, authors, br, timeout, log)
            
            if asin:
                log.info(f'SUCCESS! ASIN: {asin} from {domain}')
                mi = MetaInformation(title, authors)
                mi.identifiers = {'asin': asin}
                result_queue.put(mi)
                return
        
        log.error('No ASIN found on any store')

    def download_cover(self, log, result_queue, abort, title=None, authors=None, identifiers={}, timeout=30, get_best_cover=False):
        """Cover download - not implemented"""
        pass