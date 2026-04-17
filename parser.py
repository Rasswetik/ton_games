import os
import json
import requests
import re
from concurrent.futures import ThreadPoolExecutor
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Твои данные
raw_data = """
Vice Cream: 239Chill Flame: 263Snake Box: 275Candy Cane: 277Lunar Snake: 290Instant Ramen: 291Xmas Stocking: 294Ice Cream: 305Pool Float: 308Tama Gadget: 309Fresh Socks: 318Whip Cupcake: 319Holiday Drink: 319Lol Pop: 328Winter Wreath: 330Santa Hat: 333Pet Snake: 334Jester Hat: 338Happy Brownie: 340B-Day Candle: 341Big Year: 341Victory Medal: 346Party Sparkler: 351Mood Pack: 358Homemade Cake: 367Hypno Lollipop: 367Ginger Cookie: 379Mousse Cake: 383Money Pot: 383Stellar Rocket: 386Spiced Wine: 388Clover Pin: 389Cookie Heart: 399Star Notepad: 400Spring Basket: 414Pretty Posy: 415Swag Bag: 418Bow Tie: 418Faith Amulet: 419Hex Pot: 427Snoop Dogg: 430Jack-in-the-Box: 440Snow Globe: 449Easter Egg: 466Moon Pendant: 470Spy Agaric: 474Witch Hat: 479Restless Jar: 490Input Key: 495Timeless Book: 504Light Sword: 509Eternal Candle: 518Lush Bouquet: 579Desk Calendar: 583Jolly Chimp: 594Jelly Bunny: 599Joyful Bundle: 629Bunny Muffin: 664Snow Mittens: 673Evil Eye: 679Berry Box: 760Jingle Bells: 819Sleigh Bell: 829Hanging Star: 839Valentine Box: 859Sakura Flower: 925Love Candle: 969Skull Flower: 970Top Hat: 971Crystal Ball: 1020Snoop Cigar: 1040Flying Broom: 1090UFC Strike: 1170Mad Pumpkin: 1190Trapped Heart: 1240Record Player: 1340Love Potion: 1360Sky Stilettos: 1420Ionic Dryer: 1530Cupid Charm: 1870Khabib's Papakha: 2080Rare Bird: 2240Eternal Rose: 2400Bling Binky: 2590Diamond Ring: 2610Voodoo Doll: 2990Electric Skull: 3150Signet Ring: 3200Vintage Cigar: 3370Neko Helmet: 3530Toy Bear: 4090Sharp Tongue: 4390Swiss Watch: 4490Genie Lamp: 4490Bonded Ring: 4680Low Rider: 4990Kissed Frog: 5290Gem Signet: 6490Magic Potion: 6900Artisan Brick: 6990Ion Gem: 8390Mini Oscar: 8890Perfume Bottle: 9650Westside Sign: 10380Nail Bracelet: 12490Loot Bag: 13880Mighty Arm: 15150Scared Cat: 17480Astral Shard: 18490Heroic Helmet: 22330Precious Peach: 38790Durov's Cap: 67990Heart Locket: 172400Plush Pepe: 746900
"""

# Настройка умных повторов при сбое сети
session = requests.Session()
retry_strategy = Retry(
    total=5,
    backoff_factor=2, 
    status_forcelist=[429, 500, 502, 503, 504]
)
session.mount("https://", HTTPAdapter(max_retries=retry_strategy))

def download_item(item):
    name_clean, price, gift_id = item
    url = f"https://fragment.com/file/gifts/{gift_id}/thumb.webp"
    save_path = os.path.join("static", "img", "gifts", f"{gift_id}.png")
    
    try:
        # Тайм-аут 30 секунд для стабильности
        response = session.get(url, timeout=30)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                f.write(response.content)
            print(f"✅ Готово: {name_clean}")
            return {"id": gift_id, "name": name_clean, "price": int(price), "image": f"/static/img/gifts/{gift_id}.png"}
        else:
            print(f"⚠️ Пропущен {name_clean} (Код: {response.status_code})")
    except Exception as e:
        print(f"❌ Ошибка {name_clean}: {e}")
    return None

def main():
    # Создаем папки сразу
    os.makedirs(os.path.join('static', 'img', 'gifts'), exist_ok=True)
    os.makedirs('data', exist_ok=True)

    # Ищем пары Название: Цена
    pattern = r"([a-zA-Z\s\-\'0-9]+):\s?(\d+)"
    matches = re.findall(pattern, raw_data)
    
    tasks = []
    for name_raw, price in matches:
        name_clean = name_raw.strip()
        # Чистим ID для URL Fragment
        gift_id = name_clean.lower().replace(" ", "").replace("'", "").replace("-", "")
        tasks.append((name_clean, price, gift_id))

    print(f"🚀 Найдено подарков: {len(tasks)}. Запускаю многопоточную загрузку...")

    # Качаем в 10 потоков
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(download_item, tasks))

    # Фильтруем успешные
    final_data = [r for r in results if r is not None]

    # Сохраняем JSON
    json_path = os.path.join('data', 'gifts.json')
    try:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(final_data, f, indent=4, ensure_ascii=False)
        print(f"\n✨ ЗАВЕРШЕНО!")
        print(f"📁 Файл создан: {json_path}")
        print(f"🖼️ Картинки: static/img/gifts/")
        print(f"📊 Всего сохранено: {len(final_data)} из {len(tasks)}")
    except Exception as e:
        print(f"❌ Ошибка записи файла: {e}")

if __name__ == "__main__":
    main()