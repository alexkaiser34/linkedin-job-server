# LinkedIn Job Scraper

## Overview
This application is designed to automate the collection of job posting data from LinkedIn job searches. It navigates to a specified LinkedIn job search URL, logs in using provided credentials, and systematically extracts detailed information about each job posting. The data collected includes:

- Job Title
- Company Name
- Location
- Posted Time
- Number of Applicants
- Full Job Description (HTML)

This tool is particularly useful for:
- Job market analysis
- Tracking job posting trends
- Building a dataset of job requirements
- Monitoring specific job markets or companies

## Setup and Installation

### Prerequisites
- Python 3.8 or higher
- Chrome browser installed
- Git (for cloning the repository)

### Installation Steps

1. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Configure environment variables:

```bash
cp .env.test .env
```

Then edit `.env` with your actual credentials and configuration:
- `LINKEDIN_EMAIL`: Your LinkedIn login email
- `LINKEDIN_PASSWORD`: Your LinkedIn password
- `JOB_ALERT_URL`: The LinkedIn job search URL you want to scrape
- Other optional configuration parameters

### Running the Application

1. Ensure your virtual environment is activated
2. Run the main script:

```bash
python main.py
```

### Important Notes

- The application uses Selenium with Chrome WebDriver, which will open a visible Chrome window
- You may need to solve a CAPTCHA manually on the first run
- The Chrome profile is saved locally to maintain login sessions
- Job data is saved to a CSV file with a timestamp in the filename

### Dependencies
The main dependencies are listed in `requirements.txt`:
- selenium: For web automation
- python-dotenv: For environment variable management
- webdriver_manager: For Chrome WebDriver management

### Docker Deployment

#### Prerequisites for Docker Setup
- Docker installed on your ARM64 system
- Access to an Oracle VM or similar ARM64 environment
- SSH access to your VM for port forwarding

#### Running with Docker

1. Start the Selenium Chromium container with VNC support:
```bash
docker run -d --restart always \
  -p 4444:4444 -p 7900:7900 \
  -v $(pwd)/chrome_profile:/home/chrome-profile-data \
  --shm-size="4g" \
  --name selenium-chrome \
  selenium/standalone-chromium
```

2. Configure the application to use the remote WebDriver:
   - Update your `.env` file to include:
```bash
SELENIUM_HOST="<path_to_selenium_host>"
CHROME_PROFILE="<path_to_chrome_profile>"
```

3. Set up SSH tunnel for VNC access:
   - From your local machine, create an SSH tunnel in the background:
```bash
ssh -L 7900:localhost:7900 your_username@your_oracle_vm_ip -i <path_to_your_private_key> -N -f
```
   - The `-N` flag prevents executing a remote command
   - The `-f` flag sends the process to the background
   - To stop the tunnel later, find and kill the process:
```bash
# Find the SSH tunnel process and kill it
kill $(ps -e | grep "process name" | awk '{print $1}')
```

4. Access the browser interface:
   - Open your web browser and navigate to:
```
http://localhost:7900
```
   - Default VNC password is: `secret`
   - You can now see the Chrome browser and handle any security checkpoints

5. Run the application:
```bash
python main.py
```

#### Important Docker Notes
- The `--shm-size="4g"` flag is crucial for stable browser operation
- Chrome profile data is persisted in the `chrome_profile` directory
- Port 4444 is used for Selenium WebDriver communication
- Port 7900 is used for VNC access to view the browser
- Make sure both ports are allowed in your Oracle VM's security list

#### Handling Security Checkpoints
When LinkedIn presents a security checkpoint:
1. The script will pause and notify you
2. Access the browser through VNC viewer at `http://localhost:7900`
3. Complete the security verification manually
4. The script will continue automatically once verification is complete

#### Troubleshooting
- If the Selenium container fails to start, check Docker logs:
```bash
docker logs selenium-chrome
```
- If you can't access VNC:
  - Verify the SSH tunnel is active
  - Check if port 7900 is open in Oracle Cloud security list
  - Ensure the container is running: `docker ps`
- If the browser crashes, try increasing the shared memory size
- Ensure all mounted directories have appropriate permissions:
```bash
chmod 777 chrome_profile
```

## Contributing
Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## Disclaimer
This tool is for educational purposes only. Make sure to comply with LinkedIn's terms of service and implement appropriate delays between requests to avoid overloading their servers.