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
    response.html.render(timeout=20)

    # Parse the rendered HTML with BeautifulSoup
    soup = BeautifulSoup(response.html.html, 'html.parser')

    # Try to find the price container using the provided logic
    if '/in/' in url:
        price_container = soup.find('span', class_='as-pricepoint-mrp')
    else:
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
        print("Price found: ", clean_price)
        return clean_price
    print("Price not found")
    return None


# Function to update Mac prices
def update_mac_prices(data, region_codes, base_url, target_model_name = None):
    for model in data['hardware']['macs']:
        # if target_model_name and model['model'] != target_model_name:
        #     continue  # Skip this model if it doesn't match the target
        for config in model['configurations']:
            model_id = config['id']

            # Initialize pricing if it doesn't exist
            if 'pricing' not in config:
                config['pricing'] = []

            for country, codes in region_codes.items():
                # Skip if the price for this country already exists
                # if is_price_exists(config, country):
                #     continue

                country_code = codes.get("code")
                region_code_list = codes.get("mac", [])

                for region_code in region_code_list:
                    full_url = f"{base_url}/{country_code}/shop/product/{model_id}{region_code}"
                    print(f"Extracting Mac price for {country}, URL: {full_url}")

                    # Fetch the Mac price
                    price = fetch_mac_price(full_url)
                    config['pricing'].append({"country": country, "price": price or "Unavailable"})

    return data


# Function to update iPad prices with fallback for multiple region codes
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
                region_code_list = codes.get("ipad", [])  # Get the list of possible region codes for iPads

                price = None  # Initialize price as None
                for region_code in region_code_list:
                    full_url = f"{base_url}/{country_code}/shop/product/{model_id}{region_code}"
                    print(f"Extracting iPad price for {country} with region code {region_code}, URL: {full_url}")

                    # Fetch the iPad price
                    price = fetch_ipad_price(full_url)

                    if price:  # If a price is found, break the loop
                        break

                # Append the price (or "Unavailable" if no price was found) to the configuration
                config['pricing'].append({"country": country, "price": price or "Unavailable"})

    return data


# Function to fetch iPhone price with JavaScript rendering
def fetch_iphone_price_js(url):
    print(f"Fetching iPhone price from URL with JS rendering: {url}")

    # Start an HTML session
    session = HTMLSession()

    # Get the response from the URL
    response = session.get(url)

    # Render the JavaScript content
    response.html.render(timeout=10)

    # Parse the rendered HTML with BeautifulSoup
    soup = BeautifulSoup(response.html.html, 'html.parser')

    # Try to find the price container (similar logic to iPad fetching)
    if '/uk/' in url:
        # For the UK, the price might be stored differently
        price_container = soup.find('span', class_='price-point price-point-fullPrice-short')
    elif '/in/' in url:
        # For India, price may be under a different class
        price_container = soup.find('span', class_='as-pricepoint-mrp')
    else:
        # For other regions, use the default structure
        price_container = soup.find('span', class_='rc-prices-fullprice', attrs={'data-autom': 'full-price'})

    if price_container:
        raw_price = price_container.get_text(strip=True)
        clean_price = extract_price_and_currency(raw_price)
        print("Price found: ", clean_price)
        return clean_price

    print("Price not found.")
    return None


# Function to update iPhone prices using JavaScript rendering
def update_iphone_prices(data, region_codes, base_url, target_model_name=None):
    """
    Updates iPhone prices either for a specific model or for all models.

    :param data: The JSON data containing iPhone models and configurations.
    :param region_codes: The region codes for countries.
    :param base_url: The base URL for fetching prices.
    :param target_model_name: The specific model name to update prices for. If None, updates all models.
    :return: Updated data with prices.
    """

    # Loop through all iPhone models
    for model in data['hardware']['iphones']:
        # If a specific model name is provided, skip models that don't match
        if target_model_name and model['model'] != target_model_name:
            continue  # Skip this model if it doesn't match the target

        # Process configurations for the matching or all models
        for config in model['configurations']:
            # Get model IDs for different countries
            model_ids = config['modelIds']

            # Initialize pricing if it doesn't exist
            if 'pricing' not in config:
                config['pricing'] = []

            for country, codes in region_codes.items():
                # Skip if the price for this country already exists
                if is_price_exists(config, country):
                    continue

                country_code = codes.get("code")
                iphone_codes = codes.get("iphone", [])

                # Check if there's a matching model ID for the country
                for region_group, model_id in model_ids.items():
                    if country in region_group.split(', '):
                        for iphone_code in iphone_codes:
                            full_url = f"{base_url}/{country_code}/shop/product/{model_id}{iphone_code}"
                            print(f"Extracting iPhone price for {country}, URL: {full_url}")

                            # Fetch the iPhone price using JS rendering
                            price = fetch_iphone_price_js(full_url)
                            config['pricing'].append({"country": country, "price": price or "Unavailable"})

    return data

# Function to fetch watch price
def fetch_watch_price(url):
    print(f"Fetching Watch price from URL with JS rendering: {url}")

    # Start an HTML session
    session = HTMLSession()

    # Get the response from the URL
    response = session.get(url)

    # Render the JavaScript content
    response.html.render(timeout=10)

    # Parse the rendered HTML with BeautifulSoup
    soup = BeautifulSoup(response.html.html, 'html.parser')

    # Try to find the price container (similar logic to iPad fetching)

    # For other regions, use the default structure
    price_container = soup.find('span', class_='rc-prices-fullprice', attrs={'data-autom': 'full-price'})

    if price_container:
        raw_price = price_container.get_text(strip=True)
        clean_price = extract_price_and_currency(raw_price)
        print("Price found: ", clean_price)
        return clean_price

    print("Price not found.")
    return None

