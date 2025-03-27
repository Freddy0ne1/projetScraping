import requests
from bs4 import BeautifulSoup
import csv
from tqdm import tqdm
import os

# Fonction pour extraire les liens des livres d'une page donnée
def get_books_from_page(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    books = []
    
    for article in soup.select(".product_pod"):
        book_url = "https://books.toscrape.com/catalogue/" + article.h3.a["href"].replace("../../../", "")
        books.append(book_url)
    
    return books, soup.select_one(".next a")

# Fonction pour extraire les détails d'un livre
def scrape_product(url):
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    
    product_page_url = url
    upc = soup.find("th", string="UPC").find_next("td").text
    title = soup.find("h1").text
    price_incl_tax = soup.find("th", string="Price (incl. tax)").find_next("td").text
    price_excl_tax = soup.find("th", string="Price (excl. tax)").find_next("td").text
    number_available = soup.find("th", string="Availability").find_next("td").text.strip()
    product_description = soup.find("meta", {"name": "description"})
    product_description = product_description["content"].strip() if product_description else ""
    category = soup.find("ul", class_="breadcrumb").find_all("li")[-2].text.strip()
    review_rating = soup.find("p", class_="star-rating")["class"][1]
    image_url = soup.find("div", class_="item active").find("img")["src"].replace("../../", "")
    # print(image_url)
    image_url = url.rsplit("/", 3)[0] + "/" + image_url.strip("/")
    #print(image_url)
    
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

# Fonction principale pour parcourir toutes les pages et extraire les données
def scrape_books(base_url, start_url):
    book_urls = []
    url = start_url
    
    while url:
        print(f"Scraping page: {url}")
        page_books, next_page = get_books_from_page(url)
        book_urls.extend(page_books)
        
        if next_page:
            url = base_url + next_page["href"]
        else:
            url = None
    
# Intégration de la barre progression du scraping de chaque livre
    books_data = []
    print(f"\nScraping des détails de {len(book_urls)} livres en cours...\n")
    for book_data in tqdm(book_urls, desc="Progression", unit="livre"):
        books_data.append(scrape_product(book_data))
        
    return books_data

# Création du dossier de stockage
nom_dossier = "../output"  

# Vérifier si le dossier n'existe pas avant de le créer
if not os.path.exists(nom_dossier):
    os.makedirs(nom_dossier)
    print(f"Dossier '{nom_dossier}' créé avec succès.")
else:
    print(f"Le dossier '{nom_dossier}' existe déjà.")
    

# Fonction pour enregistrer les données extraites dans un fichier CSV
def save_to_csv(books, filename="../output/books.csv"):
    if books:
        fieldnames = books[0].keys()
        with open(filename, "w", newline="", encoding="cp1252") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(books)

if __name__ == "__main__":
    BASE_URL = "https://books.toscrape.com/catalogue/category/books/sequential-art_5/"
    START_URL = BASE_URL + "index.html"
    
    books_data = scrape_books(BASE_URL, START_URL)
    save_to_csv(books_data)
    print("Scraping terminé. Données enregistrées dans '../output/books.csv'")
