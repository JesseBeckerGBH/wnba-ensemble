import requests
import schedule
import time
import datetime

def search_sota():
    """
    Queries the arXiv API for papers regarding WNBA or basketball betting models
    in combination with Ensemble, Markov, or Bayesian methods.
    Appends the abstracts of found papers to sota_log.txt.
    """
    print(f"[{datetime.datetime.now()}] running SOTA search...")
    
    # arXiv API endpoint
    url = "http://export.arxiv.org/api/query"
    
    # Query string asking for basketball betting ML keywords
    query = 'all:"basketball OR WNBA" AND all:"betting" AND all:"ensemble OR markov OR bayesian"'
    
    params = {
        'search_query': query,
        'start': 0,
        'max_results': 5,
        'sortBy': 'submittedDate',
        'sortOrder': 'descending'
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        # Super simple XML parsing as arXiv returns ATOM feeds
        # In a robust production script, use `feedparser` library
        text = response.text
        
        with open('d:\\WNBA\\scripts\\sota_log.txt', 'a', encoding='utf-8') as f:
            f.write(f"\n--- SOTA Search Results ({datetime.datetime.now().date()}) ---\n")
            
            # Simple hacky extraction for summary text
            entries = text.split('<entry>')
            if len(entries) <= 1:
                f.write("No new papers found.\n")
            else:
                for entry in entries[1:]:
                    title_start = entry.find('<title>') + 7
                    title_end = entry.find('</title>')
                    
                    summary_start = entry.find('<summary>') + 9
                    summary_end = entry.find('</summary>')
                    
                    if title_start > 6 and summary_start > 8:
                        title = entry[title_start:title_end].replace('\\n', ' ').strip()
                        summary = entry[summary_start:summary_end].replace('\\n', ' ').strip()
                        f.write(f"Title: {title}\nAbstract: {summary[:300]}...\n\n")
                f.write("Search complete.\n")
                print("New papers logged to sota_log.txt")
                
    except Exception as e:
        print(f"Error querying arXiv: {e}")

if __name__ == "__main__":
    import sys
    if "--run-once" in sys.argv:
        search_sota()
    else:
        print("Starting SOTA Scanner Schedule (Runs every Monday at 10:00 AM)...")
        schedule.every().monday.at("10:00").do(search_sota)
        
        while True:
            schedule.run_pending()
            time.sleep(3600) # Sleep for an hour