# Function to update Watch prices
def update_watch_prices(data, region_codes, base_url):
    for model in data['hardware']['watches']:
        for config in model['configurations']:
            model_ids = config['modelIds']

            # Clear the pricing array before fetching new prices
            config['pricing'] = []

            for country, codes in region_codes.items():
                country_code = codes.get("code")

                # Get the link for the current country from modelIds
                link = None
                for region_group, model_id in model_ids.items():
                    if country in region_group.split(', '):
                        link = model_id
                        break
                    else:
                        continue

                if link:
                    # Construct the full URL
                    full_url = f"{base_url}/{country_code}/shop/buy-watch/apple-watch{link}"
                    print(f"Extracting Watch price for {country}, URL: {full_url}")

                    # Fetch the Watch price
                    price = fetch_watch_price(full_url)

                    # Append the price (or "Unavailable" if no price was found) to the configuration
                    config['pricing'].append({"country": country, "price": price or "Unavailable"})

    return data

# Function to update iPhone prices using JavaScript rendering
# Function to update AirPods prices
def update_airpods_prices(data, region_codes, base_url):
    for model in data['hardware']['airpods']:
        for config in model['configurations']:
            model_id = config['id']

            # Clear the pricing array before fetching new prices
            config['pricing'] = []

            for country, codes in region_codes.items():
                country_code = codes.get("code")

                # Construct the full URL
                full_url = f"{base_url}/{country_code}/shop/product/{model_id}"
                print(f"Extracting AirPods price for {country}, URL: {full_url}")

                # Fetch the AirPods price
                price = fetch_watch_price(full_url)

                # Append the price (or "Unavailable" if no price was found) to the configuration
                config['pricing'].append({"country": country, "price": price or "Unavailable"})

    return data

# Function to remove "Unavailable" prices if valid prices exist for the same country
def clean_pricing_data(data):
    for model in data['hardware']['macs']:
        for config in model['configurations']:
            # Track countries with valid prices
            country_valid_price = {}

            # First pass: check for valid prices and mark the country
            for price_entry in config['pricing']:
                if price_entry['price'] != "Unavailable":
                    country_valid_price[price_entry['country']] = True

            # Second pass: remove "Unavailable" entries if valid prices exist
            cleaned_pricing = [
                price_entry for price_entry in config['pricing']
                if price_entry['price'] != "Unavailable" or not country_valid_price.get(price_entry['country'])
            ]

            # Ensure at least one price is kept, even if all are "Unavailable"
            if len(cleaned_pricing) == 0 and len(config['pricing']) > 0:
                cleaned_pricing = config['pricing']

            # Update the configuration with cleaned pricing
            config['pricing'] = cleaned_pricing

    return data


# Function to update all prices (Macs, iPads, iPhones)
def update_all_prices(data):
    region_codes = {
        "USA": {"code": "", "mac": ["LL/A"], "ipad": ["LL/A"], "iphone": ["LL/A"], "airpods":["LL/A"]},
        "Canada": {"code": "ca", "mac": ["LL/A", "VC/A"], "ipad": ["CL/A", "VC/A"], "iphone": ["C/A", "VC/A"], "airpods":["AM/A"]},
        "UK": {"code": "uk", "mac": ["B/A"], "ipad": ["NF/A", "B/A"], "iphone": ["QN/A", "ZD/A", "B/A"], "airpods":["ZM/A"]},
        "Germany": {"code": "de", "mac": ["D/A"], "ipad": ["NF/A", "FD/A"], "iphone": ["D/A", "ZD/A"], "airpods":["LL/A"]},
        "India": {"code": "in", "mac": ["HN/A"], "ipad": ["HN/A"], "iphone": ["HN/A"], "airpods":["HN/A"]},
        "France": {"code": "fr", "mac": ["NF/A", "FN/A"], "ipad": ["NF/A"], "iphone": ["ZD/A"], "airpods":["ZM/A"]},
        "Japan": {"code": "jp", "mac": ["J/A"], "ipad": ["J/A"], "iphone": ["J/A"], "airpods":["J/A"]},
        "Vietnam": {"code": "vn", "mac": ["SA/A"], "ipad": ["ZA/A"], "iphone": ["VN/A"], "airpods":["ZP/A"]},
    }

    base_url = "https://www.apple.com"

    # Update Mac prices
    # data = update_mac_prices(data, region_codes, base_url)
    #
    # # Update iPad prices
    # data = update_ipad_prices(data, region_codes, base_url)

    # Set the model to update (None for all models)
    # target_model_name = "iPhone 14"  # Change this to "iPhone 14 Plus" if you want to update that model only

    # # Update iPhone prices
    # data = update_iphone_prices(data, region_codes, base_url, target_model_name)

    # data = update_watch_prices(data, region_codes, base_url)

    data = update_airpods_prices(data, region_codes, base_url)

    # Clean pricing data to remove "Unavailable" entries
    data = clean_pricing_data(data)

    return data


# Running the price update
if __name__ == "__main__":
    with open('../data/data.json', 'r') as f:
        data = json.load(f)

    # Update both Mac, iPad, and iPhone prices
    updated_data = update_all_prices(data)

    # Save the updated data back to the JSON file
    with open('../data/data.json', 'w') as f:
        json.dump(updated_data, f, separators=(',', ':'), indent=0)

    print("Prices updated successfully.")