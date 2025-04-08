import requests

def download_result_file():
    url = "https://storage.googleapis.com/shopify-tiers-assets-prod-us-east1/bulk-operation-outputs/5rq8r7fbqcyux56k2rvyk7itqg7a-final?GoogleAccessId=assets-us-prod%40shopify-tiers.iam.gserviceaccount.com&Expires=1744720299&Signature=LBmGB2YFIV8d8ovh%2FiARTpXTZZOXFBO2qXVRtctp60mfY9S6GSCqXFVbOp28uHqyk9yvTUdHIDOt8YRSIBI3syZ%2BeBjWMtaMsXn2Mhto5I8DfXbMRsxMl7ANH8bluf%2FuoVNWEk3smf%2B34FsQOwh6db0B2Z1T7iq%2BnRLGBuUpz34rIYF6kqHq%2FJPTgKDX1Ai6%2BSpYwOK98gfINte5ZxuyqY0CYqfJWX3usU1fiviODiGr10KZKE%2FUTmZsNJgBtu6KlJUgXhgzpkUOIm3kJFXA6NzKM5GwyHmaHDXgSerJ%2BOJu%2BGtgQUFOvO0BZvGiph0b5j0v2YdZzIEebCwgBIEEyA%3D%3D&response-content-disposition=attachment%3B+filename%3D%22bulk-6014548115767.jsonl%22%3B+filename%2A%3DUTF-8%27%27bulk-6014548115767.jsonl&response-content-type=application%2Fjsonl"
    r = requests.get(url)
    with open("bulk_products.jsonl", "wb") as f:
        f.write(r.content)
    print("✅ Файл сохранён как bulk_products.jsonl")

download_result_file()
