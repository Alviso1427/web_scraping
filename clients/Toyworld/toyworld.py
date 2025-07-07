import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urljoin, urlparse
import time
import math
import openpyxl
from bs4 import BeautifulSoup

# ---------------------------- Configuration ---------------------------- #
options = Options()
options.headless = True
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

chromedriver_path = "D:\\SOWMYA\\python script\\extract Title_ID\\Input\\CHROMDRIVE\\chromedriver-win64\\chromedriver.exe"
service = Service(chromedriver_path)
driver = webdriver.Chrome(service=service, options=options)
wait = WebDriverWait(driver, 30)

# ---------------------------- Functions ---------------------------- #

def extract_image_urls(url):
    """
    Extracts image URLs from a product page, filtering out 'medium' or 'large' sizes.
    Args:
        url (str): The URL of the product page.
    Returns:
        list: A list of full-resolution image URLs.
    """
    driver.get(url)
    time.sleep(3)  # Allow time for the page to load

    # Find all <a> tags with image URLs
    image_elements = driver.find_elements(By.CSS_SELECTOR, "div.slick-track a[data-variants]")
    image_urls = []

    for element in image_elements:
        img_url = element.get_attribute('href')
        # Only include URLs that do not contain "medium" or "large"
        if "medium" not in img_url and "large" not in img_url:
            image_urls.append(img_url)

    return image_urls

def extract_zoom_image_urls(soup, base_url):
    """
    Extracts zoom image URLs from the page's HTML content.
    Args:
        soup (BeautifulSoup): Parsed HTML content.
        base_url (str): The base URL for resolving relative URLs.
    Returns:
        list: A list of zoom image URLs.
    """
    image_urls = []
    zoom_image_tags = soup.find_all('li', class_=lambda c: 'zoom' in c if c else False)
    
    for tag in zoom_image_tags:
        img = tag.find('img')
        if img:
            src = img.get('src')
            if src:
                full_url = urljoin(base_url, src)
                image_urls.append(full_url)
    
    return list(set(image_urls))  # Remove duplicates

def process_batch(urls_batch, batch_number):
    """
    Processes a batch of URLs to extract product details and image URLs.
    Args:
        urls_batch (DataFrame): The batch of URLs to process.
        batch_number (int): The current batch number.
    """
    results = []

    for index, row in urls_batch.iterrows():
        url = row['URL']
        if pd.isna(url):  # Skip empty rows
            continue

        page_no = row.get('Page No.', 'N/A')
        print(f"\nProcessing URL: {url} (Page No.: {page_no})")

        try:
            driver.get(url)
            print("URL opened successfully")

            # Wait until the product title is loaded
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'product-title-details')))
            print("Product title loaded")

            # Get page source and parse it with BeautifulSoup
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')

            # Extract product title
            product_title = soup.find('h1', class_='product-title-details').get_text(strip=True) if soup.find('h1', class_='product-title-details') else 'Product title not found'

            # Extract description
            description = 'Description not found'
            description_div = soup.find('div', id='product-description')
            if description_div:
                tab_content = description_div.find('div', class_='tab-content attributedescription')
                if tab_content:
                    for tag in tab_content(['script', 'style', 'video', 'iframe', 'noscript']):
                        tag.decompose()
                    for br in tab_content.find_all('br'):
                        br.replace_with('\n')
                    description = tab_content.get_text(separator="\n", strip=True)

            # Extract image URLs
            parsed_url = urlparse(url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            zoom_image_urls = extract_zoom_image_urls(soup, base_url)
            product_image_urls = extract_image_urls(url)

            # Append results to the list
            results.append({
                'Page No.': page_no,
                'URL': url,
                'Product Title': product_title,
                'Description': description,
                'Zoom Image URLs': ', '.join(zoom_image_urls) if zoom_image_urls else 'No zoom images found',
                'Product Image URLs': ', '.join(product_image_urls) if product_image_urls else 'No product images found'
            })

        except Exception as e:
            print(f"Error processing {url}: {e}")
            results.append({
                'Page No.': page_no,
                'URL': url,
                'Product Title': 'Error',
                'Description': 'Error',
                'Zoom Image URLs': 'Error',
                'Product Image URLs': 'Error'
            })

    # Save results to Excel
    results_df = pd.DataFrame(results)
    output_excel_path = f'D:\\SOWMYA\\python script\\extract Title_ID\\Input\\Toyworld\\Final Output\\output_urls_batch_{batch_number}.xlsx'
    results_df.to_excel(output_excel_path, index=False)
    print(f"Batch {batch_number} scraping complete. Results saved to {output_excel_path}")

# ---------------------------- Main Execution ---------------------------- #

try:
    excel_path = r'D:\SOWMYA\python script\extract Title_ID\Input\Toyworld\URLS.xlsx'
    urls_df = pd.read_excel(excel_path)
    urls_df.dropna(subset=['URL'], inplace=True)

    batch_size = 50
    num_batches = math.ceil(len(urls_df) / batch_size)

    for batch_number in range(num_batches):
        start_index = batch_number * batch_size
        end_index = min((batch_number + 1) * batch_size, len(urls_df))
        urls_batch = urls_df.iloc[start_index:end_index]
        print(f"\n--- Processing batch {batch_number + 1}/{num_batches} ---")
        process_batch(urls_batch, batch_number + 1)

except Exception as e:
    print(f"An error occurred: {e}")

finally:
    driver.quit()
    print("\nWebDriver closed.")
