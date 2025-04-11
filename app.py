from flask import Flask, Response
import xml.etree.ElementTree as ET
import json

app = Flask(__name__)

# Пример структуры categories
category_info = {
    "Сорочка": {
        "group_name": "Чоловічі сорочки",
        "subdivision_id": "348",
        "category_id": "129880800",
        "portal_url": "https://prom.ua/Muzhskie-rubashki"
    },
    "Футболка": {
        "group_name": "Чоловічі футболки та майки",
        "subdivision_id": "35506",
        "category_id": "129880791",
        "portal_url": "https://prom.ua/Futbolki-muzhskie"
    },
    "Жилет": {
        "group_name": "Чоловічі піджаки",
        "subdivision_id": "35509",
        "category_id": "129883725",
        "portal_url": "https://prom.ua/Muzhskie-pidzhaki"
    }
}

def generate_xml(products):
    rss = ET.Element("rss", version="2.0", attrib={"xmlns:g": "http://base.google.com/ns/1.0"})
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = 'Інтернет-магазин "Rubaska"'
    ET.SubElement(channel, "link").text = "https://rubaska.prom.ua/"
    ET.SubElement(channel, "g:description").text = "RSS 2.0 product data feed"

    for product in products:
        if product.get("status", "").lower() != "active":
            continue
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

            offer = ET.SubElement(channel, "item")
            ET.SubElement(offer, "g:id").text = safe_id
            ET.SubElement(offer, "g:title").text = product["title"]
            desc = product.get("bodyHtml") or product.get("description") or "Опис буде додано найближчим часом."
            desc_ua = product.get("description_ua") or desc
            ET.SubElement(offer, "g:description").text = desc
            ET.SubElement(offer, "g:link").text = f"https://rubaska.com/products/{product['handle']}?source=merchant_center"
            ET.SubElement(offer, "g:ads_redirect").text = f"https://rubaska.com/products/{product['handle']}?source=merchant_center"

            for img in product.get("images", {}).get("edges", [])[:10]:
                if img["node"]["src"]:
                    if offer.find("g:image_link") is None:
                        ET.SubElement(offer, "g:image_link").text = img["node"]["src"]
                    else:
                        ET.SubElement(offer, "g:additional_image_link").text = img["node"]["src"]

            ET.SubElement(offer, "g:availability").text = "in stock"
            ET.SubElement(offer, "g:price").text = v.get("price", "0") + " UAH"
            ET.SubElement(offer, "g:product_type").text = f"одяг та взуття > чоловічий одяг > {category['group_name']}"
            ET.SubElement(offer, "g:brand").text = "RUBASKA"
            ET.SubElement(offer, "g:identifier_exists").text = "no"
            ET.SubElement(offer, "g:condition").text = "new"
            ET.SubElement(offer, "g:color").text = color
            ET.SubElement(offer, "g:size").text = size

            dimensions = {
                "S":   ("38", "98", "90", "63", "44"),
                "M":   ("39", "104", "96", "64", "46"),
                "L":   ("41", "108", "100", "65", "48"),
                "XL":  ("43", "112", "108", "66", "50"),
                "XXL": ("45", "120", "112", "67", "52"),
                "3XL": ("46", "126", "124", "68", "54"),
            }
            neck, chest, waist, sleeve, chest_size = dimensions.get(size, ("41", "108", "100", "65", "48"))
            details = {
                "Країна виробник": "Туреччина",
                "Вид виробу": product_type,
                "Розміри чоловічих сорочок": chest_size,
                "Обхват шиї": neck + " см",
                "Обхват грудей": chest + " см",
                "Обхват талії": waist + " см",
                "Тип крою": "Приталена",
                "Тип сорочкового коміра": collar,
                "Фасон рукава": "Довгий",
                "Манжет сорочки": "З двома гудзиками",
                "Тип тканини": "Бавовна",
                "Стиль": "Casual",
                "Візерунки і принти": "Без візерунків і принтів",
                "Склад": "стретч -котон",
                "Ідентифікатор_підрозділу": category["subdivision_id"],
                "Посилання_підрозділу": category["portal_url"],
                "Назва_групи": category["group_name"],
                "Міжнародний розмір": size
            }
            for key, value in details.items():
                gpd = ET.SubElement(offer, "g:product_detail")
                ET.SubElement(gpd, "g:attribute_name").text = key
                ET.SubElement(gpd, "g:attribute_value").text = value

    return ET.tostring(rss, encoding="utf-8", method="xml")


@app.route("/feed.xml")
def feed():
    # Здесь должен быть импорт товаров из Shopify или фиктивные тестовые данные
    with open("bulk_products.jsonl", "r", encoding="utf-8") as f:
        data = {"products": {"edges": [ {"node": json.loads(line.strip())} for line in f if line.strip() ] }}
    xml_data = generate_xml(data["products"]["edges"])
    return Response(xml_data, mimetype="application/xml")
