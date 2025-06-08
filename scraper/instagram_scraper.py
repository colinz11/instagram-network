import os
import time
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

    def scroll_to_load_all(self, dialog):
        print("Scrolling to load all items...")
        last_height = 0
        retries = 0
        max_retries = 3
        all_usernames = set()  # Keep track of all usernames found

        # First, quickly scroll to the bottom
        print("Fast scrolling to bottom...")
        scrollable = dialog.find_element(
            By.CSS_SELECTOR,
            ".xyi19xy.x1ccrb07.xtf3nb5.x1pc53ja.x1lliihq.x1iyjqo2.xs83m0k.xz65tgg.x1rife3k.x1n2onr6"
        )
        
        while True:
            try:
                # Extract usernames from current view and update the set
                new_usernames = self.extract_usernames(dialog)
                all_usernames.update(new_usernames)

                # Get current scroll height
                current_height = self.driver.execute_script("return arguments[0].scrollHeight", scrollable)
                
                if current_height == last_height:
                    retries += 1
                    if retries >= max_retries:
                        print("Reached the bottom")
                        break
                else:
                    retries = 0
                
                # Scroll directly to the bottom
                self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scrollable)
                
                # Store last height
                last_height = current_height
                
                # Quick pause to let content load
                time.sleep(0.5)
                
            except Exception as e:
                print(f"Error while scrolling: {str(e)}")
                break
        
        print(f"Total unique usernames found: {len(all_usernames)}")
        return list(all_usernames)  # Convert set back to list to maintain compatibility

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

    def get_follower_count(self, target_username: str) -> int:
        """Get the follower count for a user"""
        try:
            self.driver.get(f'{self.base_url}/{target_username}/')
            time.sleep(0.5)
            
            # Find the followers count from the meta section
            meta_section = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "ul.x78zum5.x1q0g3np.xieb3on"))
            )
            count_items = meta_section.find_elements(By.CSS_SELECTOR, "span.html-span")
            if len(count_items) >= 2:  # First item is posts, second is followers
                return self.convert_count_to_number(count_items[1].text)
            return 0
        except Exception as e:
            print(f"Error getting follower count for {target_username}: {str(e)}")
            return 0

    def get_following_count(self, target_username: str) -> int:
        """Get the following count for a user"""
        try:
            self.driver.get(f'{self.base_url}/{target_username}/')
            time.sleep(0.5)
            
            # Find the following count from the meta section
            meta_section = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "ul.x78zum5.x1q0g3np.xieb3on"))
            )
            count_items = meta_section.find_elements(By.CSS_SELECTOR, "span.html-span")
            if len(count_items) >= 3:  # First is posts, second is followers, third is following
                return self.convert_count_to_number(count_items[2].text)
            return 0
        except Exception as e:
            print(f"Error getting following count for {target_username}: {str(e)}")
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
            follower_count = self.get_follower_count(target_username)
            following_count = self.get_following_count(target_username)
            
            # Check if user is a celebrity
            if follower_count > self.celebrity_threshold:
                print(f"User {target_username} is a celebrity ({follower_count} followers), saving counts only...")
                self.celebrity_users.add(target_username)
                followers = []
                following = []
            else:
                # Get followers and following for non-celebrity users
                followers = self.get_followers(target_username)
                time.sleep(0.5)  # Delay between requests
                following = self.get_following(target_username)
            
            # Save data for this user
            self.save_user_data(target_username, set(followers), set(following), follower_count, following_count, profile_name)
            
            return followers, following, True
            
        except Exception as e:
            print(f"Error processing user {target_username}: {str(e)}")
            return [], [], False

    def get_followers(self, target_username: str) -> List[str]:
        try:
            print(f"Getting followers for {target_username}...")
            self.driver.get(f'{self.base_url}/{target_username}/')
            time.sleep(0.5)

            followers_link = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/followers')]"))
            )
            followers_count = followers_link.text
            print(f"Found {followers_count}")
            followers_link.click()
            time.sleep(0.5)

            followers_dialog = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='dialog']"))
            )
            
            time.sleep(0.5)
            follower_usernames = self.scroll_to_load_all(followers_dialog)

            print(f"Found {len(follower_usernames)} followers")
            
            webdriver.ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
            time.sleep(0.5)
            
            return follower_usernames

        except Exception as e:
            print(f"Error getting followers: {str(e)}")
            return []

    def get_following(self, target_username: str) -> List[str]:
        try:
            print(f"Getting following for {target_username}...")
            self.driver.get(f'{self.base_url}/{target_username}/')
            time.sleep(0.5)

            following_link = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/following')]"))
            )
            following_count = following_link.text
            print(f"Found {following_count}")
            following_link.click()
            time.sleep(0.5)

            following_dialog = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='dialog']"))
            )
            
            time.sleep(0.5)
            following_usernames = self.scroll_to_load_all(following_dialog)

            print(f"Found {len(following_usernames)} following")
            
            webdriver.ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
            time.sleep(0.5)
            
            return following_usernames

        except Exception as e:
            print(f"Error getting following: {str(e)}")
            return []

    def save_user_data(self, username: str, followers: set, following: set, followers_count: int, following_count: int, profile_name: str = ""):
        """Save user data to JSON file"""
        # Convert sets to lists for JSON serialization
        user_data = {
            'followers_count': followers_count,
            'following_count': following_count,
            'is_celebrity': len(followers) > self.celebrity_threshold,
            'followers': list(followers),
            'following': list(following),
            'profile_name': profile_name
        }
        
        # Load existing data if file exists
        try:
            with open('data/user_data.json', 'r') as f:
                all_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            all_data = {}
        
        # Update data for current user
        all_data[username] = user_data
        
        # Save updated data
        os.makedirs('public', exist_ok=True)
        with open('public/user_data.json', 'w') as f:
            json.dump(all_data, f, indent=2)
        
        print(f"Saved data for {username} to user_data.json")

    def run(self, skip_main_user: bool = False):
        try:
            self.login()
            
            if not skip_main_user:
                # Process main user first
                main_followers, main_following = self.process_user(self.username)
            else:
                # Read from user_data 
                with open('public/user_data.json', 'r') as f:
                    user_data = json.load(f)
                main_followers = user_data[self.username]['followers']
                main_following = user_data[self.username]['following']
                
            # Combine followers and following lists
            users_to_process = set(main_followers + main_following)
            print(f"\nFound {len(users_to_process)} users to process")
            
            # Process each user's network
            for i, username in enumerate(users_to_process, 1):
                try:
                    print(f"\nProcessing user {i}/{len(users_to_process)}: {username}")
                    self.process_user(username)
                    time.sleep(1)  # Increased delay between users
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
    scraper.run(True) 