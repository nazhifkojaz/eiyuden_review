import requests
import time
import urllib.parse
import pandas as pd
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    filename='data/steam_review_collector.log',  # Log file location
    level=logging.INFO,  # Set the logging level
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class SteamReviewCollector:
    def __init__(self, app_id=1658280, delay=1):
        self.app_id = app_id
        self.delay = delay
        self.next_cursor = ""
        self.collected_data = pd.DataFrame()

    def fetch_reviews(self):
        if self.next_cursor == "":
            url = f"https://store.steampowered.com/appreviews/{self.app_id}?filter=recent&language=all&purchase_type=all&num_per_page=100&filter_offtopic_activity=0&json=1"
        else:
            url = f"https://store.steampowered.com/appreviews/{self.app_id}?filter=recent&language=all&purchase_type=all&num_per_page=100&filter_offtopic_activity=0&json=1&cursor={urllib.parse.quote(self.next_cursor)}"
        response = requests.get(url)
        
        if response.status_code == 200:
            return response.json()
        else:
            logging.error(f"Failed to fetch reviews. Status code: {response.status_code}")
            return None

    def process_reviews(self, response):
        review_list = []
        for review in response['reviews']:
            review_dict = {key: review.get(key, None) for key in [
                'recommendationid', 'language', 'review', 'timestamp_created', 'timestamp_updated',
                'voted_up', 'votes_up', 'votes_funny', 'weighted_vote_score', 'comment_count',
                'steam_purchase', 'received_for_free', 'written_during_early_access',
                'hidden_in_steam_china', 'steam_china_location', 
                'author_steamid', 'author_num_games_owned', 'author_num_reviews',
                'author_playtime_forever', 'author_playtime_last_two_weeks',
                'author_playtime_at_review', 'author_last_played'
            ]}
            review_list.append(review_dict)
        return review_list

    def save_to_csv(self):
        filename = f"data/reviews_{datetime.now().strftime('%Y-%m-%d')}.csv"
        self.collected_data.to_csv(filename, index=False)
        logging.info(f"Data saved to {filename}")

    def run(self):
        while True:
            response = self.fetch_reviews()

            if response is None:
                break
            
            if self.next_cursor == response.get('cursor', ''):
                logging.info("No more reviews to collect.")
                break

            review_list = self.process_reviews(response)
            self.collected_data = pd.concat([self.collected_data, pd.DataFrame(review_list)], ignore_index=True)

            self.next_cursor = response['cursor']
            logging.info(f"Number of reviews collected: {len(self.collected_data)}")
            time.sleep(self.delay)  # Delay to avoid API blocking

        if not self.collected_data.empty:
            self.save_to_csv()
        else:
            logging.warning("No data collected, something went wrong.")

# Example usage:
if __name__ == "__main__":
    collector = SteamReviewCollector()
    collector.run()