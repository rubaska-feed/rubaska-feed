import requests
import os
import time
import json
from dotenv import load_dotenv

load_dotenv()

SHOP_URL = "676c64.myshopify.com"
API_VERSION = "2023-10"

HEADERS = {
    "Content-Type": "application/json",
    "X-Shopify-Access-Token": os.environ.get("SHOPIFY_TOKEN")
}

bulk_query = """
{
  products{
    edges {
      node {
        id
        title
        handle
        productType
        vendor
        bodyHtml
        tags
        status
        variants(first: 100) {
          edges {
            node {
              id
              title
              sku
              price
              availableForSale
              selectedOptions {
                name
                value
              }
            }
          }
        }
        images(first: 10) {
          edges {
            node {
              originalSrc
            }
          }
        }
        metafields(first: 10) {
          edges {
            node {
              namespace
              key
              value
              type
            }
          }
        }
      }
    }
  }
}
"""

def start_bulk_operation():
    url = f"https://{SHOP_URL}/admin/api/{API_VERSION}/graphql.json"
    payload = {
        "query": f'''
        mutation {{
          bulkOperationRunQuery(
            query: """
            {bulk_query}
            """
          ) {{
            bulkOperation {{
              id
              status
            }}
            userErrors {{
              field
              message
            }}
          }}
        }}
        '''
    }
    response = requests.post(url, headers=HEADERS, json=payload)
    data = response.json()
    print("🚀 Bulk operation started.")
    return data
    

def wait_for_completion():
    url = f"https://{SHOP_URL}/admin/api/{API_VERSION}/graphql.json"
    query = {
        "query": '''
        {
          currentBulkOperation {
            id
            status
            url
            errorCode
            createdAt
          }
        }
        '''
    }

    print("⏳ Waiting for bulk operation to complete...")
    while True:
        res = requests.post(url, headers=HEADERS, json=query)
        data = res.json()
        op = data["data"]["currentBulkOperation"]

        if op["status"] in ["COMPLETED", "FAILED"]:
            print(f"✅ Status: {op['status']}")
            if op["status"] == "COMPLETED":
                return op["url"]
            else:
                raise Exception("❌ Bulk operation failed")
        time.sleep(3)

def download_jsonl_file(download_url, output_file="bulk_products.jsonl"):
    print("⬇️ Downloading JSONL file...")
    response = requests.get(download_url)
    
    # Печать первого байта ответа для проверки
    print(f"Response first byte: {response.content[:10]}")
    
    with open(output_file, "wb") as f:
        f.write(response.content)
    
    print(f"📁 File saved as: {output_file}")
    return output_file

def read_jsonl_file(jsonl_path):
    print("📖 Parsing JSONL file...")

    with open(jsonl_path, 'r', encoding='utf-8') as file:
        for line in file:
            product = json.loads(line)

            # Пропускаем, если товар не активен
            if product.get("status") != "ACTIVE":
                continue

            title = product.get('title', '—')
            handle = product.get('handle', '—')
            status = product.get('status', '—')
            description = product.get('bodyHtml', '')  # Исправлено на 'bodyHtml'

            print(f"- {title} ({handle}) → Статус: {status}")
            if description:
                print(f"  Описание: {description[:150]}...")  # Печатает первые 150 символов описания
            else:
                print("  ⚠️ Описание отсутствует")
            print()

# ---- RUN ----
if __name__ == "__main__":
    start_bulk_operation()
    url = wait_for_completion()
    jsonl_path = download_jsonl_file(url)
    read_jsonl_file(jsonl_path)
