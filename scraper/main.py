from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import random

from config import Config
from linkedin_scraper import LinkedInScraper
from data_manager import DataManager

class LinkedInJobScraper:
    def __init__(self):
        self.config = Config()
        self.setup_driver()
        self.scraper = LinkedInScraper(self.driver)
        self.data_manager = DataManager()

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
            # Login
            self.scraper.login(self.config.LINKEDIN_EMAIL, self.config.LINKEDIN_PASSWORD)

            # Navigate to job search page
            self.driver.get(self.config.JOB_ALERT_URL)
            time.sleep(5)
            self.scraper.wait_for_captcha()

            # Extract job details
            job_cards = self.driver.find_elements(By.CLASS_NAME, "job-card-container")
            
            print("\nExtracting job details...")
            for i, job_card in enumerate(job_cards, 1):
                print(f"Processing job {i} of {len(job_cards)}...")
                job_data = self.scraper.extract_job_details(job_card)
                self.data_manager.add_job(job_data)
                time.sleep(random.uniform(1, 2))

            # Save results
            self.data_manager.save_to_csv()

        finally:
            self.driver.quit()

if __name__ == "__main__":
    scraper = LinkedInJobScraper()
    scraper.run() 