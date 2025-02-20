from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
import time
import random
from job_data import JobData

class LinkedInScraper:
    def __init__(self, driver):
        self.driver = driver

    def wait_for_captcha(self):
        """Pause execution until CAPTCHA is solved manually."""
        while True:
            try:
                self.driver.find_element(By.CLASS_NAME, "captcha__image")
                print("CAPTCHA detected! Solve it manually in the browser.")
                time.sleep(10)
            except NoSuchElementException:
                print("CAPTCHA solved! Continuing...")
                break

    def is_logged_in(self):
        """Check if we're already logged into LinkedIn"""
        try:
            # First try to access a LinkedIn page
            current_url = self.driver.current_url
            if not current_url.startswith('https://www.linkedin.com'):
                self.driver.get('https://www.linkedin.com')
                time.sleep(3)
            
            # Look for the nav menu that only appears when logged in
            self.driver.find_element(By.CLASS_NAME, "global-nav__me-photo")
            return True
        except NoSuchElementException:
            return False
        except Exception as e:
            print(f"Error checking login status: {str(e)}")
            return False

    def login(self, email, password):
        """Login to LinkedIn"""
        try:
            # Check if already logged in
            if self.is_logged_in():
                print("Already logged in, skipping login process")
                return True

            print("Not logged in, starting login process...")
            self.driver.get("https://www.linkedin.com/login")
            time.sleep(random.uniform(2, 4))

            username = self.driver.find_element(By.ID, "username")
            password_field = self.driver.find_element(By.ID, "password")

            for char in email:
                username.send_keys(char)
                time.sleep(random.uniform(0.1, 0.3))

            time.sleep(random.uniform(0.5, 1.0))

            for char in password:
                password_field.send_keys(char)
                time.sleep(random.uniform(0.1, 0.3))

            time.sleep(random.uniform(0.5, 1.0))
            password_field.send_keys(Keys.RETURN)

            time.sleep(3)
            self.wait_for_captcha()

            # Verify login was successful
            if self.is_logged_in():
                print("Login successful!")
                return True
            else:
                print("Login failed!")
                return False

        except Exception as e:
            print(f"Error during login process: {str(e)}")
            return False

    def extract_job_details(self, job_card) -> JobData:
        """Extract job details from a job card"""
        job_data = JobData.create_empty()
        
        try:
            # Click on the job card to load details
            job_card.click()
            time.sleep(3)
            
            # Basic information - title
            try:
                title = job_card.find_element(By.CSS_SELECTOR, "h3.base-search-card__title").text.strip()
            except NoSuchElementException:
                try:
                    title = job_card.find_element(By.CSS_SELECTOR, ".job-card-container__link").text.strip()
                except NoSuchElementException:
                    title = "Not available"
            job_data.title = self.clean_text(title)

            # Company name from job details card
            try:
                company_element = self.driver.find_element(By.CLASS_NAME, 
                    "job-details-jobs-unified-top-card__company-name")
                company_link = company_element.find_element(By.TAG_NAME, "a")
                job_data.company = self.clean_text(company_link.text)
            except NoSuchElementException as e:
                print(f"Error finding company information: {str(e)}")

            # Get spans from primary description container
            try:
                container = self.driver.find_element(By.CLASS_NAME, 
                    "job-details-jobs-unified-top-card__primary-description-container")
                spans = container.find_elements(By.TAG_NAME, "span")
                
                if spans:
                    job_data.location = self.clean_text(spans[0].text)
                    if len(spans) >= 5:
                        job_data.posted_time = self.clean_text(spans[4].text)
                    job_data.applicants = self.clean_text(spans[-1].text)
                    
            except NoSuchElementException as e:
                print(f"Error finding primary description container: {str(e)}")

            # Get the full HTML of the job description
            try:
                description_container = self.driver.find_element(By.CLASS_NAME, "jobs-description__container")
                job_data.description = description_container.get_attribute('innerHTML')
            except NoSuchElementException:
                pass

        except Exception as e:
            print(f"Error extracting job details: {str(e)}")
            job_data.error = str(e)
        
        return job_data

    @staticmethod
    def clean_text(text):
        """Clean text by removing extra whitespace and newlines"""
        if not text:
            return "Not available"
        cleaned = ' '.join(text.replace('\n', ' ').split())
        cleaned = cleaned.replace('"', "'")
        return cleaned 