import json
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from concurrent.futures import ThreadPoolExecutor
import time
import os
import subprocess

# Selenium setup with headless mode
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run browser in headless mode
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(options=chrome_options)
wait = WebDriverWait(driver, 0)

# List to store dynamically extracted category URLs
start_urls = []

# Function to extract category URLs dynamically
def extract_category_urls(base_url):
    driver.get(base_url)
    time.sleep(0)
    print(f"Extracting category URLs from: {base_url}")
    try:
        category_elements = driver.find_elements(By.CSS_SELECTOR, "li[id^='cat_id_'] a")
        for element in category_elements:
            category_url = element.get_attribute("href")
            if category_url:
                print(f"Found category URL: {category_url}")
                start_urls.append(category_url)
    except Exception as e:
        print(f"Error extracting category URLs: {e}")

# Base URL to start extracting categories
base_url = "https://mustangclinic.eu/en/"  # Replace with the main category page

# Extract all category URLs dynamically
extract_category_urls(base_url)

# List to store all product details
detailed_data = []

# Function to scrape product details directly from category pages
def scrape_category_page(url):
    current_url = url
    while True:
        try:
            print(f"Scraping category page: {current_url}")
            driver.get(current_url)
            time.sleep(2)  # Replace with explicit waits if necessary

            # Locate all product elements on the page
            product_elements = driver.find_elements(By.CSS_SELECTOR, "article.product-miniature")
            for product in product_elements:
                try:
                    # Extract product details
                    product_name = product.find_element(By.CSS_SELECTOR, ".product-title a").text.strip()
                    price = product.find_element(By.CSS_SELECTOR, ".price").text.strip()
                    part_number = product.get_attribute("data-id-product")  # Extract part number from data attribute

                    # Handle availability with a fallback
                    try:
                        availability_element = product.find_element(By.CSS_SELECTOR, ".pl-availability")
                        availability = availability_element.text.strip() if availability_element else None
                    except Exception:
                        availability = None

                    # Skip product if availability is missing
                    if not availability:
                        print(f"Skipping product with missing availability: {product.get_attribute('data-id-product')}")
                        continue

                    # Append product details to the list
                    detailed_data.append({
                        "COMPETITOR": "Mustang Clinic",
                        "NAME": product_name,
                        "URL": current_url,
                        "PRICE": price,
                        "PART_NUMBER": part_number,
                        "INVENTORY": availability
                    })
                    print(f"Scraped: {product_name} - {price} - {availability}")
                except Exception as e:
                    print(f"Error scraping a product: {e}")

            # Check for the "Next" button to go to the next page
            try:
                next_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a.next.js-search-link")))
                current_url = next_button.get_attribute("href")
                print(f"Navigating to next page: {current_url}")
            except Exception:
                print("No more pages to scrape in this category.")
                break
        except Exception as e:
            print(f"Error scraping page: {e}")
            break



# Start the scraping process
print("Starting product detail scraping...")
with ThreadPoolExecutor(max_workers=1) as executor:
    executor.map(scrape_category_page, start_urls)

# Close the browser
driver.quit()

# Save the scraped data to a CSV file
csv_file = "mustang_clinic_products.csv"
with open(csv_file, mode="w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(file, fieldnames=["COMPETITOR", "NAME", "URL", "PRICE", "PART_NUMBER", "INVENTORY"])
    writer.writeheader()
    writer.writerows(detailed_data)

print(f"Scraped data saved to {csv_file}")

# Push the CSV file to GitHub
try:
    repo_path = os.getcwd()  # Assume the script is run from the repo directory
    csv_path = os.path.join(repo_path, csv_file)

    # Git commands to add, commit, and push the CSV
    subprocess.run(["git", "add", csv_path], check=True)
    subprocess.run(["git", "commit", "-m", "Add updated Mustang Clinic product data CSV"], check=True)
    subprocess.run(["git", "push"], check=True)
    print(f"{csv_file} successfully pushed to GitHub.")
except subprocess.CalledProcessError as e:
    print(f"Error with Git command: {e}")
except Exception as e:
    print(f"General error pushing to GitHub: {e}")
