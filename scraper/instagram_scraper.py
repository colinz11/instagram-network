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

class InstagramScraper:
    def __init__(self):
        load_dotenv()
        self.username = os.getenv('INSTAGRAM_USERNAME')
        self.password = os.getenv('INSTAGRAM_PASSWORD')
        self.base_url = 'https://www.instagram.com'
        self.setup_driver()

    def setup_driver(self):
        chrome_options = Options()
        # chrome_options.add_argument('--headless')  # Uncomment to run headless
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        
        # Use system ChromeDriver
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
        SCROLL_PAUSE_TIME = 0.5
        last_height = 0
        retries = 0
        max_retries = 3

        # First, quickly scroll to the bottom
        print("Fast scrolling to bottom...")
        scrollable = dialog.find_element(
            By.CSS_SELECTOR,
            ".xyi19xy.x1ccrb07.xtf3nb5.x1pc53ja.x1lliihq.x1iyjqo2.xs83m0k.xz65tgg.x1rife3k.x1n2onr6"
        )
        
        while True:
            try:
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
                time.sleep(SCROLL_PAUSE_TIME)
                
            except Exception as e:
                print(f"Error while fast scrolling: {str(e)}")
                break
        
        # Count total items loaded
        username_elements = dialog.find_elements(
            By.CSS_SELECTOR,
            "span.x1lliihq.x193iq5w.x6ikm8r.x10wlt62.xlyipyv.xuxw1ft"
        )
        print(f"Total items loaded: {len(username_elements)}")

    def extract_usernames(self, dialog):
        try:
            print("Extracting usernames...")
            usernames = set()  # Use a set to avoid duplicates
            
            # Method 1: Direct username spans
            username_spans = dialog.find_elements(
                By.CSS_SELECTOR,
                "span.x1lliihq.x193iq5w.x6ikm8r.x10wlt62.xlyipyv.xuxw1ft"
            )
            
            for span in username_spans:
                try:
                    username = span.text.strip()
                    if self.is_valid_username(username):
                        usernames.add(username)
                except Exception as e:
                    print(f"Error extracting from span: {str(e)}")
            
            # Method 2: Profile links
            profile_links = dialog.find_elements(
                By.CSS_SELECTOR,
                "a[role='link'][tabindex='0']"
            )
            
            for link in profile_links:
                try:
                    href = link.get_attribute('href')
                    if href and '/instagram.com/' in href:
                        parts = href.rstrip('/').split('/')
                        if len(parts) > 2:
                            username = parts[-1]
                            if self.is_valid_username(username):
                                usernames.add(username)
                except Exception as e:
                    print(f"Error extracting from link: {str(e)}")
            
            # Method 3: Parent divs with role="button"
            button_divs = dialog.find_elements(
                By.CSS_SELECTOR,
                "div[role='button']"
            )
            
            for div in button_divs:
                try:
                    # Look for spans inside the button div
                    spans = div.find_elements(By.TAG_NAME, "span")
                    for span in spans:
                        username = span.text.strip()
                        if self.is_valid_username(username):
                            usernames.add(username)
                except Exception as e:
                    print(f"Error extracting from button: {str(e)}")
            
            # Method 4: Any text-containing spans that might be usernames
            all_spans = dialog.find_elements(
                By.CSS_SELECTOR,
                "span[dir='auto']"
            )
            
            for span in all_spans:
                try:
                    username = span.text.strip()
                    if self.is_valid_username(username):
                        usernames.add(username)
                except Exception as e:
                    print(f"Error extracting from general span: {str(e)}")
            
            # Convert set back to list
            username_list = list(usernames)
            print(f"Found {len(username_list)} usernames")
            return username_list
            
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

    def get_followers(self):
        try:
            print("Navigating to profile...")
            self.driver.get(f'{self.base_url}/{self.username}/')
            time.sleep(2)

            # Click followers button
            print("Opening followers list...")
            followers_link = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/followers')]"))
            )
            followers_count = followers_link.text
            print(f"Found {followers_count}")
            followers_link.click()
            time.sleep(1)

            # Get followers dialog
            print("Waiting for followers dialog...")
            followers_dialog = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='dialog']"))
            )
            
            # Wait for the dialog to be fully loaded
            time.sleep(1)
            
            # Scroll to load all followers
            self.scroll_to_load_all(followers_dialog)

            # Extract usernames
            follower_usernames = self.extract_usernames(followers_dialog)
            print(f"Found {len(follower_usernames)} followers")
            
            # Close dialog by pressing Escape
            webdriver.ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
            time.sleep(1)
            
            return follower_usernames

        except Exception as e:
            print(f"Error getting followers: {str(e)}")
            return []

    def get_following(self):
        try:
            print("Navigating to profile...")
            self.driver.get(f'{self.base_url}/{self.username}/')
            time.sleep(2)

            # Click following button
            print("Opening following list...")
            following_link = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/following')]"))
            )
            following_count = following_link.text
            print(f"Found {following_count}")
            following_link.click()
            time.sleep(2)

            # Get following dialog
            print("Waiting for following dialog...")
            following_dialog = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='dialog']"))
            )
            
            # Wait for the dialog to be fully loaded
            time.sleep(2)
            
            # Scroll to load all following
            self.scroll_to_load_all(following_dialog)

            # Extract usernames
            following_usernames = self.extract_usernames(following_dialog)
            print(f"Found {len(following_usernames)} following")
            
            # Close dialog by pressing Escape
            webdriver.ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
            time.sleep(1)
            
            return following_usernames

        except Exception as e:
            print(f"Error getting following: {str(e)}")
            return []

    def save_to_csv(self, followers, following):
        # Create data directory if it doesn't exist
        os.makedirs('data', exist_ok=True)
        
        # Save followers
        pd.DataFrame(followers, columns=['username']).to_csv('data/followers.csv', index=False)
        print(f"Saved {len(followers)} followers to data/followers.csv")
        
        # Save following
        pd.DataFrame(following, columns=['username']).to_csv('data/following.csv', index=False)
        print(f"Saved {len(following)} following to data/following.csv")
        
        # Create relationships CSV
        relationships = []
        for follower in followers:
            relationships.append({
                'source': self.username,
                'target': follower,
                'relationship': 'follower'
            })
        for following in following:
            relationships.append({
                'source': self.username,
                'target': following,
                'relationship': 'following'
            })
        
        pd.DataFrame(relationships).to_csv('data/relationships.csv', index=False)
        print(f"Saved {len(relationships)} relationships to data/relationships.csv")

    def run(self):
        try:
            self.login()
            print("Getting followers...")
            followers = self.get_followers()
            print("Getting following...")
            following = self.get_following()
            self.save_to_csv(followers, following)
            print("Scraping completed successfully!")
        finally:
            self.driver.quit()

if __name__ == "__main__":
    scraper = InstagramScraper()
    scraper.run() 