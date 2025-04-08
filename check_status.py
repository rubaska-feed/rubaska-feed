import requests
import json
from dotenv import load_dotenv
load_dotenv()

SHOP_URL = "676c64.myshopify.com"

API_VERSION = "2023-10"

HEADERS = {
    "Content-Type": "application/json",
    "X-Shopify-Access-Token": os.environ.get("SHOPIFY_TOKEN")
}

def check_bulk_status():
    url = f"https://{SHOP_URL}/admin/api/{API_VERSION}/graphql.json"
    query = {
        "query": """
        {
          currentBulkOperation {
            id
            status
            url
            errorCode
            createdAt
            completedAt
            objectCount
            fileSize
          }
        }
        """
    }
    res = requests.post(url, headers=HEADERS, json=query)
    data = res.json()
    print(json.dumps(data, indent=2))

check_bulk_status()

