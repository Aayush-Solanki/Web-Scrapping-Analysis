import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

# Constants
# Define constants for base URL, download directory, and property details
BASE_URL = "https://freesearchigrservice.maharashtra.gov.in/"
DOWNLOAD_DIR = "transaction_documents"
YEAR = "2023"
DISTRICT = "Pune"
TAHSIL = "Haveli"
VILLAGE = "Wakad"

# Function to set up the Selenium WebDriver
def setup_driver():
    """Sets up the Selenium WebDriver with necessary options."""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run in headless mode to avoid opening browser (can be commented out for debugging)
    options.add_argument("--disable-gpu") # Disable GPU acceleration (useful in headless mode)
    options.add_argument("--no-sandbox") # Avoid sandboxing (required for some systems)
    driver = webdriver.Chrome(options=options) # Initialize WebDriver
    driver.get(BASE_URL) # Open the target URL
    return driver

# Function to wait for an element to be clickable
def wait_for_element(driver, by, locator, timeout=15):
    """Waits for a specific element to be clickable within the given timeout."""
    wait = WebDriverWait(driver, timeout)
    return wait.until(EC.element_to_be_clickable((by, locator)))

# Function to fill the search form with property details
def fill_form(driver, property_number):
    """Fills out the search form with the required details based on the property number."""
    try:
        # Click the 'Rest of Maharashtra' option
        print("Locating 'Rest of Maharashtra' option...")
        wait_for_element(driver, By.ID, "optROM").click()

        # Select dropdown values for Year, District, Tahsil, and Village
        Select(driver.find_element(By.ID, "ddlYear")).select_by_visible_text(YEAR)
        Select(driver.find_element(By.ID, "ddlDistrict")).select_by_visible_text(DISTRICT)
        Select(driver.find_element(By.ID, "ddlTahsil")).select_by_visible_text(TAHSIL)
        Select(driver.find_element(By.ID, "ddlVillage")).select_by_visible_text(VILLAGE)

        # Enter the property number in the input field
        driver.find_element(By.ID, "txtPropertyNo").clear()
        driver.find_element(By.ID, "txtPropertyNo").send_keys(property_number)

        # Handle CAPTCHA manually (needs user input)
        captcha_value = input("Enter CAPTCHA displayed: ")
        driver.find_element(By.ID, "txtCaptcha").send_keys(captcha_value)

        # Submit the form
        driver.find_element(By.ID, "btnSearch").click()

    except TimeoutException:
        # Handle timeout if the form cannot be filled within the specified time
        print(f"Timeout while filling form for Property Number: {property_number}")
        raise
    except Exception as e:
        # Handle any other exceptions during form filling
        print(f"Error in form filling: {e}")
        raise

# Function to scrape transaction data and handle pagination
def scrape_transactions(driver, property_number):
    """Scrapes transaction data from the results table and handles multiple pages if present."""
    try:
        # Wait until the transaction table is loaded
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "transactionTable"))
        )

        # Extract rows from the transaction table
        rows = driver.find_elements(By.CSS_SELECTOR, "#transactionTable tbody tr")
        for row in rows:
            # Extract data from each row
            cols = row.find_elements(By.TAG_NAME, "td")
            if len(cols) < 4:
                continue
            doc_num = cols[0].text.strip()
            sro_code = cols[1].text.strip()
            year = cols[2].text.strip()
            index_link = cols[3].find_element(By.TAG_NAME, "a").get_attribute("href")

            # Download the HTML content for each transaction
            download_html(driver, index_link, doc_num, sro_code, year)

        # Handle pagination by checking for the 'Next' button
        next_button = driver.find_element(By.LINK_TEXT, "Next")
        if "disabled" not in next_button.get_attribute("class"):
            next_button.click()
            scrape_transactions(driver, property_number) # Recursive call for next page

    except TimeoutException:
        # Handle timeout if no data is found
        print(f"No data found for Property Number: {property_number}")
    except NoSuchElementException:
        # Handle case where there are no more pages to scrape
        print("No more pages to scrape.")

# Function to download and save HTML content
def download_html(driver, link, doc_num, sro_code, year):
    """Downloads and saves the HTML content of each transaction."""
    driver.get(link) # Navigate to the link for the document
    time.sleep(2) # Wait for content to load

    # Save the page source as an HTML file
    html_content = driver.page_source
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    file_path = os.path.join(DOWNLOAD_DIR, f"{doc_num}_{sro_code}_{year}.html")
    with open(file_path) as file:
        file.write(html_content)
    print(f"Downloaded: {file_path}")

# Main function to coordinate the entire process
def main():
    """Main function to orchestrate the scraping process for multiple property numbers."""
    driver = setup_driver()
    try:
        # Loop through a range of property numbers for scraping
        for property_number in range(1, 11):
            try:
                print(f"Processing Property Number: {property_number}")
                fill_form(driver, property_number) # Fill the form for the current property number
                scrape_transactions(driver, property_number) # Scrape transaction data
                driver.get(BASE_URL) # Reset to the base URL for the next property
            except Exception as e:
                # Handle exceptions for individual property numbers without stopping the process
                print(f"Error processing Property Number {property_number}: {e}")
    finally:
        # Close the browser driver
        driver.quit()

# Entry point for the script execution
if __name__ == "__main__":
    main()

