import os
import time
import random
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from dotenv import load_dotenv
from typing import Dict, List, Set, Tuple
import json
from datetime import datetime, timedelta

class InstagramScraper:
    def __init__(self):
        load_dotenv()
        self.username = os.getenv('INSTAGRAM_USERNAME')
        self.password = os.getenv('INSTAGRAM_PASSWORD')
        self.base_url = 'https://www.instagram.com'
        self.celebrity_threshold = 3000
        self.setup_driver()
        self.processed_users: Set[str] = set()
        self.celebrity_users: Set[str] = set()
        self.user_data: Dict[str, dict] = {}
        
        # Rate limiting parameters
        self.requests_per_hour = 150  # Maximum requests per hour
        self.min_delay = 2  # Minimum delay between requests in seconds
        self.max_delay = 4  # Maximum delay between requests in seconds
        self.batch_size = 25  # Number of users to process before taking a longer break
        self.batch_break_min = 300  # Minimum break time between batches in seconds (5 minutes)
        self.batch_break_max = 600  # Maximum break time between batches in seconds (10 minutes)
        
        # Request tracking
        self.request_timestamps = []

    def setup_driver(self):
        chrome_options = Options()
        # chrome_options.add_argument('--headless')  # Uncomment to run headless
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)

    def login(self):
        try:
            print("Logging in...")
            self.driver.get(self.base_url)
            time.sleep(2)  # Wait for page to load completely

            # Try to find the username input field with different selectors
            username_input = None
            for selector in ['input[name="username"]', 'input[aria-label="Phone number, username, or email"]']:
                try:
                    username_input = self.wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if username_input:
                        break
                except:
                    continue

            if not username_input:
                raise Exception("Could not find username input field")

            # Try to find the password input field with different selectors
            password_input = None
            for selector in ['input[name="password"]', 'input[aria-label="Password"]']:
                try:
                    password_input = self.wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if password_input:
                        break
                except:
                    continue

            if not password_input:
                raise Exception("Could not find password input field")

            # Enter credentials
            username_input.clear()
            username_input.send_keys(self.username)
            time.sleep(1)
            password_input.clear()
            password_input.send_keys(self.password)
            time.sleep(1)

            # Try to find the login button with different selectors
            login_button = None
            for selector in [
                'button[type="submit"]',
                'button:contains("Log in")',
                'button:contains("Sign in")'
            ]:
                try:
                    login_button = self.wait.until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    if login_button:
                        break
                except:
                    continue

            if not login_button:
                raise Exception("Could not find login button")

            # Click login
            login_button.click()
            time.sleep(5)


            print("Login successful")

        except Exception as e:
            print(f"Login failed: {str(e)}")
            raise

    def random_delay(self, min_delay: float = None, max_delay: float = None):
        """Add a random delay between operations to appear more human-like"""
        min_d = min_delay if min_delay is not None else self.min_delay
        max_d = max_delay if max_delay is not None else self.max_delay
        delay = random.uniform(min_d, max_d)
        time.sleep(delay)
        
    def check_rate_limit(self):
        """Check if we're approaching rate limits and wait if necessary"""
        now = datetime.now()
        hour_ago = now - timedelta(hours=1)
        
        # Remove timestamps older than 1 hour
        self.request_timestamps = [ts for ts in self.request_timestamps if ts > hour_ago]
        
        # If we're approaching the limit, wait until we have capacity
        while len(self.request_timestamps) >= self.requests_per_hour:
            sleep_time = (self.request_timestamps[0] + timedelta(hours=1) - now).total_seconds()
            if sleep_time > 0:
                print(f"Approaching rate limit. Waiting {sleep_time:.0f} seconds...")
                time.sleep(sleep_time)
            now = datetime.now()
            hour_ago = now - timedelta(hours=1)
            self.request_timestamps = [ts for ts in self.request_timestamps if ts > hour_ago]
        
        # Add current request timestamp
        self.request_timestamps.append(now)

    def scroll_to_load_all(self, dialog) -> List[str]:
        """Scroll through the followers/following dialog and extract all usernames"""
        try:
            usernames = set()
            last_height = 0
            scroll_attempts = 0
            max_scroll_attempts = 3  # Stop scrolling if no new content after 3 attempts
            
            while scroll_attempts < max_scroll_attempts:
                # Extract usernames from current view
                elements = dialog.find_elements(By.CSS_SELECTOR, "a.x1i10hfl")
                new_usernames = {elem.text for elem in elements if elem.text}
                usernames.update(new_usernames)
                
                # Scroll down
                dialog.send_keys(Keys.END)
                self.random_delay(1, 2)  # Shorter delay for scrolling
                
                # Check if we've reached the bottom
                new_height = dialog.get_attribute("scrollHeight")
                if new_height == last_height:
                    scroll_attempts += 1
                else:
                    scroll_attempts = 0
                last_height = new_height
                
                # Add some randomness to the scrolling
                if random.random() < 0.2:  # 20% chance to scroll up a bit
                    dialog.send_keys(Keys.PAGE_UP)
                    self.random_delay(0.5, 1)
                    dialog.send_keys(Keys.PAGE_DOWN)
                    self.random_delay(0.5, 1)
            
            return list(usernames)
                
        except Exception as e:
            print(f"Error while scrolling: {str(e)}")
            return list(usernames)  # Return what we've collected so far

    def extract_usernames(self, dialog) -> List[str]:
        try:
            all_usernames = set()
            links = dialog.find_elements(By.CSS_SELECTOR, "a[role='link']")
            for link in links:
                try:
                    href = link.get_attribute('href')
                    if href and 'instagram.com' in href:
                        username = href.split('instagram.com/')[-1].strip('/')
                        if self.is_valid_username(username):
                            all_usernames.add(username)
                except:
                    continue
            print(f"Found {len(all_usernames)} unique usernames so far...")
            return list(all_usernames)
        except Exception as e:
            print(f"Error extracting usernames: {str(e)}")
            return []
    
    def is_valid_username(self, text):
        """Helper function to validate usernames"""
        if not text:
            return False
            
        # Skip common non-username texts
        if text.startswith(('Follow', 'Following', 'Remove', '#', '@')):
            return False
            
        # Skip if contains spaces or newlines
        if ' ' in text or '\n' in text:
            return False
            
        # Skip common button texts
        if text.lower() in ['follow', 'following', 'remove', 'verified']:
            return False
            
        # Skip if too long or too short
        if len(text) < 2 or len(text) > 30:
            return False
            
        # Skip if contains invalid characters
        valid_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._')
        if not all(c in valid_chars for c in text):
            return False
            
        # Skip common non-username paths
        if text in ['explore', 'direct', 'p', 'reels', 'stories', 'tags', 'locations']:
            return False
            
        return True

    def convert_count_to_number(self, count_text: str) -> int:
        """Convert Instagram count format (e.g., '61.2k', '1.2M') to number"""
        try:
            # Remove commas and convert to lowercase
            count_text = count_text.replace(',', '').lower().strip()
            
            # Handle 'k' thousands
            if 'k' in count_text:
                number = float(count_text.replace('k', ''))
                return int(number * 1000)
            
            # Handle 'M' millions
            if 'm' in count_text:
                number = float(count_text.replace('m', ''))
                return int(number * 1000000)
            
            # Handle regular numbers
            return int(count_text.split()[0])
        except Exception as e:
            print(f"Error converting count '{count_text}': {str(e)}")
            return 0

    def get_connection_count(self, target_username: str, connection_type: str) -> int:
        """Get either followers or following count for a user.
        Args:
            target_username: The username to get count for
            connection_type: Either 'followers' or 'following'
        Returns:
            Count of connections
        """
        try:
            # Navigate to profile if not already there
            if not self.driver.current_url.endswith(f'/{target_username}/'):
                self.driver.get(f'{self.base_url}/{target_username}/')
                time.sleep(2)

            # Find the count element
            count_link = self.wait.until(
                EC.presence_of_element_located((By.XPATH, f"//a[contains(@href, '/{connection_type}')]"))
            )
            count_text = count_link.text.strip()
            
            # Extract number from text (e.g., "1,234 followers" -> 1234)
            count = int(''.join(filter(str.isdigit, count_text)))
            return count

        except Exception as e:
            print(f"Error getting {connection_type} count for {target_username}: {str(e)}")
            return 0

    def get_profile_name(self, target_username: str) -> str:
        """Get the user's display name from their profile."""
        try:
            # Wait for the profile header to load
            header = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "header section"))
            )
            
            # Try to find the name element
            try:
                name_element = header.find_element(By.CSS_SELECTOR, "span.x1lliihq")
                return name_element.text.strip()
            except:
                return ""  # Return empty string if name not found
                
        except Exception as e:
            print(f"Error getting profile name for {target_username}: {str(e)}")
            return ""

    def get_user_connections(self, target_username: str, connection_type: str) -> List[str]:
        """Get either followers or following list for a user."""
        try:
            print(f"Getting {connection_type} for {target_username}...")
            
            self.check_rate_limit()
            if not self.driver.current_url.endswith(f'/{target_username}/'):
                self.driver.get(f'{self.base_url}/{target_username}/')
            self.random_delay()

            # Click the appropriate link based on connection type
            connection_link = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, f"//a[contains(@href, '/{connection_type}')]"))
            )
            connection_count = connection_link.text
            print(f"Found {connection_count}")
            
            self.check_rate_limit()
            connection_link.click()
            self.random_delay()

            connection_dialog = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='dialog']"))
            )
            
            self.random_delay()
            usernames = self.scroll_to_load_all(connection_dialog)

            print(f"Found {len(usernames)} {connection_type}")
            
            webdriver.ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
            self.random_delay()
            
            return usernames

        except Exception as e:
            print(f"Error getting {connection_type}: {str(e)}")
            return []

    def process_user(self, target_username: str) -> Tuple[List[str], List[str], bool]:
        """Process a single user and return their followers and following lists"""
        print(f"\nProcessing user: {target_username}")
        
        if target_username in self.processed_users:
            print(f"User {target_username} already processed, skipping...")
            return [], [], False
            
        self.processed_users.add(target_username)
        
        try:
            # Navigate to user's profile
            self.driver.get(f'{self.base_url}/{target_username}/')
            time.sleep(0.5)
            
            # Get profile name
            profile_name = self.get_profile_name(target_username)
            
            # Get follower and following counts
            follower_count = self.get_connection_count(target_username, 'followers')
            following_count = self.get_connection_count(target_username, 'following')
            
            # Check if user is a celebrity
            if follower_count > self.celebrity_threshold:
                print(f"User {target_username} is a celebrity ({follower_count} followers), saving counts only...")
                self.celebrity_users.add(target_username)
                followers = []
                following = []
            else:
                # Get followers and following for non-celebrity users
                followers = self.get_user_connections(target_username, 'followers')
                following = self.get_user_connections(target_username, 'following')
            
            # Save data for this user
            self.save_user_data(target_username, set(followers), set(following), follower_count, following_count, profile_name)
            
            return followers, following, True
            
        except Exception as e:
            print(f"Error processing user {target_username}: {str(e)}")
            return [], [], False

    def save_user_data(self, username: str, followers: set, following: set, followers_count: int, following_count: int, profile_name: str = ""):
        """Save user data to JSON file"""
        # Convert sets to lists for JSON serialization
        user_data = {
            'followers_count': followers_count,
            'following_count': following_count,
            'is_celebrity': len(followers) > self.celebrity_threshold,
            'followers': list(followers),
            'following': list(following),
            'profile_name': profile_name,
            'last_updated': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Load existing data if file exists
        try:
            with open('public/user_data.json', 'r') as f:
                all_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            all_data = {}
        
        # Update data for current user
        all_data[username] = user_data
        
        # Save updated data
        os.makedirs('public', exist_ok=True)
        with open('public/user_data.json', 'w') as f:
            json.dump(all_data, f, indent=2)
        
        print(f"Updated data for {username} in user_data.json")

    def run(self, skip_main_user: bool = False):
        try:
            self.login()
            
            if not skip_main_user:
                # Process main user first
                main_followers, main_following, _ = self.process_user(self.username)
            else:
                # Read from user_data 
                with open('public/user_data.json', 'r') as f:
                    user_data = json.load(f)
                main_followers = user_data[self.username]['followers']
                main_following = user_data[self.username]['following']
                
            # Combine followers and following lists
            users_to_process = set(main_followers + main_following)
            print(f"\nFound {len(users_to_process)} users to process")
            
            # Process users in batches
            users_list = list(users_to_process)
            for i in range(0, len(users_list), self.batch_size):
                batch = users_list[i:i + self.batch_size]
                print(f"\nProcessing batch {i//self.batch_size + 1}/{(len(users_list) + self.batch_size - 1)//self.batch_size}")
                
                for j, username in enumerate(batch, 1):
                    try:
                        print(f"\nProcessing user {j}/{len(batch)} in current batch: {username}")
                        self.process_user(username)
                        # Random delay between users
                        if j < len(batch):
                            self.random_delay()
                    except Exception as e:
                        print(f"Error processing user {username}: {str(e)}")
                        # Try to recreate the driver if it crashed
                        try:
                            self.driver.quit()
                        except:
                            pass
                        self.setup_driver()
                        self.login()
                        continue
                
                # Take a longer break between batches
                if i + self.batch_size < len(users_list):
                    break_time = random.uniform(self.batch_break_min, self.batch_break_max)
                    print(f"\nTaking a break for {break_time/60:.1f} minutes...")
                    time.sleep(break_time)
            
            print("\nNetwork data collection completed successfully!")
            
        except Exception as e:
            print(f"Error during network collection: {str(e)}")
        finally:
            try:
                self.driver.quit()
            except:
                pass

if __name__ == "__main__":
    scraper = InstagramScraper()
    scraper.run(False) 