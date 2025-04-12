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


# ✅ Глобальный словарь с дефолтными метафилдами по категории
default_metafields_by_category = {
    "Чоловічі сорочки": {
        "Вид изделия": "Сорочка",
        "Застежка": "Гудзики",
        "Тип тканини": "Бавовна",
        "Тип крою": "Приталена",
        "Фасон рукава": "Довгий",
        "Манжет сорочки": "З двома гудзиками",
        "Стиль": "Casual",
        "Візерунки і принти": "Без візерунків і принтів",
        "Склад": "95% бавовна 5% стретч",
        "Кишені": ""
    },
    "Чоловічі футболки та майки": {
        "Вид изделия": "Футболка",
        "Модель": "Поло",
        "Тип тканини": "Бавовна",
        "Силует": "Прямий",
        "Фасон вирізу горловини": "V-подібний",
        "Візерунки і принти": "Без візерунків і принтів",
        "Стиль": "Спортивний",
        "Склад": "100% бавовна"
        
    },
    "Святкові жилети": {
        "Вид изделия": "Жилет",
        "Тип тканини": "Трикотаж",
        "Тип крою": "Діловий",
        "Стиль": "Святковий",
        "Склад": "Поліестер 70%, Віскоза 30%",
        "Кишені": "Фальш"
    }
}

# 👇 А потом уже идёт функция
def generate_xml(products):
    ...




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
        

        metafields = {
            m["node"]["key"]: m["node"]["value"]
            for m in product.get("metafields", {}).get("edges", [])
            if m["node"]["namespace"] == "custom"
        }
        # Получаем 'product_type_raw' из метафилдов, иначе берём стандартное поле
        product_type_raw = metafields.get("product_type_raw") or product.get("productType", "").strip()
        product_type = product_type_raw or "Сорочка"
        category = category_info.get(product_type, category_info["Сорочка"])


        for variant in product.get("variants", {}).get("edges", []):
            v = variant["node"]
            if not v.get("availableForSale", True):
                continue  # Пропускаем товары, которые не в наличии
            safe_id = str(int(v["id"].split("/")[-1]) % 1000000000)
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

            # ✅ Добавить portal_category_id на основе метафилда product_type_raw или стандартного поля
            category_name = metafields.get("product_type_raw") or product.get("productType", "").strip() or "Сорочка"
            category = category_info.get(category_name, category_info["Сорочка"])
    


            # Добавляем тег availability
            availability_status = "in stock" if available == "true" else "out of stock"
            ET.SubElement(offer, "{http://base.google.com/ns/1.0}availability").text = availability_status


            
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

            for img in product.get("images", {}).get("edges", []):
                ET.SubElement(offer, "picture").text = img["node"]["src"]

            ET.SubElement(offer, "price").text = v.get("price", "0")
            ET.SubElement(offer, "currencyId").text = "UAH"
            ET.SubElement(offer, "param", name="Де знаходиться товар").text = "Одесса"
            ET.SubElement(offer, "categoryId").text = category["category_id"]
            ET.SubElement(offer, "portal_category_id").text = category["subdivision_id"]  # категория на маркетплейсе
            ET.SubElement(offer, "portal_category_url").text = category["portal_url"]  # ссылка на маркетплейс
            ET.SubElement(offer, "vendor").text = product.get("vendor", "RUBASKA")
            model_prefix = product_type_raw or "Сорочка"
            model_title = v.get("title", "").strip() or "Без моделі"
            ET.SubElement(offer, "model").text = f"{model_prefix} {model_title}"
            ET.SubElement(offer, "vendorCode").text = v.get("sku") or safe_id
            ET.SubElement(offer, "param", name="Колір").text = color
            ET.SubElement(offer, "param", name="Розмір").text = size
            ET.SubElement(offer, "param", name="Тип сорочкового коміра").text = collar
            ET.SubElement(offer, "param", name="Міжнародний розмір").text = size
            ET.SubElement(offer, "param", name="Стан").text = "Новий"            
            ET.SubElement(offer, "param", name="Країна виробник").text = "Туреччина"


            # Размерные характеристики для "Сорочка"
            if category["group_name"] == "Чоловічі сорочки":
                measurements = {
                    "S":   {"Обхват шеи": "38", "Обхват груди": "98",  "Обхват талии": "90", "Длина рукава изделия": "63", "Розміри чоловічих сорочок": "44"},
                    "M":   {"Обхват шеи": "39", "Обхват груди": "104", "Обхват талии": "96", "Длина рукава изделия": "64", "Розміри чоловічих сорочок": "46"},
                    "L":   {"Обхват шеи": "41", "Обхват груди": "108", "Обхват талии": "100", "Длина рукава изделия": "65", "Розміри чоловічих сорочок": "48"},
                    "XL":  {"Обхват шеи": "43", "Обхват груди": "112", "Обхват талии": "108", "Длина рукава изделия": "66", "Розміри чоловічих сорочок": "50"},
                    "XXL": {"Обхват шеи": "45", "Обхват груди": "120", "Обхват талии": "112", "Длина рукава изделия": "67", "Розміри чоловічих сорочок": "52"},
                    "3XL": {"Обхват шеи": "46", "Обхват груди": "126", "Обхват талии": "124", "Длина рукава изделия": "68", "Розміри чоловічих сорочок": "54"},
                }
                for label, value in measurements.get(size, {}).items():
                    ET.SubElement(offer, "param", name=label).text = value


            # 👉 Характеристики для "Футболка"
            elif category["group_name"] == "Чоловічі футболки та майки":
                measurements = {
                    "S":   {"Обхват грудей": "", "Обхват таліїу": ""},
                    "M":   {"Обхват грудей": "", "Обхват таліїу": ""},
                    "L":   {"Обхват грудей": "", "Обхват таліїу": ""},
                    "XL":   {"Обхват грудей": "", "Обхват таліїу": ""},
                    "XXL":   {"Обхват грудей": "", "Обхват таліїу": ""},
                     "3XL":   {"Обхват грудей": "", "Обхват таліїу": ""},
                }
                for label, value in measurements.get(size, {}).items():
                    ET.SubElement(offer, "param", name=label).text = value





            # Характеристики из метафилдов
            field_mapping = {
                "Вид виробу": "product_type_raw",
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

            for label, key in field_mapping.items():
                value = metafields.get(key)
                if not value and key == "product_type_raw":
                    value = product_type_raw  # если в метафилде пусто, но product_type_raw есть
                if value:
                    ET.SubElement(offer, "param", name=label).text = value




                    

    return ET.tostring(rss, encoding="utf-8")

@app.route("/feed.xml")
def feed():
    products = load_products_from_bulk("bulk_products.jsonl")
    xml_data = generate_xml(products)
    return Response(xml_data, mimetype="application/xml")



if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5050)
