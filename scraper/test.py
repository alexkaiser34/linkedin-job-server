import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException
import csv
from datetime import datetime

# Your LinkedIn credentials (store them securely!)
LINKEDIN_EMAIL = "alexkaiser@me.com"
LINKEDIN_PASSWORD = "$Ecret12"

# Replace this with your specific saved job alert URL
JOB_ALERT_URL = "https://www.linkedin.com/jobs/search/?distance=25&f_TPR=r86400&f_WT=1%2C3&geoId=90000664&keywords=software%20engineer&origin=JOB_SEARCH_PAGE_JOB_FILTER&sortBy=DD&spellCorrectionEnabled=true"

def wait_for_captcha(driver):
   """Pause execution until CAPTCHA is solved manually."""
   while True:
       try:
           driver.find_element(By.CLASS_NAME, "captcha__image")  # CAPTCHA detected
           print("CAPTCHA detected! Solve it manually in the browser.")
           time.sleep(10)  # Wait before checking again
       except NoSuchElementException:
           print("CAPTCHA solved! Continuing...")
           break

def is_logged_in(driver):
    """Check if we're already logged into LinkedIn"""
    try:
        # Try to find an element that only exists when logged in
        # LinkedIn's nav bar with profile picture is a good indicator
        driver.find_element(By.CLASS_NAME, "global-nav__me-photo")
        return True
    except NoSuchElementException:
        return False

def clean_text(text):
    """Clean text by removing extra whitespace and newlines"""
    if not text:
        return "Not available"
    # Replace newlines and multiple spaces with single space
    cleaned = ' '.join(text.replace('\n', ' ').split())
    # Remove any quotes that might interfere with CSV
    cleaned = cleaned.replace('"', "'")
    return cleaned

def summarize_text(text, max_length=500):
    """Summarize text if it's longer than max_length"""
    if not text or len(text) <= max_length:
        return clean_text(text)
    return clean_text(text[:max_length]) + "..."

def extract_job_details(driver, job_card):
    """Extract detailed information for a single job posting"""
    details = {}
    
    try:
        # Click on the job card to load details
        job_card.click()
        time.sleep(3)  # Wait for details to load
        
        # Basic information - title
        try:
            title = job_card.find_element(By.CSS_SELECTOR, "h3.base-search-card__title").text.strip()
        except NoSuchElementException:
            try:
                title = job_card.find_element(By.CSS_SELECTOR, ".job-card-container__link").text.strip()
            except NoSuchElementException:
                title = "Not available"
        details['title'] = clean_text(title)

        # Company name and URL from the job details card
        try:
            company_element = driver.find_element(By.CLASS_NAME, 
                "job-details-jobs-unified-top-card__company-name")
            company_link = company_element.find_element(By.TAG_NAME, "a")
            details['company'] = clean_text(company_link.text)
        except NoSuchElementException as e:
            print(f"Error finding company information: {str(e)}")
            details['company'] = "Not available"

        # Get the primary description container and its spans
        try:
            container = driver.find_element(By.CLASS_NAME, 
                "job-details-jobs-unified-top-card__primary-description-container")
            spans = container.find_elements(By.TAG_NAME, "span")
            
            if spans:
                # Location is first span (index 0)
                details['location'] = clean_text(spans[0].text)
                
                # Posted time is fifth span (index 4)
                if len(spans) >= 5:
                    details['posted_time'] = clean_text(spans[4].text)
                else:
                    details['posted_time'] = "Not available"
                
                # Applicants is last span
                details['applicants'] = clean_text(spans[-1].text)
            else:
                details['location'] = "Not available"
                details['posted_time'] = "Not available"
                details['applicants'] = "Not available"
                
        except NoSuchElementException as e:
            print(f"Error finding primary description container: {str(e)}")
            details['location'] = "Not available"
            details['posted_time'] = "Not available"
            details['applicants'] = "Not available"

        # Get the full HTML of the job description
        try:
            description_container = driver.find_element(By.CLASS_NAME, "jobs-description__container")
            details['description'] = description_container.get_attribute('innerHTML')
        except NoSuchElementException:
            details['description'] = "Not available"

    except Exception as e:
        print(f"Error extracting job details: {str(e)}")
        details['error'] = str(e)
    
    return details

def save_to_csv(jobs, filename=None):
    """Save job details to a CSV file"""
    if filename is None:
        filename = f"linkedin_jobs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    fieldnames = ['title', 'company', 'location', 'posted_time', 
                  'applicants', 'description', 'error']
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for job in jobs:
                writer.writerow(job)
        print(f"\nJob details successfully saved to {filename}")
    except Exception as e:
        print(f"Error saving to CSV: {str(e)}")

def main():
    # Configure Selenium WebDriver
    options = Options()
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
    
    # Add browser fingerprinting evasion
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)
    
    # Use a persistent profile to maintain cookies and session data
    user_data_dir = "chrome_profile"
    options.add_argument(f'--user-data-dir={user_data_dir}')
    
    # Remove headless mode as it's more easily detected
    # options.add_argument("--headless")

    # Initialize WebDriver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    # Set window size explicitly
    driver.set_window_size(1920, 1080)
    
    # Add random delays function
    def random_delay():
        time.sleep(random.uniform(2, 5))

    try:
        # Execute CDP commands to modify navigator.webdriver flag
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            '''
        })
        
        # First check if we're already logged in by visiting LinkedIn
        driver.get("https://www.linkedin.com")
        random_delay()
        
        # Only proceed with login if we're not already logged in
        if not is_logged_in(driver):
            # Step 1: Open LinkedIn login page
            driver.get("https://www.linkedin.com/login")
            random_delay()
            
            # Step 2: Enter credentials with human-like typing
            username = driver.find_element(By.ID, "username")
            password = driver.find_element(By.ID, "password")
            
            for char in LINKEDIN_EMAIL:
                username.send_keys(char)
                time.sleep(random.uniform(0.1, 0.3))
            
            random_delay()
            
            for char in LINKEDIN_PASSWORD:
                password.send_keys(char)
                time.sleep(random.uniform(0.1, 0.3))
                
            random_delay()
            password.send_keys(Keys.RETURN)

            # Handle CAPTCHA if needed after login
            time.sleep(3)
            wait_for_captcha(driver)
        else:
            print("Already logged in, skipping login process")

        # Step 4: Navigate to the specific job alert page
        driver.get(JOB_ALERT_URL)
        time.sleep(5)  # Allow the page to load

        # Step 5: Handle possible CAPTCHA again
        wait_for_captcha(driver)

        # Step 6: Extract job details
        job_cards = driver.find_elements(By.CLASS_NAME, "job-card-container")
        
        jobs = []
        print("\nExtracting job details...")
        for i, job_card in enumerate(job_cards, 1):
            print(f"Processing job {i} of {len(job_cards)}...")
            job_details = extract_job_details(driver, job_card)
            jobs.append(job_details)
            time.sleep(random.uniform(1, 2))  # Random delay between processing jobs

        # Save results to CSV
        save_to_csv(jobs)

    finally:
        # Close the browser session
        driver.quit()

if __name__ == "__main__":
   main()