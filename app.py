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


        for variant in product.get("variants", {}).get("edges", []):
            v = variant["node"]
            if not v.get("availableForSale", True):
                continue  # Пропускаем товары, которые не в наличии
            safe_id = str(int(v["id"].split("/")[-1]) % 2147483647)
            title_parts = v.get("title", "").split(" / ")
            size = title_parts[0] if len(title_parts) > 0 else "M"
            color = title_parts[1] if len(title_parts) > 1 else "Невідомо"
            collar = title_parts[2] if len(title_parts) > 2 else "Класичний"
            available = "true" if v.get("availableForSale", True) else "false"

            offer = ET.SubElement(offers, "offer", {
                "id": safe_id,
                "available": available,
                "in_stock": "true" if available == "true" else "false",
                "type": "vendor.model",
                "selling_type": "r",
                "group_id": safe_id
            })

            # Добавляем тег availability
            availability_status = "in stock" if available == "true" else "out of stock"
            ET.SubElement(offer, "{http://base.google.com/ns/1.0}availability").text = availability_status


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
            ET.SubElement(offer, "description").text = f"<![CDATA[{product.get('bodyHtml', '')}]]>"
            ET.SubElement(offer, "description_ua").text = f"<![CDATA[{product.get('bodyHtml', '')}]]>"
            ET.SubElement(offer, "url").text = f"https://rubaska.com/products/{product['handle']}"

            for img in product.get("images", {}).get("edges", []):
                ET.SubElement(offer, "picture").text = img["node"]["src"]

            ET.SubElement(offer, "price").text = v.get("price", "0")
            ET.SubElement(offer, "currencyId").text = "UAH"
            ET.SubElement(offer, "categoryId").text = category["category_id"]
            ET.SubElement(offer, "portal_category_id").text = category["portal_url"]
            ET.SubElement(offer, "vendor").text = product.get("vendor", "RUBASKA")
            ET.SubElement(offer, "model").text = v.get("title", "Сорочка Без моделі")
            ET.SubElement(offer, "vendorCode").text = v.get("sku") or safe_id
            ET.SubElement(offer, "country").text = "Туреччина"
            ET.SubElement(offer, "param", name="Колір").text = color
            ET.SubElement(offer, "param", name="Розмір").text = size
            ET.SubElement(offer, "param", name="Тип сорочкового коміра").text = collar

            ET.SubElement(offer, "param", name="Міжнародний розмір").text = size
            ET.SubElement(offer, "param", name="Стан").text = "Новий"
            ET.SubElement(offer, "param", name="Де знаходиться товар").text = "Одеса"
            ET.SubElement(offer, "param", name="Країна виробник").text = "Туреччина"

            # Характеристики из метафилдов
            field_mapping = {
                "Тип виробу": "product_type",
                "Застежка": "fastening",
                "Тип тканини": "fabric_type",
                "Тип крою": "cut_type",
                "Фасон рукава": "sleeve_style",
                "Візерунки і принти": "pattern_and_prints",
                "Манжет сорочки": "shirt_cuff",
                "Стиль": "style",
                "Склад": "fabric_composition",
                "Кишені": "pockets",
            
            }

            for label, key in field_mapping.items():
                value = metafields.get(key)
                if value:
                    ET.SubElement(offer, "param", name=label).text = value

            # Постоянные характеристики
            constant_params = [
                ("Міжнародний розмір", size),
                ("Стан", "Новий"),
                ("Де знаходиться товар", "Одеса"),
                ("Країна виробник", "Туреччина"),
            ]
            for name, value in constant_params:
                ET.SubElement(offer, "param", name=name).text = value

            # Добавление product_detail по категории
            if category_details:
                for attr_name, attr_value in {
                    "Ідентифікатор_підрозділу": category["subdivision_id"],
                    "Посилання_підрозділу": category["portal_url"],
                    "Назва_групи": category["group_name"]
                }.items():
                    detail = ET.SubElement(offer, "{http://base.google.com/ns/1.0}product_detail")
                    ET.SubElement(detail, "{http://base.google.com/ns/1.0}attribute_name").text = attr_name
                    ET.SubElement(detail, "{http://base.google.com/ns/1.0}attribute_value").text = attr_value
        

    return ET.tostring(rss, encoding="utf-8")

@app.route("/feed.xml")
def feed():
    products = load_products_from_bulk("bulk_products.jsonl")
    xml_data = generate_xml(products)
    return Response(xml_data, mimetype="application/xml")


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5050)

