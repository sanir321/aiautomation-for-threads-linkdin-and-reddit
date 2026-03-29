import database
from platforms.browser_engine import BrowserEngine
import time

def scrape_trends(subreddits=['Entrepreneur', 'SaaS', 'SideProject'], limit=5):
    """Simplified trend scraping for Reddit."""
    return ["AI Automation in 2024 (r/SaaS)", "Building a micro-SaaS in a weekend (r/SideProject)"]

def post(content: str, target_subreddit: str):
    """Posts content to a specific subreddit using browser automation."""
    engine = BrowserEngine()
    
    def post_logic(page):
        # Navigate to the submit page
        url = f"https://www.reddit.com/r/{target_subreddit}/submit"
        print(f"🚀 Navigating to {url}...")
        page.goto(url)
        
        # Wait for dynamic UI
        page.wait_for_load_state("domcontentloaded")
        time.sleep(10) # Reddit is heavy
        
        # Check if we are logged in
        if "login" in page.url.lower():
            return False, "Not logged in to Reddit. Please update your session cookies."

        try:
            lines = content.strip().split('\n')
            title_text = lines[0][:300] if lines else "Update from AI Agent"
            body_text = '\n'.join(lines[1:]) if len(lines) > 1 else ""
            
            print(f"📝 Preparing post: '{title_text[:50]}...'")

            # Title input
            # Reddit's new 'faceplate' components are tricky for .fill()
            # We'll click and type instead.
            title_input = page.locator('textarea[placeholder="Title"], [name="title"], faceplate-textarea-input').first
            if title_input.is_visible():
                print("⌨️ Typing title...")
                title_input.click()
                time.sleep(1)
                page.keyboard.type(title_text)
            else:
                return False, "Could not find the Title input field."

            # Body input (Draft.js)
            # Find the editor div
            editor = page.locator('div[role="textbox"], [aria-label="Text (optional)"], .public-DraftEditor-content, faceplate-batch-input').first
            if editor.is_visible():
                print("⌨️ Typing body...")
                editor.click()
                time.sleep(1)
                page.keyboard.type(body_text)
            else:
                print("⚠️ Body editor not found, attempting fallback Tab-type...")
                page.keyboard.press("Tab")
                time.sleep(0.5)
                page.keyboard.type(body_text)

            time.sleep(2)
            
            # Submit button
            # Look for ANY button that says Post
            post_button = page.locator('button:has-text("Post"), shreddit-post-button').filter(has_not=page.locator('svg')).last
            
            if not post_button.is_visible():
                post_button = page.locator('button[type="submit"]').first

            if post_button.is_visible():
                print("📤 Clicking 'Post'...")
                # Force click if it's a web component
                post_button.click(force=True)
                
                # Wait for redirect to the post
                print("⏳ Waiting for post confirmation...")
                time.sleep(5)
                if "submit" not in page.url:
                    return True, f"Successfully posted to r/{target_subreddit}: {page.url}"
                
                # Check for error messages on page
                error_msg = page.locator('[role="alert"], .error-message').first
                if error_msg.is_visible():
                    return False, f"Reddit UI Error: {error_msg.inner_text()}"
                    
                return True, f"Post triggered, current URL: {page.url}"
            else:
                return False, "Could not find the 'Post' button."
                
        except Exception as e:
            return False, f"Reddit posting error: {str(e)}"

    return engine.perform_post('reddit', f"https://www.reddit.com/r/{target_subreddit}/submit", post_logic)
