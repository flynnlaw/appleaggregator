import json


# Function to clean up 'Unavailable' entries if valid prices exist for the same country
def clean_up_unavailable_entries(data):
    for device_type in data['hardware']:
        for model in data['hardware'][device_type]:
            for config in model['configurations']:

                # Group pricing entries by country
                country_prices = {}
                for price_entry in config['pricing']:
                    country = price_entry['country']
                    if country not in country_prices:
                        country_prices[country] = []
                    country_prices[country].append(price_entry)

                # Clean up: if a valid price exists, remove "Unavailable" for that country
                cleaned_pricing = []
                for country, prices in country_prices.items():
                    # Check if any valid price exists (non-"Unavailable")
                    valid_prices = [p for p in prices if p['price'] != "Unavailable"]

                    if valid_prices:
                        # If valid prices exist, add only those and ignore "Unavailable"
                        cleaned_pricing.extend(valid_prices)
                    else:
                        # If no valid prices exist, keep the "Unavailable" entry
                        cleaned_pricing.extend(prices)

                # Update the config's pricing with the cleaned entries
                config['pricing'] = cleaned_pricing

    return data


# Main function to load, clean, and save the JSON data
def remove_unavailable_prices(file_path):
    # Load the JSON data
    with open(file_path, 'r') as f:
        data = json.load(f)

    # Clean up the "Unavailable" entries
    updated_data = clean_up_unavailable_entries(data)

    # Save the cleaned data back to the JSON file
    with open(file_path, 'w') as f:
        json.dump(updated_data, f, separators=(',', ':'), indent=2)

    print("Cleaned up 'Unavailable' entries successfully.")


# Example usage:
if __name__ == "__main__":
    file_path = '../data/data.json'  # Change this path as needed
    remove_unavailable_prices(file_path)