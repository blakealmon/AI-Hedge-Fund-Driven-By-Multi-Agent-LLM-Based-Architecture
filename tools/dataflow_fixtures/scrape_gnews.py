# scrape_gnews.py
# Script to scrape news by topics using gnews for a date range
# Usage: python scrape_gnews.py YYYY-MM-DD YYYY-MM-DD

import sys
import os
from datetime import datetime, timedelta
from gnews import GNews
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

topics = ['Economy', 'Finance']

def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days) + 1):
        yield start_date + timedelta(n)

def main():
    if len(sys.argv) < 3:
        print('Usage: python scrape_gnews.py YYYY-MM-DD YYYY-MM-DD')
        sys.exit(1)
    start_str, end_str = sys.argv[1], sys.argv[2]
    start_date = datetime.strptime(start_str, '%Y-%m-%d')
    end_date = datetime.strptime(end_str, '%Y-%m-%d')
    out_dir = os.path.join(os.getcwd(), 'gnews_data')
    os.makedirs(out_dir, exist_ok=True)
    gnews = GNews(language="en",
                  max_results=100,
                  period='1d',
                  )
    def scrape_day(topic, day):
        g = GNews(language="en", max_results=100, period='1d')
        g.period = '1d'
        g.end_date = day
        date_str = day.strftime('%Y-%m-%d')
        try:
            results = g.get_news_by_topic(topic.upper())
            for r in results:
                r['scraped_date'] = date_str
            print(f"  {topic} {date_str}: {len(results)} articles")
            return results
        except Exception as e:
            print(f"  {topic} {date_str}: ERROR {e}")
            return []

    for topic in topics:
        print(f"Scraping topic: {topic}")
        all_results = []
        days = list(daterange(start_date, end_date))
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_day = {executor.submit(scrape_day, topic, day): day for day in days}
            for future in as_completed(future_to_day):
                results = future.result()
                all_results.extend(results)
        out_file = os.path.join(out_dir, f"gnews_{topic.lower()}_{start_str}_{end_str}.json")
        with open(out_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        print(f"Saved {len(all_results)} articles for topic '{topic}' to {out_file}")

if __name__ == '__main__':
    main()
