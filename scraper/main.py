from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import random
from selenium.common.exceptions import NoSuchElementException

from src.config.config import Config
from src.scraper.linkedin_scraper import LinkedInScraper
from src.data.data_manager import DataManager
from src.database.database_manager import DatabaseManager

class LinkedInJobScraper:
    def __init__(self):
        self.config = Config()
        self.setup_driver()
        self.scraper = LinkedInScraper(self.driver)
        self.data_manager = DataManager()
        self.db_manager = DatabaseManager(self.config.SUPABASE_URL, self.config.SUPABASE_KEY)

    def setup_driver(self):
        """Configure and initialize the Selenium WebDriver"""
        options = Options()
        options.add_argument(f'--window-size={self.config.WINDOW_SIZE[0]},{self.config.WINDOW_SIZE[1]}')
        options.add_argument(f'--user-agent={self.config.USER_AGENT}')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument(f'--user-data-dir={self.config.CHROME_PROFILE}')

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.set_window_size(*self.config.WINDOW_SIZE)

        # Modify navigator.webdriver flag
        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
        })

    def run(self):
        """Main execution flow"""
        try:
            # Initialize database with migrations
            print("Initializing database...")
            self.db_manager.initialize_database()

            # Login
            self.scraper.login(self.config.LINKEDIN_EMAIL, self.config.LINKEDIN_PASSWORD)

            # Navigate to job search page
            self.driver.get(self.config.JOB_ALERT_URL)
            time.sleep(1)
            self.scraper.wait_for_captcha()

            page = 1
            total_jobs_processed = 0
            
            while total_jobs_processed < self.config.MAX_JOBS:
                print(f"\nProcessing page {page}")
                processed_jobs = 0
                
                while True:
                    # Get current visible job cards
                    job_cards = self.driver.find_elements(By.CLASS_NAME, "job-card-container")
                    current_jobs_count = len(job_cards)
                    
                    # Process only new jobs (ones we haven't processed yet)
                    for i in range(processed_jobs, current_jobs_count):
                        if total_jobs_processed >= self.config.MAX_JOBS:
                            print(f"\nReached maximum job limit of {self.config.MAX_JOBS}")
                            # Upsert collected jobs to database
                            self.db_manager.upsert_jobs(self.data_manager.jobs)
                            return
                            
                        print(f"Processing job {i + 1} of {current_jobs_count} (Total: {total_jobs_processed + 1})")
                        job_data = self.scraper.extract_job_details(job_cards[i])
                        self.data_manager.add_job(job_data)
                        total_jobs_processed += 1
                        time.sleep(0.2)
                    
                    processed_jobs = current_jobs_count
                    
                    # Scroll to the last job card to trigger loading more
                    if job_cards:
                        last_job = job_cards[-1]
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", last_job)
                        time.sleep(0.5)
                    
                    # Check if we got any new jobs after scrolling
                    new_job_cards = self.driver.find_elements(By.CLASS_NAME, "job-card-container")
                    if len(new_job_cards) == current_jobs_count:
                        print(f"No more jobs loading on page {page}")
                        break
                
                print(f"Processed {processed_jobs} jobs on page {page}")
                
                # Try to go to next page
                try:
                    # Scroll back to top to ensure pagination is visible
                    self.driver.execute_script("window.scrollTo(0, 0);")
                    time.sleep(0.5)
                    
                    # Find and click the next page number button
                    next_page = page + 1
                    next_page_button = self.driver.find_element(By.CSS_SELECTOR, 
                        f"button[aria-label='Page {next_page}']")
                    
                    if not next_page_button:
                        print("\nReached last page")
                        break
                        
                    # Use JavaScript to click the button
                    self.driver.execute_script("arguments[0].click();", next_page_button)
                    page += 1
                    time.sleep(1)
                    
                except NoSuchElementException:
                    print("\nNo more pages available")
                    break

            # Upsert all collected jobs to database
            print("\nSaving jobs to database...")
            self.db_manager.upsert_jobs(self.data_manager.jobs)

        finally:
            self.driver.quit()

if __name__ == "__main__":
    scraper = LinkedInJobScraper()
    scraper.run() 