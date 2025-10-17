import pandas
import requests
import os

# pandas, os, requests leírva dolgozatban [2025.10.17: 15:53]
# Excel fájl kezelése
excel_forras= input("Kérlek add meg a kari oktatók adatait tartalmazó excel fájl nevét: ")

#excel_forras = "DEIK_Nevsor_1.4.xlsx"  régi megoldás(marad teszteléshez)
excel_beolvasas_adatkeret = pandas.read_excel(excel_forras)

# Feldolgozandó tanszékek (marad, mivel belső szűrést biztosít
letoltendo_tanszekek = [
    "Információ Technológia Tanszék",
    "Adattudomány és Vizualizáció Tanszék",
    "Számítógéptudományi Tanszék",
    "Alkalmazott Matematika és Valószínűségszámítás Tanszék",
    "Informatikai Rendszerek és Hálózatok Tanszék"
]

# Adatok tisztítása és szürése
tisztitott_adatok = excel_beolvasas_adatkeret.dropna(subset=['MTID (MTMT ID)', 'Tanszék'])
tisztitott_adatok = tisztitott_adatok[tisztitott_adatok['Tanszék'].isin(letoltendo_tanszekek)]
tisztitott_adatok['MTID (MTMT ID)'] = tisztitott_adatok['MTID (MTMT ID)'].astype(int)

# URL sablonok
#Rendes sablon (1000):
url_sablon_V2 = "https://m2.mtmt.hu/api/publication?page=1&cond=authors%3Bin%3B{}&sort=publishedYear%2Cdesc&size=1000"

#Nagy sablon (2500)
url_sablon_nagy_V2= "https://m2.mtmt.hu/api/publication?page=1&cond=authors%3Bin%3B{}&sort=publishedYear%2Cdesc&size=2500"
# V2 link a végleges, pár infó: default format=json,   / ez nem találom most default cite_type=2/ %3B--> ; karakter
#snippet "Mélység"--> depth=0 (Snippet mélység)

# Fő programrész
kimeneti_mappa_neve=input("Kérlek add meg a kimeneti mappa nevét: ")
os.makedirs(kimeneti_mappa_neve, exist_ok=True)

for index, sor in tisztitott_adatok.iterrows():
    tanszek = str(sor['Tanszék'])
    azonosito = sor['MTID (MTMT ID)']

    # Tanszékek számára almappa jön létre
    tanszek_mappa = os.path.join(kimeneti_mappa_neve, tanszek)
    os.makedirs(tanszek_mappa, exist_ok=True)

#Stringként kezelni a legbiztonságosabb, mert nem felételezem hogy int lesz az adat típusa.
    if str(azonosito) == "10018517": # Ujvári Balázs azonostítója a 2000+ publikáció miatt  10018517
        print(f"A program nem akadt meg, csak átlagosnál több idő szükséges a következő kutató ({azonosito} publikációinak kigyüjtéséhez.") # extra rész, tájékoztatás
        url = url_sablon_nagy_V2.format(azonosito)
    else:
        url = url_sablon_V2.format(azonosito)

    api_valasz = requests.get(url)

    if api_valasz.status_code == 200:
        fajl_eleresi_utja = os.path.join(tanszek_mappa, f"{azonosito}.json")
        with open(fajl_eleresi_utja, "w", encoding="utf-8") as fajl:
            fajl.write(api_valasz.text)
        print(f"Mentve: {fajl_eleresi_utja}")
    else:
        print(f"Hiba {api_valasz.status_code} | ID: {azonosito} | Tanszék: {tanszek}")

print("A letöltés befejeződött!")