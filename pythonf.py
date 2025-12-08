# Amazon Smart Watch Scraper
# Modified to include PostgreSQL database integration like the Amazon scraper.

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from datetime import datetime

#  Added imports for DB integration (from your Amazon script)
from pythondb import create_db_connection, insert_products, create_products_table, clear_products_table


# =========================
#  Database Setup Section
# =========================
conn, cursor = create_db_connection(
    host="localhost",
    database="Amazondata2",       # You can change DB name if you prefer
    user="Sanskar11",
    password="SANskar@@@001"
)

if conn and cursor:
    print(" Database connection successful.")
    create_products_table(cursor, conn)
    clear_products_table(cursor, conn)   # <--- ADD THIS LINE
else:
    print(" Database connection failed.")
    exit()

# =========================
#  Selenium Functions
# =========================
def setup_driver():
    service = Service(executable_path="chromedriver.exe")
    driver = webdriver.Chrome(service=service)
    driver.maximize_window()
    return driver

def search_amazon(driver, search_term):
    driver.get("https://www.amazon.com/")
    print("Amazon page loaded successfully.")
    print(f"Current URL: {driver.current_url}")

    try:
        search_box = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID,"twotabsearchtextbox")))
    except:
        try:
            search_box = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.NAME, "field-keywords")))
        except:
            print("Search box not found. Page might have changed.")
            driver.quit()
            raise

    search_box.clear()
    search_box.send_keys(search_term + Keys.ENTER)
    print(f" Searching for '{search_term}'...")

    WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.XPATH, "//div[@data-component-type='s-search-result']"))
    )

def scrape_page(driver, page):
    print(f"\nScraping Page {page}...")
    products = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.XPATH, "//div[@data-component-type='s-search-result']"))
    )
    print(f"Found {len(products)} products on page {page}.")

    page_data = []
    for idx, product in enumerate(products, start=1):
        try:
            link_elem = product.find_element(By.CSS_SELECTOR, "a.a-link-normal.a-text-normal")
            link = link_elem.get_attribute("href")
            name = link_elem.text.strip() or "N/A"
        except NoSuchElementException:
            name, link = "N/A", "N/A"

        try:
            price_whole = product.find_element(By.CLASS_NAME, "a-price-whole").text.replace(',', '')
            price_fraction = product.find_element(By.CLASS_NAME, "a-price-fraction").text
            price = f"${price_whole}.{price_fraction}"
        except NoSuchElementException:
            price = "N/A"

        try:
            image = product.find_element(By.CSS_SELECTOR, "img").get_attribute("src")
        except NoSuchElementException:
            image = "N/A"

        product_dict = {
            "product_name": name,
            "product_price": price,
            "page_number": page,
            "timestamp": datetime.now(),  #  Added timestamp like in Myntra script
            "product_link": link,
            "product_image": image
            
        }

        page_data.append(product_dict)
        print(f"Product {idx} on Page {page}: {product_dict}")

    print(f"Page {page} done — collected {len(page_data)} items.")
    return page_data

def navigate_to_page(driver, page):
    if page > 1:
        current_url = driver.current_url
        if "&page=" in current_url:
            next_page_url = current_url.split("&page=")[0] + f"&page={page}"
        else:
            next_page_url = current_url + f"&page={page}"
        driver.get(next_page_url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, "//div[@data-component-type='s-search-result']"))
        )

# =========================
#  Main Execution
# =========================
def main():
    search_term = input("Enter the search term (e.g., 'Smart Watches'): ")
    try:
        page_limit = int(input("Enter the number of pages to scrape (e.g., 7): "))
        if page_limit < 1:
            raise ValueError("Page limit must be at least 1.")
    except ValueError as e:
        print(f"Invalid input for page limit: {e}")
        return

    driver = setup_driver()

    try:
        search_amazon(driver, search_term)
        data = []

        for page in range(1, page_limit + 1):
            navigate_to_page(driver, page)
            page_data = scrape_page(driver, page)
            data.extend(page_data)

        print(f"\nTotal collected products: {len(data)}")

        #  Store in Database (added section)
        try:
            insert_products(cursor, conn, data)
            print(f" All '{search_term}' products stored successfully in DB.")
        except Exception as e:
            print(f" Error while inserting into DB: {e}")

    finally:
        cursor.close()
        conn.close()
        driver.quit()
        print("Session Completed and Database Closed.")

if __name__ == "__main__":
    main()
