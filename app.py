from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import threading
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
from time import sleep
import re
import requests
import openpyxl
from webdriver_manager.chrome import ChromeDriverManager
import os
from io import BytesIO

app = Flask(__name__)
CORS(app)

class GoogleMapsScraper:
    def __init__(self):
        self.scraped_data = []
        self.data_count = 0
        self.scraping_flag = True
        self.stop_flag = False
        self.current_status = "Ready to go..."

    def generate_combinations(self, keywords, locations):
        keywords = [k.strip() for k in keywords.split(',') if k.strip()]
        locations = [l.strip() for l in locations.split(',') if l.strip()]

        if not keywords or not locations:
            return []

        return [(k, l) for k in keywords for l in locations]

    def scrape_google_maps(self, combination):
        keyword, location = combination
        url = "https://www.google.com/maps"
        options = webdriver.ChromeOptions()
        options.add_argument("--window-size=1920x1080")
        options.add_argument("--headless")

        driver_path = ChromeDriverManager().install()
        chrome_service = webdriver.chrome.service.Service(driver_path)
        
        with webdriver.Chrome(service=chrome_service, options=options) as driver:
            try:
                self.current_status = f"Scraping {keyword} in {location}..."

                driver.get(url)
                driver.implicitly_wait(5)

                search_input = driver.find_element(By.NAME, "q")
                search_input.send_keys(f"{keyword} in {location}")
                search_input.send_keys(Keys.RETURN)

                while self.scraping_flag and not self.stop_flag:
                    for iteration in range(2):
                        try:
                            WebDriverWait(driver, 20).until(
                                EC.presence_of_element_located((By.CLASS_NAME, "Nv2PK"))
                            )

                            result_locator = (By.CLASS_NAME, 'Nv2PK')
                            result_elements = WebDriverWait(driver, 20).until(
                                EC.presence_of_all_elements_located(result_locator)
                            )

                            i = 0
                            while i < len(result_elements) and self.scraping_flag and not self.stop_flag:
                                try:
                                    driver.execute_script("arguments[0].scrollIntoView();", result_elements[i])
                                    result_elements[i].click()
                                    sleep(2)

                                    name = self.extract_location_info(driver, "DUwDvf", "class")
                                    address = self.extract_location_info(driver, "rogA2c", "class")
                                    
                                    if not any(existing_data["NAME"] == name for existing_data in self.scraped_data):
                                        category = self.extract_location_info(driver, "DkEaL", "class")
                                        phone = self.extract_phone_number(driver)
                                        web_url = self.extract_web_url(driver) 
                                        ratings = self.extract_ratings(driver)
                                        total_reviews = self.extract_total_reviews(driver)
                                        timings = self.extract_available_timings(driver)
                                        email_id = self.extract_emails_from_web_url(web_url)

                                        data = {
                                            "NAME": name,
                                            "ADDRESS": address,
                                            "DEPARTMENT": category,
                                            "PHONE": phone,
                                            "URL": web_url,
                                            "RATINGS": ratings,
                                            "TOTAL_REVIEWS": total_reviews,
                                            "AVAILABLE_TIMINGS": timings,
                                            "EMAIL ID": email_id,
                                        }

                                        self.scraped_data.append(data)
                                        self.data_count += 1
                                        self.current_status = f"Scraped {self.data_count} items..."

                                    WebDriverWait(driver, 20).until(
                                        EC.presence_of_element_located((By.CLASS_NAME, "Nv2PK"))
                                    )

                                    result_locator = (By.CLASS_NAME, 'Nv2PK')
                                    result_elements = WebDriverWait(driver, 20).until(
                                        EC.presence_of_all_elements_located(result_locator)
                                    )

                                except (NoSuchElementException, TimeoutException, StaleElementReferenceException):
                                    i += 1
                                    continue

                                i += 1

                            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                            sleep(5)

                        except TimeoutException:
                            break
                        else:
                            WebDriverWait(driver, 30).until(
                                EC.presence_of_element_located((By.CLASS_NAME, "Nv2PK"))
                            )

            except Exception as e:
                self.current_status = f"Error: {e}"
                print(f"Error: {e}")

            finally:
                self.current_status = "Scraping completed."
                driver.quit()

    def extract_location_info(self, driver, identifier, locator_type="class"):
        try:
            element = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((self.get_locator_strategy(locator_type), identifier))
            )
            return element.text.strip() if element.text else "Not available"
        except (NoSuchElementException, TimeoutException, StaleElementReferenceException):
            return "NA"

    def extract_phone_number(self, driver):
        try:
            phone_element = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'button[aria-label^="Phone:"] div.Io6YTe'))
            )
            return phone_element.text
        except (NoSuchElementException, TimeoutException, StaleElementReferenceException):
            return "__________"

    def extract_web_url(self, driver):
        try:
            web_url_element = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'a[data-item-id="authority"]'))
            )
            web_url = web_url_element.get_attribute('href')
            return web_url if web_url else "Not available"
        except (TimeoutException, NoSuchElementException, StaleElementReferenceException):
            return "NA"

    def extract_ratings(self, driver):
        try:
            rating_element = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div.F7nice span[aria-hidden="true"]'))
            )
            return rating_element.text
        except (NoSuchElementException, TimeoutException, StaleElementReferenceException):
            return "NA"

    def extract_total_reviews(self, driver):
        try:
            total_reviews_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div.jANrlb span'))
            )
            return total_reviews_element.text
        except (NoSuchElementException, TimeoutException, StaleElementReferenceException):
            return "NA"

    def get_locator_strategy(self, locator_type):
        if locator_type == "class":
            return By.CLASS_NAME
        elif locator_type == "xpath":
            return By.XPATH
        elif locator_type == "css":
            return By.CSS_SELECTOR
        else:
            raise ValueError("Invalid locator_type. Use 'class', 'xpath', or 'css'.")
        
    def extract_emails_from_web_url(self, web_url):
        try:
            if web_url == "NA":
                return []
                
            response = requests.get(web_url, timeout=10)
            response.raise_for_status()
            html_content = response.text

            email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            matches = re.findall(email_regex, html_content)
            return ", ".join(matches) if matches else "NA"
        except requests.RequestException as e:
            print(f"Error fetching HTML content: {e}")
            return "NA"

    def extract_available_timings(self, driver):
        try:
            timings_button = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'OMl5r'))
            )
            timings_button.click()

            timings_table = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'eK4R0e'))
            )

            timings_rows = timings_table.find_elements(By.CLASS_NAME, 'y0skZc')
            timings_data = []

            for row in timings_rows:
                day_element = row.find_element(By.CLASS_NAME, 'ylH6lf')
                day = day_element.text.strip()

                timings_element = row.find_element(By.CLASS_NAME, 'mxowUb')
                timings_list = timings_element.find_elements(By.CLASS_NAME, 'G8aQO')

                timings_info = f"{day}: {' '.join([timings.text.strip() for timings in timings_list])}"
                timings_data.append(timings_info)

            return "  ".join(timings_data)
        except (NoSuchElementException, TimeoutException, StaleElementReferenceException):
            return "NA"

