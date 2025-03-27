# Importation des bibliothèques
import requests
from bs4 import BeautifulSoup
import csv
import os

# Fonction Scrape_product
def scrape_product(url):
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Extraction des données
    product_page_url = url
    upc = soup.find("th", string="UPC").find_next("td").text
    title = soup.find("h1").text
    price_incl_tax = soup.find("th", string="Price (incl. tax)").find_next("td").text
    price_excl_tax = soup.find("th", string="Price (excl. tax)").find_next("td").text
    number_available = soup.find("th", string="Availability").find_next("td").text
    product_description = soup.find("meta", {"name": "description"})
    product_description = product_description["content"].strip() if product_description else ""
    category = soup.find("ul", class_="breadcrumb").find_all("li")[-2].text.strip()
    review_rating = soup.find("p", class_="star-rating")["class"][1]
    image_url = soup.find("div", class_="item active").find("img")["src"]
    image_url = url.rsplit("/", 3)[0] + "/" + image_url.strip("/")
    
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

# Création du dossier de stackage
nom_dossier = "../output"  

# Vérifier si le dossier n'existe pas avant de le créer
if not os.path.exists(nom_dossier):
    os.makedirs(nom_dossier)
    print(f"Dossier '{nom_dossier}' créé avec succès.")
else:
    print(f"Le dossier '{nom_dossier}' existe déjà.")


def save_to_csv(data, filename="../output/data.csv"):
    fieldnames = data.keys()
    
    with open(filename, mode="w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(data)

if __name__ == "__main__":
    product_url = "https://books.toscrape.com/catalogue/emma_17/index.html"  
    product_data = scrape_product(product_url)
    save_to_csv(product_data)
    print("Les données ont été enregistrées dans data.csv")