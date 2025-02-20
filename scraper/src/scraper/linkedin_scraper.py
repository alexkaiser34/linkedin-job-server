from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement
from dataclasses import dataclass
from typing import Optional, Dict

import time
import random
from selenium.common.exceptions import (
    StaleElementReferenceException, 
    NoSuchElementException,
    TimeoutException
)
from ..scraper.job_data import JobData

@dataclass
class JobSelector:
    """Configuration for job data selectors"""
    selector: str  # CSS selector or XPATH
    attribute: Optional[str] = None  # Attribute to extract (e.g., 'text', 'innerHTML', 'aria-label')
    is_nested: bool = False  # Whether we need to traverse nested elements
    nested_selectors: Optional[list] = None  # List of selectors for nested elements

class LinkedInSelectors:
    """Centralized configuration for LinkedIn selectors"""
    
    # Job list selectors
    JOB_LIST = {
        'container': JobSelector(
            selector=".scaffold-layout__list ul"
        ),
        'job_cards': JobSelector(
            selector="li div.job-card-container"
        ),
        'title': JobSelector(
            selector="a.job-card-list__title--link",
            attribute="aria-label"
        ),
        'company': JobSelector(
            selector=".job-details-jobs-unified-top-card__company-name a",
            attribute="text"
        ),
        'metadata_container': JobSelector(
            selector=".job-details-jobs-unified-top-card__primary-description-container .t-black--light",
            is_nested=True,
            nested_selectors=[
                {"type": "location", "selector": "span.tvm__text:first-child", "attribute": "text"},
                {"type": "posted_time", "selector": "span.tvm__text--positive strong span:last-child", "attribute": "text"},
                {"type": "applicants", "selector": "span.tvm__text:last-child", "attribute": "text"}
            ]
        ),
        'description': JobSelector(
            selector="article.jobs-description__container",
            attribute="innerHTML"
        ),
        'details_container': JobSelector(
            selector="#job-details",
            attribute="textContent"
        )
    }

