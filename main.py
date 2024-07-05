# Import necessary libraries
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import requests
import os
from dotenv import load_dotenv

class ImageDownloader:
    def __init__(self, download_path):
        self.download_path = download_path
        self.driver = self._initialize_driver()
        # Load environment variables
        load_dotenv()
        self.email = os.getenv('EMAIL')
        self.password = os.getenv('PASSWORD')

    def _initialize_driver(self):
        # Setup Chrome options
        chrome_options = webdriver.ChromeOptions()
        prefs = {"download.default_directory": self.download_path}
        chrome_options.add_experimental_option("prefs", prefs)
        # Initialize and return Chrome driver
        return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    def sign_in(self, url):
        # Open the URL
        self.driver.get(url)
        # Wait for the login page to load
        time.sleep(2)
        # Login process
        self.driver.find_element(By.ID, "Email").send_keys(self.email)
        self.driver.find_element(By.ID, "Password").send_keys(self.password)
        self.driver.find_element(By.CSS_SELECTOR, "button.btn.btn-primary.btn-large").click()
        
        # Wait for the login process to complete
        time.sleep(5)
        
        # After successful login, find and store the session cookie
        cookies = self.driver.get_cookies()
        session_cookie = '; '.join([f"{cookie['name']}={cookie['value']}" for cookie in cookies if cookie['name'] in ['ASP.NET_SessionId', 'SessionKey']])
        self.session_cookie = session_cookie

    def get_image_details(self):
        # Find the ul element by its class name
        document_list = self.driver.find_element(By.CLASS_NAME, 'documents.clearfix')
        # Find all li elements within the ul
        items = document_list.find_elements(By.TAG_NAME, 'li')
        # Initialize an empty list to store the ids along with date, description, and amount
        item_details = []
        for item in items:
            # Assuming each item has an id attribute
            item_id = item.get_attribute('id')
            if item_id:
                # Extract date, description, and amount
                date = item.find_element(By.CSS_SELECTOR, '.label.date').text
                description = item.find_element(By.CSS_SELECTOR, '.description').get_attribute('title')
                amount = item.find_element(By.CSS_SELECTOR, '.label.amount').text
                # Append a dictionary with all details to the list
                item_details.append({
                    'id': item_id,
                    'date': date,
                    'description': description,
                    'amount': amount
                })
        # save the item details to a file
        with open('item_details.txt', 'w') as file:
            for item in item_details:
                file.write(f"{item['id']}, {item['date']}, {item['description']}, {item['amount']}\n")
        # Return a list of item ids
        return [item['id'] for item in item_details]
    
    def download_images_by_ids(self, item_ids):
        # Use the stored session_cookie for the GET request headers
        headers = {
            'Cookie': self.session_cookie
        }
        for item_id in item_ids:
            # Construct the URL with the current item_id
            download_url = f"https://mine.spiir.dk/bilag/download/{item_id}.jpg"
            # Send a GET request to the URL with the headers
            response = requests.get(download_url, headers=headers)
            # Check if the request was successful
            if response.status_code == 200:
                # validate that response Content-Type is image/jpeg
                if response.headers['Content-Type'] != 'image/jpeg':
                    print(f"Authentication failed for {download_url} - check that the session cookie is valid.")
                    continue
                # Define the path where the image will be saved
                file_path = f"{self.download_path}/{item_id}.jpg"
                # Open the file in binary write mode and save the content
                with open(file_path, 'wb') as file:
                    file.write(response.content)
                print(f"Downloaded {item_id}.jpg")
            else:
                print(f"ERROR: Failed to download {item_id}.jpg - status code {response.status_code}")

    def close_browser(self):
        self.driver.quit()

if __name__ == "__main__":
    # Configuration
    download_path = "bilag"
    url = "https://mine.spiir.dk/bilag"

    # Initialize downloader
    downloader = ImageDownloader(download_path)
    downloader.sign_in(url)
    item_ids = downloader.get_image_details()
    downloader.close_browser()
    downloader.download_images_by_ids(item_ids)