scraper = GoogleMapsScraper()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start_scraping():
    data = request.json
    keywords = data.get('keywords', '')
    locations = data.get('locations', '')
    
    # Reset scraper state
    scraper.scraped_data = []
    scraper.data_count = 0
    scraper.scraping_flag = True
    scraper.stop_flag = False
    
    # Generate combinations and start scraping in a new thread
    combinations = scraper.generate_combinations(keywords, locations)
    if not combinations:
        return jsonify({"error": "Please provide valid keywords and locations."}), 400
    
    for combination in combinations:
        threading.Thread(target=scraper.scrape_google_maps, args=(combination,)).start()
    
    return jsonify({"message": "Scraping started successfully"})

@app.route('/stop', methods=['POST'])
def stop_scraping():
    scraper.stop_flag = True
    scraper.scraping_flag = False
    return jsonify({"message": "Scraping stopped"})

# @app.route('/download', methods=['GET'])
# def download_results():
#     try:
#         # Create a DataFrame from the scraped data
#         df = pd.DataFrame(scraper.scraped_data)
        
#         # Create an in-memory Excel file
#         output = BytesIO()
#         writer = pd.ExcelWriter(output, engine='openpyxl')
#         df.to_excel(writer, index=False, sheet_name='Scraped Data')
#         writer.close()
#         output.seek(0)
        
#         return send_file(
#             output,
#             mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
#             as_attachment=True,
#             download_name='google_maps_data.xlsx'
#         )
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500



@app.route('/download', methods=['GET'])
def download_results():
    try:
        # Get current data (don't wait for scraping to complete)
        current_data = scraper.scraped_data
        
        if not current_data:
            return jsonify({"error": "No data available to download"}), 400
        
        # Create a DataFrame from the current data
        df = pd.DataFrame(current_data)
        
        # Create an in-memory Excel file
        output = BytesIO()
        writer = pd.ExcelWriter(output, engine='openpyxl')
        df.to_excel(writer, index=False, sheet_name='Scraped Data')
        writer.close()
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='google_maps_data.xlsx'
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500




@app.route('/status', methods=['GET'])
def get_status():
    return jsonify({
        "status": scraper.current_status,
        "count": scraper.data_count,
        "data": scraper.scraped_data[:]  # Return last 10 items for display
    })


@app.route('/get_data', methods=['GET'])
def get_current_data():
    return jsonify({
        "data": scraper.scraped_data,
        "count": scraper.data_count
    })



if __name__ == '__main__':
    app.run()
