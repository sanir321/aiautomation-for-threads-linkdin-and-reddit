import database
from datetime import datetime
from platforms import reddit_client, linkedin_client, threads_client

def collect_daily_trends():
    """Collects trends from all active platforms and updates the DB."""
    
    # Empty old trends logic can be added here
    # database.get_db_connection().execute("DELETE FROM trends_cache"); ...
    
    platforms_with_scrapers = {
        'reddit': reddit_client.scrape_trends,
        'linkedin': linkedin_client.scrape_trends,
        'threads': threads_client.scrape_trends
    }
    
    total_trends_found = 0
    
    for platform, scraper_func in platforms_with_scrapers.items():
        account = database.get_account(platform)
        if account and account['status'] == 'active':
            print(f"Scraping {platform} for trends...")
            try:
                trends = scraper_func()
                
                # Save to DB
                conn = database.get_db_connection()
                for trend in trends:
                    conn.execute('''
                        INSERT INTO trends_cache (platform, trending_topic, scraped_at) 
                        VALUES (?, ?, ?)
                    ''', (platform, str(trend), datetime.now()))
                conn.commit()
                conn.close()
                total_trends_found += len(trends)
            except Exception as e:
                print(f"Error executing scraper for {platform} - {e}")
                
    return total_trends_found

def get_recent_trends():
    """Retrieve the most recently scraped trends as a flat list."""
    conn = database.get_db_connection()
    # Get last 10 trends across platforms
    rows = conn.execute('SELECT trending_topic FROM trends_cache ORDER BY scraped_at DESC LIMIT 10').fetchall()
    conn.close()
    
    return [row['trending_topic'] for row in rows]
