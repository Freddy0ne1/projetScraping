import requests
from bs4 import BeautifulSoup
import csv
import os
from urllib.parse import urljoin
from tqdm import tqdm
import re


# URL de base du site à scraper
BASE_SITE_URL = "https://books.toscrape.com/"

# Récupération de toutes les catégories de livres depuis la page d'accueil
def get_all_categories():
    response = requests.get(BASE_SITE_URL)
    soup = BeautifulSoup(response.text, "html.parser")
    category_elements = soup.select("div.side_categories ul li ul li a")

    categories = {}
    for cat in category_elements:
        name = cat.text.strip()
        href = cat["href"]
        url = urljoin(BASE_SITE_URL, href)
        categories[name] = url
    
    return categories

# Extraction des liens des livres d'une page et la gestion la pagination
def get_books_from_page(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    books = []

    for article in soup.select(".product_pod"):
        book_url = urljoin(BASE_SITE_URL, "catalogue/" + article.h3.a["href"].replace("../../../", ""))
        books.append(book_url)

    next_page = soup.select_one(".next a")
    next_url = url.rsplit('/', 1)[0] + "/" + next_page["href"] if next_page else None

    return books, next_url

# Extraction des données détaillées d'un livre : titre, prix, disponibilité, etc.
def scrape_product(url):
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    product_page_url = url
    upc = soup.find("th", string="UPC").find_next("td").text
    title = soup.find("h1").text
    price_incl_tax = soup.find("th", string="Price (incl. tax)").find_next("td").text
    price_excl_tax = soup.find("th", string="Price (excl. tax)").find_next("td").text
    number_available = re.search(r"\d+", soup.find("th", string="Availability").find_next("td").text)
    number_available = number_available.group() if number_available else "0"
    product_description = soup.find("meta", {"name": "description"})
    product_description = product_description["content"].strip() if product_description else ""
    category = soup.find("ul", class_="breadcrumb").find_all("li")[-2].text.strip()
    review_rating = soup.find("p", class_="star-rating")["class"][1]
    image_url = soup.find("img")["src"].replace("../../", "")
    image_url = urljoin(BASE_SITE_URL, image_url)

    return {
        "product_page_url": product_page_url,
        "universal_product_code (upc)": upc,
        "title": title,
        "price_including_tax": price_incl_tax,
        "price_excluding_tax": price_excl_tax,
        "number_available": number_available,
        "product_description": product_description,
        "category": category,
        "review_rating": review_rating,
        "image_url": image_url
    }

# Téléchargement des images des livres et la gestion des erreurs de téléchargement
def download_image(url, path):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        with open(path, "wb") as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors du téléchargement de l'image {url} : {e}")

# Scrape tous les livres d'une catégorie et télécharge leurs images.
def scrape_books_from_category(category_name, category_url):
    print(f"\nScraping de la catégorie : {category_name}")
    url = category_url
    book_urls = []

    while url:
        print(f"  Page: {url}")
        books, url = get_books_from_page(url)
        book_urls.extend(books)

    books_data = []
    safe_category = category_name.lower().replace(" ", "_")
    image_folder = f"../output/images/{safe_category}"
    os.makedirs(image_folder, exist_ok=True)

# Intégration de la barre de progression 
    print(f"\nScraping de {len(book_urls)} livres en cours...\n")
    for book_url in tqdm(book_urls, desc=f"  → Livres de la catégorie : {category_name}"):
        try:
            book_data = scrape_product(book_url)
            books_data.append(book_data)

            image_filename = re.sub(r'[\\/*?:"<>|]', "_", book_data['title'])[:100] + ".jpg"
            image_path = os.path.join(image_folder, image_filename)
            download_image(book_data["image_url"], image_path)
        except Exception as e:
            print(f"Erreur lors du scraping de {book_url} : {e}")
    
    return books_data

# Sauvegarde les informations des livres dans un fichier CSV.
def save_to_csv(books, category_name):
    if not books:
        return

    safe_category_name = category_name.lower().replace(" ", "_")
    filename = f"books_{safe_category_name}.csv"
    os.makedirs("../output", exist_ok=True)
    filepath = os.path.join("../output", filename)

    with open(filepath, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=books[0].keys())
        writer.writeheader()
        writer.writerows(books)


    print(f"Données sauvegardées dans : {filepath}")

# Exécute le scraping pour toutes les catégories disponibles.
if __name__ == "__main__":
    categories = get_all_categories()

    for category_name, category_url in categories.items():
        books_data = scrape_books_from_category(category_name, category_url)
        save_to_csv(books_data, category_name)

    print("\nScraping terminé pour toutes les catégories.")
