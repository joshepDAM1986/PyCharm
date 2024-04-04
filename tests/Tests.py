import requests

url = "https://api.holded.com/api/invoicing/v1/products"

headers = {
    "accept": "application/json",
    "key": "43b4f1738a6200eb59d19b07a3077977"
}

response = requests.get(url, headers=headers)

product_list = response.json()

print (product_list)
