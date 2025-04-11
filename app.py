from flask import Flask, Response
import xml.etree.ElementTree as ET
import json

app = Flask(__name__)

def load_products_from_bulk(filepath):
    products_raw = {}
    variants = {}
    images = {}
    metafields = {}

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line)
            obj_id = obj.get("id", "")
            parent_id = obj.get("__parentId")

            if "Product" in obj_id and not parent_id:
                products_raw[obj_id] = obj
            elif "ProductVariant" in obj_id and parent_id:
                variants.setdefault(parent_id, []).append({"node": obj})
            elif "originalSrc" in obj and parent_id:
                images.setdefault(parent_id, []).append({"node": {"src": obj["originalSrc"]}})
            elif obj.get("namespace") == "custom" and parent_id:
                metafields.setdefault(parent_id, []).append({"node": obj})

    structured_products = []
    for pid, product in products_raw.items():
        product["variants"] = {"edges": variants.get(pid, [])}
        product["images"] = {"edges": images.get(pid, [])}
        product["metafields"] = {"edges": metafields.get(pid, [])}
        structured_products.append(product)

    return structured_products

def generate_xml(products):
    ET.register_namespace("g", "http://base.google.com/ns/1.0")
    rss = ET.Element("rss", {"version": "2.0"})
    shop = ET.SubElement(rss, "shop")

    ET.SubElement(shop, "name").text = 'Інтернет-магазин "Rubaska"'
    ET.SubElement(shop, "company").text = "Rubaska"
    ET.SubElement(shop, "url").text = "https://rubaska.com/"

    category_info = {
        "Сорочка": {
            "category_id": "129880800", "parent_id": "129880784",
            "group_name": "Чоловічі сорочки",
            "portal_url": "https://prom.ua/Muzhskie-rubashki",
            "subdivision_id": "348"
        },
        "Теніска": {
            "category_id": "129880800",
            "parent_id": "129880784",
            "group_name": "Чоловічі сорочки",
            "portal_url": "https://prom.ua/Muzhskie-rubashki",
            "subdivision_id": "348"
        },
        "Футболка": {
            "category_id": "129880791",
            "parent_id": "129880784",
            "group_name": "Чоловічі футболки та майки",
            "portal_url": "https://prom.ua/Futbolki-muzhskie",
            "subdivision_id": "35506"
        },
        "Жилет": {
            "category_id": "129883725",
            "parent_id": "129880784",
            "group_name": "Святкові жилети",
            "portal_url": "https://prom.ua/ua/Muzhskie-zhiletki-i-bezrukavki-1",
            "subdivision_id": "35513"
        },
    }

    categories = ET.SubElement(shop, "categories")
    for cat in category_info.values():
        ET.SubElement(categories, "category", id=cat["category_id"], parentId=cat["parent_id"]).text = cat["group_name"]

    offers = ET.SubElement(shop, "offers")

    
for product in products:
    product_type = product.get("productType", "Сорочка")
    category = category_info.get(product_type, category_info["Сорочка"])

    metafields = {
        m["node"]["key"]: m["node"]["value"]
        for m in product.get("metafields", {}).get("edges", [])
        if m["node"]["namespace"] == "custom"
    }

    for variant in product.get("variants", {}).get("edges", []):
        v = variant["node"]
        if not v.get("availableForSale", True):
            continue

        safe_id = str(int(v["id"].split("/")[-1]) % 2147483647)
        title_parts = v.get("title", "").split(" / ")
        size = title_parts[0] if len(title_parts) > 0 else "M"
        color = title_parts[1] if len(title_parts) > 1 else "Невідомо"
        collar = title_parts[2] if len(title_parts) > 2 else "Класичний"

        offer = ET.SubElement(offers, "offer", {
            "id": safe_id,
            "available": "true",
            "in_stock": "true",
            "type": "vendor.model",
            "selling_type": "r",
            "group_id": safe_id
        })

        ET.SubElement(offer, "portal_category_id").text = category["subdivision_id"]

        # Размерные характеристики
        measurements = {
            "S":   {"Обхват шиї": "38", "Обхват грудей": "98",  "Обхват талії": "90", "Довжина рукава": "63", "Розміри чоловічих сорочок": "44"},
            "M":   {"Обхват шиї": "39", "Обхват грудей": "104", "Обхват талії": "96", "Довжина рукава": "64", "Розміри чоловічих сорочок": "46"},
            "L":   {"Обхват шиї": "41", "Обхват грудей": "108", "Обхват талії": "100", "Довжина рукава": "65", "Розміри чоловічих сорочок": "48"},
            "XL":  {"Обхват шиї": "43", "Обхват грудей": "112", "Обхват талії": "108", "Довжина рукава": "66", "Розміри чоловічих сорочок": "50"},
            "XXL": {"Обхват шиї": "45", "Обхват грудей": "120", "Обхват талії": "112", "Довжина рукава": "67", "Розміри чоловічих сорочок": "52"},
            "3XL": {"Обхват шиї": "46", "Обхват грудей": "126", "Обхват талії": "124", "Довжина рукава": "68", "Розміри чоловічих сорочок": "54"},
        }
        for label, value in measurements.get(size, {}).items():
            ET.SubElement(offer, "param", name=label).text = value

        ET.SubElement(offer, "name").text = product["title"]
        ET.SubElement(offer, "name_ua").text = product["title"]

        desc = (
            product.get("bodyHtml")
            or product.get("descriptionHtml")
            or product.get("description")
            or "Опис буде додано найближчим часом."
        )
        desc_ua = product.get("description_ua") or desc
        ET.SubElement(offer, "description").text = f"<![CDATA[{desc}]]>"
        ET.SubElement(offer, "description_ua").text = f"<![CDATA[{desc_ua}]]>"

        ET.SubElement(offer, "url").text = f"https://rubaska.com/products/{product['handle']}"

        for img in product.get("images", {}).get("edges", [])[:10]:
            ET.SubElement(offer, "picture").text = img["node"]["src"]

        ET.SubElement(offer, "price").text = v.get("price", "0")
        ET.SubElement(offer, "currencyId").text = "UAH"

        ET.SubElement(offer, "param", name="Де знаходиться товар").text = "Одеса"
        ET.SubElement(offer, "categoryId").text = category["category_id"]
        ET.SubElement(offer, "param", name="product_type").text = "одяг та взуття > чоловічий одяг > " + category["group_name"]

        ET.SubElement(offer, "vendor").text = product.get("vendor", "RUBASKA")
        ET.SubElement(offer, "param", name="identifier_exists").text = "no"
        ET.SubElement(offer, "model").text = v.get("title", "Сорочка Без моделі")
        ET.SubElement(offer, "vendorCode").text = metafields.get("sku") or v.get("sku") or safe_id

        default_params = {
            "Стан": "Новий",
            "Колір": color,
            "Розмір": size,
            "Країна виробник": "Туреччина",
            "Тип виробу": "Сорочка",
            "Тип крою": "Приталена",
            "Тип сорочкового коміра": collar,
            "Фасон рукава": "Довгий",
            "Манжет сорочки": "З двома гудзиками",
            "Застежка": "Гудзики",
            "Тип тканини": "Бавовна",
            "Стиль": "Casual",
            "Візерунки і принти": "Без візерунків і принтів",
            "Кишені": "Верхній",
            "Склад": "95% бавовна, 5% стретч",
            "Міжнародний розмір": size,
            "Ідентифікатор_підрозділу": category["subdivision_id"],
            "Посилання_підрозділу": category["portal_url"],
            "Назва_групи": category["group_name"]
        }

        for key, value in default_params.items():
            ET.SubElement(offer, "param", name=key).text = value

