import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import math
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urljoin, urlparse

# ---------------------------- Configuration ---------------------------- #

# Set up Selenium options
options = Options()
options.headless = True  # Run in headless mode (without opening a browser window)
options.add_argument('--disable-gpu')  # Disable GPU acceleration
options.add_argument('--no-sandbox')   # Bypass OS security model
options.add_argument('--disable-dev-shm-usage')  # Overcome limited resource problems

# Path to the ChromeDriver executable
chromedriver_path = "D:\\SOWMYA\\python script\\extract Title_ID\\Input\\CHROMDRIVE\\chromedriver-win64\\chromedriver.exe"

# Initialize the WebDriver service with headless option
service = Service(chromedriver_path)
driver = webdriver.Chrome(service=service, options=options)

# Define a wait object with a timeout of 30 seconds
wait = WebDriverWait(driver, 30)

# ---------------------------- Functions ---------------------------- #

def extract_image_urls(soup, base_url):
    """
    Extracts all image URLs from the BeautifulSoup-parsed HTML within <figure> tags.
    
    Args:
        soup (BeautifulSoup): Parsed HTML content.
        base_url (str): The base URL of the page for constructing absolute URLs.
    
    Returns:
        list: A list of all image URLs found within <figure> tags.
    """
    image_urls = []
    figure_tags = soup.find_all('figure', attrs={'data-index': True})
    
    for tag in figure_tags:
        img = tag.find('img', itemprop='image')
        if img:
            url = img.get('src')
            if url:
                full_url = urljoin(base_url, url)
                image_urls.append(full_url)
    
    # Remove duplicates by converting to a set and back to a list
    unique_image_urls = list(set(image_urls))
    return unique_image_urls

def process_batch(urls_batch, batch_number):
    """
    Processes a batch of URLs, extracting product details and image URLs.
    
    Args:
        urls_batch (DataFrame): A batch of URLs to process.
        batch_number (int): The current batch number.
    """
    results = []

    for index, row in urls_batch.iterrows():
        url = row['URL']
        page_no = row.get('Page No.', 'N/A')
        print(f"\nProcessing URL: {url} (Page No.: {page_no})")

        try:
            # Open the webpage
            driver.get(url)
            print("URL opened successfully")

            # Wait until the product title is present to ensure the page has loaded
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'product-header')))
            print("Product title loaded")

            # Get the page source
            page_source = driver.page_source

            # Parse the HTML content using BeautifulSoup
            soup = BeautifulSoup(page_source, 'html.parser')

            # Extract Product Title
            product_element = soup.find('h1', class_='product-header', attrs={'data-property': 'title'})
            product_title = product_element.get_text(strip=True) if product_element else 'Product title not found'

            # Find the section where the description is stored
            description_section = soup.find('section', id='description', class_='tabcontent active')
            if description_section:

                # Extract paragraphs and list items
                paragraphs = description_section.find_all(['p', 'strong'])  # Include <strong> within <p> as well
                description_items = description_section.find_all('li')

                # Extract text for paragraphs and list items
                description_p = '\n'.join([para.get_text(separator=" ", strip=True) for para in paragraphs])
                description_li = '\n'.join([f"• {item.get_text(strip=True)}" for item in description_items])

                # Combine paragraphs first, followed by list items with a line break
                description = f"{description_p}\n\n{description_li}".strip()
            else:
                description = 'Description not found'
                
            # Extract Image URLs
            parsed_url = urlparse(url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            image_urls = extract_image_urls(soup, base_url)

            # Append the result to the list
            results.append({
                'Page No.': page_no,
                'URL': url,
                'Product Title': product_title,
                'Description': description,
                'Image URLs': ', '.join(image_urls) if image_urls else 'Image URLs not found'
            })

            # Optional: print the product title and number of images extracted for each URL
            print(f'Product Title: {product_title}')
            print(f'Extracted {len(image_urls)} image(s)')

        except Exception as e:
            print(f"An error occurred while processing URL: {url}")
            print(f"Error: {e}")
            results.append({
                'Page No.': page_no,
                'URL': url,
                'Product Title': 'Error',
                'Description': 'Error',
                'Image URLs': 'Error'
            })

    # Convert the results to a DataFrame
    results_df = pd.DataFrame(results)

    # Save the results to a new Excel file
    output_excel_path = f'D:\\SOWMYA\\python script\\extract Title_ID\\Input\\Appliance Plus\\Final Output\\output_urls_batch_{batch_number}.xlsx'
    results_df.to_excel(output_excel_path, index=False)

    print(f"\nBatch {batch_number} scraping complete. Results saved to: {output_excel_path}")

# ---------------------------- Main Execution ---------------------------- #

try:
    # Read URLs from the Excel file
    excel_path = r'D:\SOWMYA\python script\extract Title_ID\Input\Appliance Plus\URLS.xlsx'
    urls_df = pd.read_excel(excel_path)

    # Define batch size
    batch_size = 25  # Adjust the batch size as necessary

    # Calculate the number of batches
    num_batches = math.ceil(len(urls_df) / batch_size)

    print(f"Total URLs to process: {len(urls_df)}")
    print(f"Batch size: {batch_size}")
    print(f"Number of batches: {num_batches}")

    for batch_number in range(num_batches):
        start_index = batch_number * batch_size
        end_index = min((batch_number + 1) * batch_size, len(urls_df))
        urls_batch = urls_df.iloc[start_index:end_index]

        print(f"\n--- Processing batch {batch_number + 1}/{num_batches} ---")
        process_batch(urls_batch, batch_number + 1)

except Exception as main_e:
    print("An error occurred during the scraping process.")
    print(f"Error: {main_e}")

finally:
    # Quit the driver
    driver.quit()
    print("\nWebDriver closed.")
