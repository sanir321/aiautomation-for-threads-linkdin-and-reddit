import database
from platforms.browser_engine import BrowserEngine
import time

def scrape_trends():
    """Simplified trend scraping for Threads."""
    return ["AI Threads is booming", "Meta's new platform growth"] # Mock trends for now

def post(content: str):
    """Posts a thread via browser automation."""
    engine = BrowserEngine()
    
    def post_logic(page):
        # Navigate to Threads
        page.goto("https://www.threads.net/")
        
        # Wait for the page to at least start loading
        page.wait_for_load_state("domcontentloaded")
        time.sleep(10) # Give extra time for dynamic JS UI
        
        # Check if logged in
        if "login" in page.url.lower():
            return False, "Not logged in to Threads. Please check your session cookies."

        try:
            print("🔍 Searching for thread composer...")
            
            # Step 1: Find the thread composer. 
            # In the screenshot, we see 'What's new?' text at the top.
            # We can also use the obvious '+' buttons.
            
            # Try finding the top composer directly
            top_composer = page.locator('div:has-text("What\'s new?")').last
            if top_composer.is_visible():
                print("🖱️ Clicking top 'What's new?' composer...")
                top_composer.click()
                time.sleep(2)
            else:
                # Fallback to the '+' button in bottom right
                print("⚠️ Top composer not found. Trying bottom-right '+' button...")
                plus_btn = page.locator('div[role="button"]:has(svg), button:has(svg)').last
                if plus_btn.is_visible():
                    plus_btn.click()
                    time.sleep(2)

            # Step 2: Fill the textbox
            # Threads uses a div with role="textbox"
            editor = page.locator('div[role="textbox"]').first
            if not editor.is_visible():
                print("⚠️ Textbox not visible. Searching for any textbox...")
                editor = page.locator('[contenteditable="true"]').first

            if editor.is_visible():
                print("🖋️ Filling content...")
                editor.focus()
                editor.fill(content)
                time.sleep(2)
                
                # Step 3: Click 'Post'
                # The post button usually becomes enabled after typing
                post_btn = page.locator('div[role="button"]:has-text("Post"), button:has-text("Post")').last
                if post_btn.is_visible():
                    print("📤 Clicking 'Post'...")
                    post_btn.click()
                    time.sleep(5) # Wait for post to complete
                    return True, "Posted to Threads successfully."
                else:
                    return False, "Found composer but could not find the 'Post' button."
            else:
                return False, "Could not find or open the thread composer textbox."
                
        except Exception as e:
            return False, f"Threads posting error: {str(e)}"

    return engine.perform_post('threads', 'https://www.threads.net/', post_logic)
