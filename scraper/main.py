from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random

from src.config.config import Config
from src.scraper.linkedin_scraper import LinkedInScraper
from src.data.data_manager import DataManager
from src.database.database_manager import DatabaseManager

class LinkedInJobScraper:
    
    def __init__(self):
        self.config = Config()
        self.setup_driver()
        self.scraper = LinkedInScraper(self.driver, self.config)
        self.data_manager = DataManager()
        self.db_manager = DatabaseManager(self.config.SUPABASE_URL, self.config.SUPABASE_KEY)

    def setup_driver(self):
        """Configure and initialize the Selenium WebDriver with optimized settings"""
        options = Options()
        
        # Profile and session persistence
        options.add_argument(f'--user-data-dir={self.config.CHROME_PROFILE}')
        options.add_argument('--profile-directory=Default')
        options.add_argument('--enable-profile-shortcut-manager')
        options.add_argument('--password-store=basic')
        
        # Performance optimization settings
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-infobars')
        options.add_argument('--disable-notifications')
        options.add_argument('--disable-popup-blocking')
        
        # Memory and resource optimization
        options.add_argument('--disable-features=TranslateUI')
        options.add_argument('--disable-translate')
        options.add_argument('--disable-web-security')
        options.add_argument('--disable-client-side-phishing-detection')
        options.add_argument('--disable-component-extensions-with-background-pages')
        options.add_argument('--disable-default-apps')
        options.add_argument('--disable-background-timer-throttling')
        options.add_argument('--disable-backgrounding-occluded-windows')
        options.add_argument('--disable-renderer-backgrounding')
        
        # Network optimization
        options.add_argument('--dns-prefetch-disable')
        options.add_argument('--disable-sync')
        options.add_argument('--no-proxy-server')
        options.add_argument('--disable-web-resources')
        
        # Page load strategy
        options.page_load_strategy = 'eager'
        
        # User agent
        options.add_argument(f'user-agent={self.config.USER_AGENT}')
        
        # Start optimized options
        options.add_argument('--start-maximized')
        options.add_argument('--window-size=1920,1080')
        
        # Additional performance preferences
        prefs = {
            'profile.default_content_setting_values.notifications': 2,
            'profile.default_content_settings.popups': 0,
            'download.prompt_for_download': False,
            'download.directory_upgrade': True,
            'safebrowsing.enabled': True,
            'disk-cache-size': 4096,
            'media.autoplay.enabled': False,
            'media.cache_size': 0,
            'permissions.default.stylesheet': 2,
            'javascript.enabled': True,
            'dom.ipc.plugins.enabled': False,
            'browser.cache.memory.enable': True,
            'browser.cache.memory.capacity': 4096,
            'browser.cache.disk.enable': False,
            'network.cookie.cookieBehavior': 0,
            'network.http.max-connections-per-server': 10,
            'network.http.max-persistent-connections-per-server': 5,
            'credentials_enable_service': True,
            'profile.password_manager_enabled': True,
        }
        options.add_experimental_option('prefs', prefs)
        
        # Initialize the driver with optimized settings
        self.driver = webdriver.Remote(
            command_executor=self.config.SELENIUM_HOST,
            options=options
        )
        
        # Set timeouts
        self.driver.set_page_load_timeout(20)
        self.driver.set_script_timeout(20)
        self.driver.implicitly_wait(2)
        
        return self.driver

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
            wait = WebDriverWait(self.driver, 5)
            
            while total_jobs_processed < self.config.MAX_PROCESS_JOBS:
                print(f"\nProcessing page {page}")
                processed_jobs = 0
                
                while True:
                    # Get fresh list of job cards using selectors from LinkedInScraper
                    job_list = wait.until(
                        EC.presence_of_element_located((
                            By.CSS_SELECTOR, 
                            self.scraper.selectors['container'].selector
                        ))
                    )
                    current_jobs = job_list.find_elements(
                        By.CSS_SELECTOR, 
                        self.scraper.selectors['job_cards'].selector
                    )
                    current_jobs_count = len(current_jobs)
                    
                    # Process only new jobs
                    for i in range(processed_jobs, current_jobs_count):
                        if total_jobs_processed >= self.config.MAX_PROCESS_JOBS:
                            print(f"\nReached maximum job limit of {self.config.MAX_PROCESS_JOBS}")
                            self.db_manager.upsert_jobs(self.data_manager.jobs) 
                            return
                            
                        print(f"Processing job {i + 1} of {current_jobs_count} (Total: {total_jobs_processed + 1})")
                        
                        # Add delay before processing next job
                        delay = random.uniform(0.5, 1.0)  # Random delay between 0.5-1 seconds
                        # time.sleep(delay)
                        
                        job_data, success = self.scraper.extract_job_details(i)
                        if not success:
                            print(f"Failed to extract job details for job {i + 1}")
                            continue
                        
                        self.data_manager.add_job(job_data)
                        total_jobs_processed += 1
                        
                        # Add delay after processing job
                        delay = random.uniform(0.5, 1.0)  # Random delay between 0.5-1 seconds
                        # time.sleep(delay)
                    
                    processed_jobs = current_jobs_count
                    
                    # Get fresh reference to job list and last job card before scrolling
                    fresh_job_list = wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".scaffold-layout__list ul"))
                    )
                    fresh_jobs = fresh_job_list.find_elements(By.CSS_SELECTOR, "li div.job-card-container")
                    
                    if fresh_jobs:
                        last_job = fresh_jobs[-1]
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", last_job)
                        time.sleep(0.5)
                    
                    # Check if we got any new jobs after scrolling
                    new_job_list = wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".scaffold-layout__list ul"))
                    )
                    new_jobs = new_job_list.find_elements(By.CSS_SELECTOR, "li div.job-card-container")
                    if len(new_jobs) == current_jobs_count:
                        print(f"No more jobs loading on page {page}")
                        break
                
                print(f"Processed {processed_jobs} jobs on page {page}")
                
                # Try to go to next page
                try:
                    # Scroll back to top to ensure pagination is visible
                    self.driver.execute_script("window.scrollTo(0, 0);")
                    time.sleep(1)
                    
                    # Find and click the next page number button
                    next_page = page + 1
                    wait = WebDriverWait(self.driver, 10)
                    next_page_button = wait.until(
                        EC.element_to_be_clickable(
                            (By.CSS_SELECTOR, f"button[aria-label='Page {next_page}']")
                        )
                    )
                    
                    if not next_page_button:
                        print("\nReached last page")
                        break
                    
                    # Get the current URL before clicking
                    current_url = self.driver.current_url
                    
                    # Click and wait for URL change
                    self.driver.execute_script("arguments[0].click();", next_page_button)
                    
                    # Wait for URL to change
                    wait.until(lambda driver: driver.current_url != current_url)
                    
                    # Wait for DOM to be ready
                    wait.until(
                        lambda driver: driver.execute_script('return document.readyState') == 'complete'
                    )
                    
                    # Wait for the job list container with increased timeout
                    wait = WebDriverWait(self.driver, 20)  # Increased timeout for slow loading
                    job_list = wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".scaffold-layout__list ul"))
                    )
                    
                    # Wait for job cards to be present and visible
                    wait.until(
                        lambda driver: len(job_list.find_elements(By.CSS_SELECTOR, "li div.job-card-container")) > 0 and
                        driver.find_element(By.CSS_SELECTOR, "li div.job-card-container").is_displayed()
                    )
                    
                    # Reset for new page
                    page += 1
                    processed_jobs = 0
                    time.sleep(2)  # Increased wait time to ensure everything is ready
                    
                except Exception as e:
                    print(f"\nError during page transition: {str(e)}")
                    break

            # Upsert all collected jobs to database
            print("\nSaving jobs to database...")
            self.db_manager.upsert_jobs(self.data_manager.jobs)

        finally:
            self.driver.quit()

if __name__ == "__main__":
    scraper = LinkedInJobScraper()
    scraper.run()