import database
from platforms.browser_engine import BrowserEngine
import time

def scrape_trends():
    """Simplified trend scraping for LinkedIn."""
    return ["AI in B2B SaaS", "Remote work productivity"] # Mock trends for now

def post(content: str):
    """Posts a text update to LinkedIn using browser automation."""
    engine = BrowserEngine()
    
    def post_logic(page):
        # Navigate to the feed
        print("🚀 Navigating to LinkedIn feed (60s timeout)...")
        # Increase timeout for heavy LinkedIn loading
        page.goto("https://www.linkedin.com/feed/", timeout=60000)
        
        # Wait for dynamic UI
        page.wait_for_load_state("domcontentloaded")
        time.sleep(10) # LinkedIn is heavy on dynamic assets
        
        # Check if logged in
        if "login" in page.url.lower() or page.locator('a[href*="login"]').first.is_visible():
            return False, "Not logged in to LinkedIn. Please update your session cookies."

        try:
            print("🔍 Searching for post composer...")
            
            # Step 1: Click the trigger to start a post
            # Using ARIA labels for stability (LinkedIn's current most robust method)
            trigger_selectors = [
                'button[aria-label="Start a post"]',
                '.share-box-feed-entry__trigger',
                'div.share-box-feed-entry__trigger',
                'button.artdeco-button--muted:has-text("Start a post")',
                'button:has-text("Start a post")'
            ]
            
            trigger = None
            for selector in trigger_selectors:
                try:
                    t = page.wait_for_selector(selector, state="visible", timeout=3000)
                    if t:
                        trigger = t
                        break
                except:
                    continue
            
            if trigger:
                print("🖱️ Clicking 'Start a post' trigger...")
                trigger.click()
            else:
                # Fallback: Just look for any element with the text and click it
                print("⚠️ Direct selectors failed, trying text-based fallback...")
                try:
                    page.click('text="Start a post"', timeout=5000)
                except:
                    return False, "Could not find or open the LinkedIn post composer."
            
            # Step 2: Fill the textbox
            # Wait for modal and editor
            try:
                editor_selector = 'div[role="textbox"][aria-label="Text editor for creating content"], .ql-editor, div[contenteditable="true"]'
                page.wait_for_selector(editor_selector, state="visible", timeout=12000)
                editor = page.locator(editor_selector).first
                
                print("🖋️ Filling content...")
                editor.click()
                time.sleep(2)
                # Clear existing if any (though usually empty)
                page.keyboard.press("Control+A")
                page.keyboard.press("Backspace")
                page.keyboard.type(content)
                time.sleep(3)
                
                # Step 3: Click 'Post' button
                post_btn_selectors = [
                    'button[aria-label="Post"]',
                    'button.share-actions__post-button',
                    'button:has-text("Post")',
                    '.share-actions__primary-action'
                ]
                
                post_btn = None
                for selector in post_btn_selectors:
                    try:
                        btn = page.locator(selector).filter(has_not=page.locator('svg')).last
                        if btn.is_visible():
                            post_btn = btn
                            break
                    except:
                        continue
                
                if post_btn:
                    print("📤 Clicking 'Post'...")
                    post_btn.click()
                    time.sleep(10) # Wait for post to complete and feedback UI
                    return True, "Posted to LinkedIn successfully."
                else:
                    return False, "Found composer but could not find the 'Post' button."
            except Exception as e:
                return False, f"Could not find or interact with the LinkedIn editor: {str(e)}"
                
        except Exception as e:
            return False, f"LinkedIn posting error: {str(e)}"

    return engine.perform_post('linkedin', 'https://www.linkedin.com/feed/', post_logic)
