import requests
import json

# Data structure to store regions and model IDs
regions = {"ids": []}


def check_url(url):
    """Check if the URL returns a 404 status. If it doesn't, return True."""
    print(f"Checking URL: {url}")
    response = requests.get(url)

    if response.status_code == 404:
        print(f"URL not found (404): {url}")
        return False
    else:
        print(f"Valid URL: {url}")
        return True


if __name__ == "__main__":
    region_codes = {
        "USA": {"code": "", "mac": ["LL/A"], "ipad": ["LL/A"], "iphone": ["LL/A"], "watch":[], "airpods":["LL/A"]},
        "Canada": {"code": "ca", "mac": ["LL/A"], "ipad": ["CL/A", "VC/A"], "iphone": ["C/A", "VC/A"], "watch":[], "airpods":["AM/A"]},
        "UK": {"code": "uk", "mac": ["B/A"], "ipad": ["NF/A", "B/A"], "iphone": ["QN/A", "ZD/A", "B/A"], "watch":[], "airpods":["ZM/A"]},
        "Germany": {"code": "de", "mac": ["D/A"], "ipad": ["NF/A", "FD/A"], "iphone": ["D/A", "ZD/A"], "watch":[], "airpods":["ZM/A"]},
        "India": {"code": "in", "mac": ["HN/A"], "ipad": ["HN/A"], "iphone": ["HN/A"], "watch":[], "airpods":["HN/A"]},
        "France": {"code": "fr", "mac": ["NF/A"], "ipad": ["NF/A"], "iphone": ["ZD/A"], "watch":[], "airpods":["ZM/A"]},
        "Japan": {"code": "jp", "mac": ["J/A"], "ipad": ["J/A"], "iphone": ["J/A"], "watch":[], "airpods":["J/A"]},
        "Vietnam": {"code": "vn", "mac": ["SA/A"], "ipad": ["ZA/A"], "iphone": ["VN/A"], "watch":[], "airpods":["ZP/A"]},
    }

    base_url = "https://www.apple.com"
    model_ids = ["MTJV3", "MUYG3"]

    # Loop through model IDs and regions to construct URLs and check if they are valid
    for model_id in model_ids:
        for region, codes in region_codes.items():
            internet_code = codes.get("code")
            region_code_list = codes.get("airpods", [])

            for region_code in region_code_list:
                full_url = f"{base_url}/{internet_code}/shop/product/{model_id}{region_code}"

                # Check if the URL is valid (not 404)
                if check_url(full_url):
                    # Append the country and model ID to the regions list
                    regions["ids"].append({
                        "country": region,
                        "id": model_id
                    })

    # Write the valid region and model IDs to a JSON file
    with open("iphone_models.json", "w") as file:
        json.dump(regions, file, indent=4)

    print("Valid iPhone model IDs have been written to iphone_models.json")