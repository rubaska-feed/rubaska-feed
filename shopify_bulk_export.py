import requests
import time
import json

SHOP_URL = "676c64.myshopify.com"

API_VERSION = "2023-10"



HEADERS = {
    "Content-Type": "application/json",
    "X-Shopify-Access-Token": TOKEN
}

bulk_query = """
{
  products {
    edges {
      node {
        id
        title
        handle
        productType
        vendor
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
    query = {
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
    response = requests.post(url, headers=HEADERS, json=query)
    print(response.json())

start_bulk_operation()