class LinkedInScraper:
    def __init__(self, driver):
        self.driver = driver
        self.selectors = LinkedInSelectors.JOB_LIST

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

    def wait_for_job_details_loading(self, timeout: int = 10, min_text_length: int = 100) -> bool:
        """
        Wait for job details to finish loading by checking text content length.
        Returns True if loading completed successfully, False otherwise.
        """
        try:
            wait = WebDriverWait(self.driver, timeout)
            
            def check_content_loaded(driver):
                try:
                    details_container = driver.find_element(
                        By.CSS_SELECTOR, 
                        self.selectors['details_container'].selector
                    )
                    text_content = details_container.get_attribute(
                        self.selectors['details_container'].attribute
                    )
                    # Remove whitespace and check length
                    cleaned_text = ' '.join(text_content.split())
                    return len(cleaned_text) >= min_text_length
                except:
                    return False
            
            # First wait for the container to exist
            wait.until(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR, 
                    self.selectors['details_container'].selector
                ))
            )
            
            # Then wait for content to be loaded
            wait.until(check_content_loaded)
            
            # Additional verification that other essential elements are present
            wait.until(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR, 
                    self.selectors['company'].selector
                ))
            )
            
            return True
            
        except TimeoutException as e:
            print(f"Timeout waiting for job details to load: {str(e)}")
            return False

    def extract_job_details(self, job_index: int) -> JobData:
        """Extract job details from a job card using its index in the list"""
        job_data = JobData.create_empty()
        
        try:
            # Find fresh job card using index
            wait = WebDriverWait(self.driver, 5)
            
            # Find the job list using selector from config
            job_list = wait.until(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR, 
                    self.selectors['container'].selector
                ))
            )
            
            # Get all job cards using selector from config
            job_cards = job_list.find_elements(
                By.CSS_SELECTOR, 
                self.selectors['job_cards'].selector
            )
            
            if job_index >= len(job_cards):
                print(f"Job index {job_index} out of range")
                return job_data
            
            # Get fresh reference to the specific job card
            job_card = job_cards[job_index]
            
            # Find and click the title link using selector from config
            title_link = job_card.find_element(By.CSS_SELECTOR, self.selectors['title'].selector)
            job_data.title = self._get_job_title(job_card)
            job_data.job_url = self._get_job_url(job_card.get_attribute('data-job-id'))
            
            # Click the title and wait for content to load
            self.driver.execute_script("arguments[0].click();", title_link)
            
            # Wait for loading to complete
            if not self.wait_for_job_details_loading():
                print("Failed to load job details, returning partial data")
                return job_data
            
            # Now get the job details
            try:
                # Company
                job_data.company = self._get_company_name()
                
                # Metadata
                self._get_job_metadata(job_data)
                
                # Description
                job_data.description = self._get_job_description()
                
            except Exception as e:
                print(f"Error extracting job details after loading: {str(e)}")
            
            return job_data
            
        except Exception as e:
            print(f"Error extracting job details: {str(e)}")
            return job_data

    def _get_job_url(self, job_card_id: str) -> str:
        """Get the job URL from the job card ID"""
        return f"https://www.linkedin.com/jobs/view/{job_card_id}"

    def _get_element_data(self, element: WebElement, selector: JobSelector) -> str:
        """Generic method to extract data using a selector configuration"""
        try:
            if selector.is_nested:
                return self._handle_nested_selectors(element, selector)
            
            found_element = element.find_element(By.CSS_SELECTOR, selector.selector)
            if selector.attribute == "text":
                return self.clean_text(found_element.text)
            elif selector.attribute == "innerHTML":
                return found_element.get_attribute('innerHTML')
            else:
                return self.clean_text(found_element.get_attribute(selector.attribute))
        except Exception as e:
            print(f"Error extracting data with selector {selector.selector}: {str(e)}")
            return "Not available"

    def _handle_nested_selectors(self, element: WebElement, selector: JobSelector) -> Dict[str, str]:
        """Handle nested selectors for complex elements"""
        result = {}
        try:
            container = element.find_element(By.CSS_SELECTOR, selector.selector)
            for nested in selector.nested_selectors:
                try:
                    found_element = container.find_element(By.CSS_SELECTOR, nested["selector"])
                    value = (found_element.text if nested["attribute"] == "text" 
                            else found_element.get_attribute(nested["attribute"]))
                    result[nested["type"]] = self.clean_text(value)
                except Exception:
                    result[nested["type"]] = "Not available"
        except Exception as e:
            print(f"Error handling nested selectors: {str(e)}")
            for nested in selector.nested_selectors:
                result[nested["type"]] = "Not available"
        return result

    def _get_job_title(self, job_card: WebElement) -> str:
        return self._get_element_data(job_card, self.selectors['title'])

    def _click_job_card(self, job_card_id: str) -> Optional[WebElement]:
        """Click the job card and return the refreshed element"""
        try:
            wait = WebDriverWait(self.driver, 5)
            refreshed_card = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, f"div[data-job-id='{job_card_id}']"))
            )
            self.driver.execute_script("arguments[0].click();", refreshed_card)
            time.sleep(0.2)
            return refreshed_card
        except (TimeoutException, StaleElementReferenceException):
            return None

    def _get_company_name(self) -> str:
        try:
            wait = WebDriverWait(self.driver, 5)
            company_element = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, self.selectors['company'].selector)))
            return self._get_element_data(company_element.parent, self.selectors['company'])
        except (TimeoutException, StaleElementReferenceException):
            return "Not available"

    def _get_job_metadata(self, job_data: JobData) -> None:
        """Extract metadata (location, posted time, applicants) from job card"""
        try:
            wait = WebDriverWait(self.driver, 5)
            container = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, self.selectors['metadata_container'].selector))
            )
            metadata = self._get_element_data(container.parent, self.selectors['metadata_container'])
            
            # Extract metadata from the returned dictionary
            job_data.location = metadata.get('location', "Not available")
            job_data.posted_time = metadata.get('posted_time', "Not available")
            job_data.applicants = metadata.get('applicants', "Not available")
            
        except (TimeoutException, StaleElementReferenceException) as e:
            print(f"Error getting job metadata: {str(e)}")
            job_data.location = "Not available"
            job_data.posted_time = "Not available"
            job_data.applicants = "Not available"

    def _get_job_description(self) -> str:
        try:
            wait = WebDriverWait(self.driver, 5)
            description_element = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, self.selectors['description'].selector)))
            return self._get_element_data(description_element.parent, self.selectors['description'])
        except (TimeoutException, StaleElementReferenceException):
            return "Not available"

    @staticmethod
    def clean_text(text):
        """Clean text by removing extra whitespace and newlines"""
        if not text:
            return "Not available"
        cleaned = ' '.join(text.replace('\n', ' ').split())
        cleaned = cleaned.replace('"', "'")
        return cleaned 