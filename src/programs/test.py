import re  # Use the regex module for Unicode property escapes
import requests
from bs4 import BeautifulSoup
from requests_html import HTMLSession
import json
from price_parser import Price


# Function to clean the price format using regex
def extract_price_and_currency(raw_price):
    match = Price.fromstring(raw_price)
    if match.currency == "đ" or match.currency == "円":  # Extract the matched price with commas and decimal points
        return f"{match.amount}{match.currency}"
    else:
        return f"{match.currency}{match.amount}"


# Function to check if a price for the country already exists in the configuration
def is_price_exists(config, country):
    for price_entry in config.get('pricing', []):
        if price_entry.get('country') == country:
            return True
    return False


# Function to fetch the iPad price with JavaScript rendering
def fetch_ipad_price(url):
    print(f"Fetching iPad price from URL: {url}")

    # Start an HTML session
    session = HTMLSession()

    # Get the response from the URL
    response = session.get(url)

    # Render the JavaScript content (wait=2 gives time for JS to load, can be adjusted)
    response.html.render(timeout=10)

    # Parse the rendered HTML with BeautifulSoup
    soup = BeautifulSoup(response.html.html, 'html.parser')

    # Try to find the price container using the provided logic
    price_container = soup.find('span', class_='rc-prices-fullprice', attrs={'data-autom': 'full-price'})

    # If the price is found, extract and clean it
    if price_container:
        raw_price = price_container.get_text(strip=True)
        inbetween_price = raw_price.replace('\xa0', '.')
        clean_price = extract_price_and_currency(inbetween_price)
        print(f"Found price: {clean_price}")
        return clean_price

    print("Price not found.")
    return None


# Function to fetch Mac price (no rendering required)
def fetch_mac_price(url):
    print(f"Fetching Mac price from URL: {url}")
    response = requests.get(url)

    if response.status_code != 200:
        return None

    # Parse the HTML response
    soup = BeautifulSoup(response.content, 'html.parser')
    price_tag = soup.find('span', class_='rc-prices-fullprice', attrs={'data-autom': 'full-price'})

    if price_tag:
        raw_price = price_tag.text.strip()
        clean_price = extract_price_and_currency(raw_price)
        return clean_price
    return None


# Function to update Mac prices
def update_mac_prices(data, region_codes, base_url):
    for model in data['hardware']['macs']:
        for config in model['configurations']:
            model_id = config['id']

            # Initialize pricing if it doesn't exist
            if 'pricing' not in config:
                config['pricing'] = []

            for country, codes in region_codes.items():
                # Skip if the price for this country already exists
                if is_price_exists(config, country):
                    continue

                country_code = codes.get("code")
                region_code = codes.get("mac")

                if region_code:
                    full_url = f"{base_url}/{country_code}/shop/product/{model_id}{region_code}"
                    print(f"Extracting Mac price for {country}, URL: {full_url}")

                    # Fetch the Mac price
                    price = fetch_mac_price(full_url)
                    config['pricing'].append({"country": country, "price": price or "Unavailable"})

    return data


# Function to update iPad prices
def update_ipad_prices(data, region_codes, base_url):
    for model in data['hardware']['ipads']:
        for config in model['configurations']:
            model_id = config['id']

            # Initialize pricing if it doesn't exist
            if 'pricing' not in config:
                config['pricing'] = []

            for country, codes in region_codes.items():
                # Skip if the price for this country already exists
                if is_price_exists(config, country):
                    continue

                country_code = codes.get("code")
                region_code = codes.get("ipad")

                if region_code:
                    full_url = f"{base_url}/{country_code}/shop/product/{model_id}{region_code}"
                    print(f"Extracting iPad price for {country}, URL: {full_url}")

                    # Fetch the iPad price
                    price = fetch_ipad_price(full_url)
                    print("Price: ", price)
                    config['pricing'].append({"country": country, "price": price or "Unavailable"})

    return data


# Function to update all prices (Macs and iPads)
def update_all_prices(data):
    region_codes = {
        "USA": {"code": "", "mac": "LL/A", "ipad": "LL/A"},
        "Canada": {"code": "ca", "mac": "LL/A", "ipad": "CL/A"},
        "UK": {"code": "uk", "mac": "B/A", "ipad": "NF/A"},
        "Germany": {"code": "de", "mac": "D/A", "ipad": "NF/A"},
        "India": {"code": "in", "mac": "HN/A", "ipad": "HN/A"},
        "France": {"code": "fr", "mac": "NF/A", "ipad": "NF/A"},
        "Japan": {"code": "jp", "mac": "J/A", "ipad": "J/A"},
        "Vietnam": {"code": "vn", "mac": "SA/A", "ipad": "ZA/A"},
    }

    base_url = "https://www.apple.com"

    # Update Mac prices
    data = update_mac_prices(data, region_codes, base_url)

    # Update iPad prices
    data = update_ipad_prices(data, region_codes, base_url)

    return data


# Running the price update
if __name__ == "__main__":
    with open('../data/data.json', 'r') as f:
        data = json.load(f)

    # Update both Mac and iPad prices
    updated_data = update_all_prices(data)

    # Save the updated data back to the JSON file
    with open('../data/data.json', 'w') as f:
        json.dump(updated_data, f, separators=(',', ':'), indent=0)

    print("Prices updated successfully.")