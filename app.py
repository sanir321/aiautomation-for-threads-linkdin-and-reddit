import os
import fitz  # PyMuPDF
from flask import Flask, render_template, request, redirect, url_for, flash
from config import Config
import database
import scheduler

from platforms.browser_engine import BrowserEngine

app = Flask(__name__)
app.config['SECRET_KEY'] = Config.SECRET_KEY
app.config['UPLOAD_FOLDER'] = Config.UPLOADS_DIR

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Start background scheduler
scheduler.start_scheduler()

# Initialize Browser Engine
browser_engine = BrowserEngine()

@app.route('/')
def index():
    config = database.get_config()
    accounts = {
        'reddit': database.get_account('reddit'),
        'linkedin': database.get_account('linkedin'),
        'threads': database.get_account('threads'),
    }
    analytics = database.get_analytics_summary()
    recent_posts = database.get_recent_posts(10)
    trends = database.get_posting_trends(7)
    
    return render_template('index.html', 
                         config=config, 
                         accounts=accounts, 
                         analytics=analytics, 
                         recent_posts=recent_posts,
                         trends_json=trends)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        kilo_api_key = request.form.get('kilo_api_key')
        system_prompt = request.form.get('system_prompt')
        posting_time = request.form.get('posting_time')
        jitter_minutes = request.form.get('jitter_minutes', type=int)
        model_name = request.form.get('model_name')
        
        linkedin_rule = request.form.get('linkedin_rule')
        reddit_rule = request.form.get('reddit_rule')
        threads_rule = request.form.get('threads_rule')
        
        # Don't overwrite key if empty and already set
        if not kilo_api_key:
            kilo_api_key = None
            
        database.update_config(
            kilo_api_key=kilo_api_key, 
            system_prompt=system_prompt, 
            posting_time=posting_time, 
            jitter_minutes=jitter_minutes,
            model_name=model_name,
            linkedin_rule=linkedin_rule,
            reddit_rule=reddit_rule,
            threads_rule=threads_rule
        )
        scheduler.update_schedule_time(posting_time)
        flash('Settings updated successfully!', 'success')
        return redirect(url_for('settings'))
        
    config = database.get_config()
    return render_template('settings.html', config=config)

# --- New Connection Routes ---

@app.route('/connect/<platform>', methods=['GET'])
def connect_platform(platform):
    # This now just renders the form to paste cookies
    valid_platforms = ['reddit', 'linkedin', 'threads']
    if platform not in valid_platforms:
        flash(f'Unsupported platform: {platform}', 'error')
        return redirect(url_for('accounts'))
        
    return render_template('connect_cookies.html', platform=platform)

@app.route('/save_cookies/<platform>', methods=['POST'])
def save_cookies(platform):
    cookie_json = request.form.get('cookie_json')
    if not cookie_json:
        flash('No cookie JSON provided.', 'error')
        return redirect(url_for('connect_platform', platform=platform))
        
    try:
        # Validate format (JSON or Netscape)
        is_valid = browser_engine._normalize_storage_state(cookie_json)
        if not is_valid:
            flash('Invalid cookie format. Please provide valid JSON or a Netscape/Curl text file.', 'error')
            return redirect(url_for('connect_platform', platform=platform))
        
        # Save to database
        # We store it as a dict with session_state key to match our engine's expectations
        creds = {'session_state': cookie_json}
        database.update_account(platform, creds, status="active")
        
        flash(f'Successfully connected {platform.capitalize()} via Session JSON!', 'success')
        return redirect(url_for('accounts'))
    except Exception as e:
        flash(f'Error saving cookies: {str(e)}', 'error')
        return redirect(url_for('connect_platform', platform=platform))

@app.route('/accounts')
def accounts():
    accounts_data = {
        'reddit': database.get_account('reddit'),
        'linkedin': database.get_account('linkedin'),
        'threads': database.get_account('threads'),
    }
    return render_template('accounts.html', accounts=accounts_data)

@app.route('/knowledge', methods=['GET', 'POST'])
def knowledge():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part', 'error')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(request.url)
            
        if file:
            filename = file.filename
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Extract text
            content = ""
            try:
                if filename.endswith('.pdf'):
                    doc = fitz.open(filepath)
                    for page in doc:
                        content += page.get_text()
                else:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                database.add_knowledge(filename, content)
                flash(f'File {filename} parsed and added to Knowledge Base.', 'success')
            except Exception as e:
                flash(f'Error processing file: {str(e)}', 'error')
                
            # Optional: Remove file after parsing
            if os.path.exists(filepath):
                os.remove(filepath)
                
            return redirect(url_for('knowledge'))
            
    kb_entries = database.get_all_knowledge()
    return render_template('knowledge.html', entries=kb_entries)

if __name__ == '__main__':
    # Disable reloader because Playwright's internal file accesses
    # can trigger the watchdog and cause infinite restarts.
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True, use_reloader=False)
