import os
import json
import time
import re
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
import database

class BrowserEngine:
    def __init__(self):
        self.playwright = None
        self.browser = None

    def _parse_netscape_cookies(self, text):
        """
        Parses Netscape / Curl cookie file format into Playwright cookies.
        Each line is: domain  flag  path  secure  expiration  name  value
        """
        cookies = []
        lines = text.splitlines()
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            parts = line.split('\t')
            if len(parts) < 7:
                # Try space-separated if tabs fail (fallback)
                parts = re.split(r'\s+', line)
                if len(parts) < 7:
                    continue
            
            domain = parts[0].strip()
            # Normalize LinkedIn domains to prevent Playwright injection failures
            if 'linkedin.com' in domain:
                domain = '.linkedin.com'
                
            path = parts[2].strip()
            secure = parts[3].strip().upper() == 'TRUE'
            try:
                expires = float(parts[4].strip())
            except ValueError:
                expires = -1
                
            name = parts[5].strip()
            value = parts[6].strip()
            
            cookie = {
                "name": name,
                "value": value,
                "domain": domain,
                "path": path,
                "expires": expires,
                "secure": secure,
                "httpOnly": False,
                "sameSite": "None"
            }
            cookies.append(cookie)
            
        return cookies

    def _normalize_storage_state(self, raw_input):
        """
        Takes a raw input (Playwright JSON, List JSON, or Netscape Text)
        and returns a standard Playwright storage_state dictionary.
        """
        if not raw_input:
            return None
            
        # 1. Try JSON formats
        try:
            raw_json = json.loads(raw_input) if isinstance(raw_input, str) else raw_input
            
            # If it's already in Playwright format
            if isinstance(raw_json, dict) and 'cookies' in raw_json:
                return raw_json
                
            # If it's a simple list of cookies (e.g. from Cookie-Editor extension)
            if isinstance(raw_json, list):
                return {
                    "cookies": raw_json,
                    "origins": []
                }
        except (json.JSONDecodeError, TypeError):
            pass
            
        # 2. Try Netscape / Curl text format
        if isinstance(raw_input, str) and ("# Netscape" in raw_input or "\t" in raw_input):
            netscape_cookies = self._parse_netscape_cookies(raw_input)
            if netscape_cookies:
                return {
                    "cookies": netscape_cookies,
                    "origins": []
                }
                
        return None

    def get_page(self, platform, p, headless=True):
        """Helper to get a page with correctly loaded session state from the database."""
        # Launch browser
        browser = p.chromium.launch(headless=headless)
        
        # Load account session from DB
        account = database.get_account(platform)
        storage_state = None
        if account and 'credentials' in account:
            raw_state = account['credentials'].get('session_state')
            if raw_state:
                storage_state = self._normalize_storage_state(raw_state)
            
        # Create context with storage state if available and fixed desktop viewport
        context_args = {
            "viewport": {'width': 1280, 'height': 800},
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }
        if storage_state:
            context_args["storage_state"] = storage_state
            
        context = browser.new_context(**context_args)
            
        page = context.new_page()
        stealth_sync(page) # Apply stealth to avoid detection
        return browser, context, page

    def perform_post(self, platform, post_url, post_logic_fn):
        """Higher level wrapper to perform a post using platform-specific logic."""
        with sync_playwright() as p:
            try:
                browser, context, page = self.get_page(platform, p, headless=True)
            except Exception as e:
                return False, f"Failed to open browser: {str(e)}"
                
            try:
                page.goto(post_url, wait_until="domcontentloaded", timeout=60000)
                result, msg = post_logic_fn(page)
                return result, msg
            except Exception as e:
                return False, f"Browser error: {str(e)}"
            finally:
                browser.close()
