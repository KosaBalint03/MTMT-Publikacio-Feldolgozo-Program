import os
import json
import pandas as pd
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from collections import defaultdict
from itertools import combinations
import threading

#os, pandas leírva dolgozatban, többi hátravan! [2025.10.17 15:54]

#gyors jegyzet: mitől lesz kari a kari hálózat( oktatók mint csomópont). ha egy műben van kari oktató ,akkor az felkerül a feldogozott publikációk közé, és figyelembe vesszük, és csomópontok( melyek az oktatók) csak akkor jön létre kapcsolat, ha van olyan publikáció melyen 2 kari személy legalább dolgozott.
# tanszéki: csak azon publikációk szerepelnek, melyeken IKs szerzők dolgoztak, külsős személyt is tartalmazók nincsenek benne!( tisztán kari személyek általál készített publikációk)
# lényege: koncepciónális egyeztetés!( biztosítás hogy jól van-e megcsinálva

#plus note: et al.. csak egy felületi formátum, a fájlban benne van minden személy , még aki el van takarva et al. által is!!


class HalozatGeneraloGrafikusFelulettel:
    def __init__(self, root):
        self.root = root
        self.root.title("MTMT Hálózat Generátor és Elemző")  # ablak neve
        self.root.geometry("800x800")  # ablak méret
        #program során használt instance változók elő-deklarálása
        self.kari_szerzonevek = None
        self.folyamatcsik_vaz = None
        self.eredmenyek_szovege_vaz = None
        self.halozat_generalas_gomb_vaz = None
        self.kimeneti_fajl_prefixje = None
        self.minimum_egyuttmukodesek_szama_widget = None
        self.minimum_egyuttmukodesek_szama = None
        self.kozos_publikacio_szuro = None
        self.utolsoev_widget = None
        self.kezdetiev_widget = None
        self.ev_ig = None
        self.kezdeti_ev = None
        self.megjelenes_eve_alapu_szures = None
        self.csak_valodi_publikaciok = None
        self.halozat_tipusa = None
        self.rovid_adatelemzes = None
        self.adatalap_mappa_eleresi_utvonal = None
        self.kari_excel_eleresi_utvonal = None

        # Adatok Tárolására szolgáló változók
        self.publikaciok = [] #publákicókat tartalmazó tömb
        self.karhoz_tartozo_mtidk = set() #kari személyek mtid-jét tartalmazó set, melyek az excelből vevődnek ki
        self.Kari_tanszekek_nevei = set()  # Tanszékek neve amely az excelből vevődik ki
        self.excel_fajl = None
        self.szerzolapok_mappa = None
        self.kari_tanszekek = {}

        # a szürt publikációhoz tartozó típusnevek (fontos hogy a subtype-ban lévő típusok szerepelnek itt)
        self.valodi_publikacio_tipusok = [
            "Konferenciaközlemény (Egyéb konferenciaközlemény)",
            "Szakcikk (Folyóiratcikk)",
            "Sokszerzős vagy csoportos szerzőségű szakcikk (Folyóiratcikk)",
            "Összefoglaló cikk (Folyóiratcikk)",
            "Rövid közlemény (Folyóiratcikk)",
            "Konferenciakötet (Könyv)",
            "Szakkönyv (Könyv)",
            "Monográfia (Könyv)",
            "Konferenciaközlemény (Könyvrészlet)",
            "Szaktanulmány (Könyvrészlet)",
            "Könyvfejezet (Könyvrészlet)"
        ]

        #grafikus interfész inicializálása
        self.grafikus_interfesz_inicializalasa()

    def grafikus_interfesz_inicializalasa(self):
        # fő ablak a lapokhoz
        #Tkinker általi notebook létrehozása
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=10, pady=10) #jellemzők beállítása: padX: x tengelyen behúzás. padY: y tengelyen behúzás Fill: kitöltés a kelleténél többre

        # Első lap: Adat bevitel
        self.adatabetoltese_lap_inicializalas(notebook)
        # Második lap: Hálózat generálás
        self.halozatgeneralas_lap_inicilaizalasa(notebook)
        # Harmadik lap: Eredmények/Statisztika (majd bővíteni, módosítani)
        self.rovidelemzes_lap_inicilaizalasa(notebook)

    def adatabetoltese_lap_inicializalas(self, notebook):
        adatlap_vaz = ttk.Frame(notebook)
        notebook.add(adatlap_vaz, text="Adatbevitel") #adatbetoltes lap cimkéje nevet kap it

        # Excel fájl kiválasztás
        ttk.Label(adatlap_vaz, text="Kari Excel fájl megadása").pack(anchor='w', pady=(10, 5))
        excel_vaz = ttk.Frame(adatlap_vaz)
        excel_vaz.pack(fill='x', pady=(0, 10))

        self.kari_excel_eleresi_utvonal = ttk.Label(excel_vaz, text="Nincs kiválasztva fájl", background="white", relief="sunken")
        self.kari_excel_eleresi_utvonal.pack(side='left', fill='x', expand=True, padx=(0, 10))
        ttk.Button(excel_vaz, text="Keresés", command=self.kari_szemelyek_excel_beolvasasa).pack(side='right')

        # Adatlap mappa kiválasztás
        ttk.Label(adatlap_vaz, text="MTMT Adatlap Mappa:").pack(anchor='w', pady=(10, 5))
        adatmappa_vaz = ttk.Frame(adatlap_vaz)
        adatmappa_vaz.pack(fill='x', pady=(0, 10))

        self.adatalap_mappa_eleresi_utvonal = ttk.Label(adatmappa_vaz, text="Nincs kiválasztva mappa", background="white", relief="sunken")
        self.adatalap_mappa_eleresi_utvonal.pack(side='left', fill='x', expand=True, padx=(0, 10))
        ttk.Button(adatmappa_vaz, text="Keresés", command=self.publikaciogyujtemeny_mappa_megadasa).pack(side='right')

        # Adat betöltés gomb
        ttk.Button(adatlap_vaz, text="Publikációk betöltése", command=self.adatbetoltes).pack(pady=20)

        # Publikáció típusok exportálása gomb
        ttk.Button(adatlap_vaz, text="Publikáció típusok exportálása", command=self.publikacio_tipus_lementes).pack(pady=10)

        # Adatok összegzése
        ttk.Label(adatlap_vaz, text="Rövid adatelemzés:").pack(anchor='w', pady=(20, 5))
        self.rovid_adatelemzes = tk.Text(adatlap_vaz, height=10, width=70)
        self.rovid_adatelemzes.pack(fill='both', expand=True)


    def halozatgeneralas_lap_inicilaizalasa(self, notebook):
        # hálózatgenerálási felület létrehozása

        halozatgeneralas_vaz = ttk.Frame(notebook)
        notebook.add(halozatgeneralas_vaz, text="Hálózat generálás") # hálózatgenerálás fül létrehozása

        # Hálózat típus kiválasztás
        ttk.Label(halozatgeneralas_vaz, text="Hálózat típus:").pack(anchor='w', pady=(10, 5))
        self.halozat_tipusa = tk.StringVar(value="teljes")
        halozattipus_vaz = ttk.Frame(halozatgeneralas_vaz)
        halozattipus_vaz.pack(fill='x', pady=(0, 15))
        ttk.Radiobutton(halozattipus_vaz, text="Teljes hálózat (Minden publikáció figyelembe vétele)", variable=self.halozat_tipusa, value="teljes").pack(anchor='w') #legyen vegyes hálózat (kari és nem kari együttműködések hálózata)
        ttk.Radiobutton(halozattipus_vaz, text="Tanszékekre bontott kari hálózat (Csak a kari szerzők publikációnak figyelembe vételével készül, ahol Tanszékek a csomópontok)", variable=self.halozat_tipusa, value="tanszek_halozat").pack(anchor='w')
        ttk.Radiobutton(halozattipus_vaz, text="Oktatókra bontott kari hálózat (Csak a kari szerzők publikációnak figyelembe vételével készül, ahol a Szerzők a csomópontok)", variable=self.halozat_tipusa, value="Kari_hálózat").pack(anchor='w')

        self.csak_valodi_publikaciok = tk.BooleanVar()
        ttk.Checkbutton(halozatgeneralas_vaz, text="Csak fontosabb tudományos művek feldolgozása",
                        variable=self.csak_valodi_publikaciok).pack(anchor='w', pady=(10, 5))
        # Év alapú szűrő
        evszures_vaz = ttk.LabelFrame(halozatgeneralas_vaz, text="Év szűrés")
        evszures_vaz.pack(fill='x', pady=(0, 15))
        self.megjelenes_eve_alapu_szures = tk.BooleanVar()
        ttk.Checkbutton(evszures_vaz, text="Év szűrés:", variable=self.megjelenes_eve_alapu_szures, command=self.ev_szures_opcio).pack(anchor='w', pady=5)
        evszuro_vaz = ttk.Frame(evszures_vaz)
        evszuro_vaz.pack(fill='x', padx=10, pady=5)

        #Év alapú szürő gombjai, és határétékei
        ttk.Label(evszuro_vaz, text="Kezdet:").pack(side='left')
        self.kezdeti_ev = tk.StringVar(value="2010")
        kezdetiev_kivalaszto_vaz = ttk.Spinbox(evszuro_vaz, from_=1960, to=2030, textvariable=self.kezdeti_ev, width=8)
        kezdetiev_kivalaszto_vaz.pack(side='left', padx=(5, 15))

        ttk.Label(evszuro_vaz, text="Vég:").pack(side='left')
        self.ev_ig = tk.StringVar(value="2024")
        utolsoev_kivalaszto_vaz = ttk.Spinbox(evszuro_vaz, from_=1960, to=2030, textvariable=self.ev_ig, width=8)
        utolsoev_kivalaszto_vaz.pack(side='left', padx=5)

        # Év beállítás alapértelmezetten ne legyen bekapcsolva és a widget létrehozása
        kezdetiev_kivalaszto_vaz.configure(state='disabled')
        utolsoev_kivalaszto_vaz.configure(state='disabled')
        self.kezdetiev_widget = kezdetiev_kivalaszto_vaz
        self.utolsoev_widget = utolsoev_kivalaszto_vaz

        # Minimum közös publikáció szürő
        kozos_publikacio_vaz = ttk.LabelFrame(halozatgeneralas_vaz, text="Közös publikáció szürés")
        kozos_publikacio_vaz.pack(fill='x', pady=(0, 15))

        self.kozos_publikacio_szuro = tk.BooleanVar()
        ttk.Checkbutton(kozos_publikacio_vaz, text="Minimum közös publikációk száma:", variable=self.kozos_publikacio_szuro, command=self.kozos_egyuttmukodesek_szures_opcio).pack(anchor='w', pady=5)

        kozos_publikacio_beallito = ttk.Frame(kozos_publikacio_vaz)
        kozos_publikacio_beallito.pack(fill='x', padx=10, pady=5)

        ttk.Label(kozos_publikacio_beallito, text="Minimum:").pack(side='left')
        self.minimum_egyuttmukodesek_szama = tk.StringVar(value="2")
        minimum_egyuttmukodesek_szama_beallito = ttk.Spinbox(kozos_publikacio_beallito, from_=1, to=20, textvariable=self.minimum_egyuttmukodesek_szama, width=8)
        minimum_egyuttmukodesek_szama_beallito.pack(side='left', padx=5)
        minimum_egyuttmukodesek_szama_beallito.configure(state='disabled')
        self.minimum_egyuttmukodesek_szama_widget = minimum_egyuttmukodesek_szama_beallito

        # Kimeneti beállítások
        kimeneti_beallitasok_vaz = ttk.LabelFrame(halozatgeneralas_vaz, text="Kimeneti beállítások")
        kimeneti_beallitasok_vaz.pack(fill='x', pady=(0, 15))
        ttk.Label(kimeneti_beallitasok_vaz, text="Kimeneti fájl prefixje:").pack(anchor='w', pady=5)
        self.kimeneti_fajl_prefixje = tk.StringVar(value="Hálózat")
        ttk.Entry(kimeneti_beallitasok_vaz, textvariable=self.kimeneti_fajl_prefixje, width=30).pack(anchor='w', padx=10, pady=(0, 10))

        # Hálózat generálás gomb
        self.halozat_generalas_gomb_vaz = ttk.Button(halozatgeneralas_vaz, text="Hálózat fájl generálása", command=self.halozat_generalas_szalon)
        self.halozat_generalas_gomb_vaz.pack(pady=20)

        # Folyamat csík
        self.folyamatcsik_vaz = ttk.Progressbar(halozatgeneralas_vaz, mode='indeterminate')
        self.folyamatcsik_vaz.pack(fill='x', pady=10)

    def rovidelemzes_lap_inicilaizalasa(self, notebook):
        eredmenyek_lap_vaz = ttk.Frame(notebook)
        notebook.add(eredmenyek_lap_vaz, text="Eredmények/Statisztika")
        ttk.Label(eredmenyek_lap_vaz, text="Generálás eredménye:").pack(anchor='w', pady=(10, 5))
        self.eredmenyek_szovege_vaz = tk.Text(eredmenyek_lap_vaz, height=20, width=70)
        self.eredmenyek_szovege_vaz.pack(fill='both', expand=True)

        # Görgető
        gorgeto_vaz = ttk.Scrollbar(eredmenyek_lap_vaz, orient="vertical", command=self.eredmenyek_szovege_vaz.yview)
        gorgeto_vaz.pack(side="right", fill="y")
        self.eredmenyek_szovege_vaz.configure(yscrollcommand=gorgeto_vaz.set)

    def ev_szures_opcio(self):
        #Év alapú szűres opció bekapcsolása használathoz
        state = 'normal' if self.megjelenes_eve_alapu_szures.get() else 'disabled'
        self.kezdetiev_widget.configure(state=state)
        self.utolsoev_widget.configure(state=state)

    def kozos_egyuttmukodesek_szures_opcio(self):
        # mimimum közös publikáció alapú szürés opció bekapcsolása használathoz
        state = 'normal' if self.kozos_publikacio_szuro.get() else 'disabled'
        self.minimum_egyuttmukodesek_szama_widget.configure(state=state)


    def kari_szemelyek_excel_beolvasasa(self):
        #kari személyeket tartalmazó excel beolvasására szolgáló ablkakpont
        kariexcel_nev = filedialog.askopenfilename(
            title="Kari személyeket tartalmazó Excel fájl kiválasztása",
            filetypes=[("Excel fájl", "*.xlsx *.xls")])

        if kariexcel_nev:
            self.excel_fajl = kariexcel_nev # excel fájl neve
            self.kari_excel_eleresi_utvonal.configure(text=os.path.basename(kariexcel_nev)) # excel elérési útvonala

    def publikaciogyujtemeny_mappa_megadasa(self):
        #MTMT-ből összeszedett publikációkat tartalmazó főmappa kiválasztására szolgáló ablakpont
        publikaciogyujtemeny_mappanev = filedialog.askdirectory(title="MTMT adatlap mappa kiválasztása")
        if publikaciogyujtemeny_mappanev:
            #főmappa adatait átmentjük: név és elérési út
            self.szerzolapok_mappa = publikaciogyujtemeny_mappanev
            self.adatalap_mappa_eleresi_utvonal.configure(text=os.path.basename(publikaciogyujtemeny_mappanev))

    def adatbetoltes(self):
        #Excelből lévő szerző adatok beolvasása

        if not self.excel_fajl or not self.szerzolapok_mappa:
            messagebox.showerror("Hiba", "Kérlek válaszd ki az Excel és az adatlapokat tartalmazó mappát!")
            return

        try:
            # Kari adatlap(Excel) betöltése
            kari_adatlap = pd.read_excel(self.excel_fajl, sheet_name="Munka1")
            # MTID Beolvasás
            nev_oszlop = kari_adatlap.columns[0] #A oszlop
            mtid_oszlop = kari_adatlap.columns[1]  # B oszlop , 1-es index(2.sor)
            tanszek_oszlop = kari_adatlap.columns[3]

            self.karhoz_tartozo_mtidk = set()
            self.kari_tanszekek = {}
            self.kari_szerzonevek = {}

            # Tanszékekről készítünk egy "szótárat"
            for _, row in kari_adatlap.iterrows():
                mtid = row[mtid_oszlop]
                if pd.notna(mtid):
                    mtid_erteke = int(mtid) #nem lehet string wrap, majd fix., 3.13.7 miatt warning .5-ben jó.
                    self.karhoz_tartozo_mtidk.add(mtid_erteke)
                    # Excelből a szerzőnevek kivétele és szótárba helyezése
                    excel_szerzo_teljesnev = str(row[nev_oszlop]).strip()
                    self.kari_szerzonevek[mtid_erteke] = excel_szerzo_teljesnev
                    # Tanszéknevek kimentése excelből
                    if pd.notna(row[tanszek_oszlop]):
                        self.kari_tanszekek[mtid_erteke] = str(row[tanszek_oszlop]).strip()

            # Tanszék beolvasás
            self.Kari_tanszekek_nevei = set(kari_adatlap[tanszek_oszlop].dropna().astype(str).str.strip())
            print(f"{len(self.karhoz_tartozo_mtidk)} Kari MTID betöltve.")
            print(f"Betöltött tanszékek:")
            for inst in sorted(self.Kari_tanszekek_nevei):
                print(f" - {inst}")

            # Publikációk betöltése
            self.publikaciok = self.publikaciok_osszegyujtese(self.szerzolapok_mappa)

            # Összegzés frissítése
            self.adatosszegzes_frissitese()
            messagebox.showinfo("Kész!", f"{len(self.publikaciok)} publikáció sikeresen betöltve!")

        except Exception as e:
            messagebox.showerror("Hiba!", f"Nem sikerült az adatok betöltése: {str(e)}")

    def publikaciok_osszegyujtese(self, root_folder):
        # publikációk feldolgozása
        kesz_idk = set()
        minden_publikacio = []

        for mappa_utvonal, _, fajl_nevek in os.walk(root_folder):
            for fajlnev in fajl_nevek:
                if fajlnev.endswith(".json"):
                    eleresi_ut = os.path.join(mappa_utvonal, fajlnev)
                    try:
                        publikaciok = self.mtmtfajl_olvasasa(eleresi_ut)
                        for publikacio in publikaciok:
                            publikacio_azonosito = self.publikacio_azonositok_kinyerese(publikacio)
                            if publikacio_azonosito not in kesz_idk:
                                kesz_idk.add(publikacio_azonosito)
                                feldolgozott_publikaciok = self.publikaciok_feldogozasa(publikacio)
                                minden_publikacio.append(feldolgozott_publikaciok)
                    except Exception as e:
                        print(f"Hiba történt {eleresi_ut} útvonal olvasása közben: {e}")
        return minden_publikacio

    @staticmethod
    def mtmtfajl_olvasasa(fajl_eleresi_utvonala):
        #beolvassa az mtmt-ről leszedett szerzői fájlt
        with open(fajl_eleresi_utvonala, "r", encoding="utf-8") as fajl:
            beolvasott_adat = json.load(fajl)
            return beolvasott_adat.get("content", [])

    @staticmethod
    def publikacio_azonositok_kinyerese(publikacio):
        #publikacióslista fájlból kiszedjük az azonosítókat
        digitalis_azonosito = None
        mtid = publikacio.get("mtid")
        for azonosito in publikacio.get("identifiers", []):
            if "DOI" in azonosito.get("label", ""):
                digitalis_azonosito = azonosito.get("idValue")
                break
        return digitalis_azonosito or f"MTID_{mtid}"


    def publikaciok_feldogozasa(self, publikacio):
        #publikacióslista fájlból kiszedjük a számunkra fontos adatokat
        szerzo_informaciok = self.szerzok_kigyujtese(publikacio)
        return {
            "Publikácio_mtid": publikacio.get("mtid"),
            "Publikáció_azonosító": self.publikacio_azonositok_kinyerese(publikacio), #az előző fg. return értékét írja ide
            "Publikáció címe": publikacio.get("title"),
            "Publikálás éve": publikacio.get("publishedYear"),
            "Típus": {
                "Általános": publikacio.get("type", {}).get("label"), #type tömbön belül a label mező adatát szedi ki mint típus
                "Altípus": publikacio.get("subType", {}).get("label") #subtype tömbön belüli label mező adatát szedi ki mint altípus
            },



            "Szerzőinformációk": {
                "Összes_szerzők_száma": szerzo_informaciok["Összes_szerzők_száma"],
                "Kari_szerzők_száma": szerzo_informaciok["Kari_szerzők_száma"],
                "Kari_szerzők": szerzo_informaciok["Kari_szerzők"],
                "Minden_szerző": szerzo_informaciok["Minden_szerző"]
            },
            "kulcsszavak": [kulcsszo.get("label") for kulcsszo in publikacio.get("keywords", [])], #  jelenleg nem használt
            "Nyelv": publikacio.get("languages", [{}])[0].get("label", "Ismeretlen"), #  jelenleg nem használt
            "Kategória": publikacio.get("category", {}).get("label"), # jelenleg nem használt
            "Hivatkozások_száma": publikacio.get("citationCount", 0), #  jelenleg nem használt
        }




    def szerzok_kigyujtese(self, publikacio):
        #Publikacio szerzőinek kigyüjtése
        kari_szerzok_listaja = []
        minden_szerzo_listaja = []
        szerzok = publikacio.get("authorships", [])
        osszes_szerzok_szama = len(szerzok)
        kari_szerzok_szama = 0

        for szerzo in szerzok:
            szerzo_mtid = szerzo.get("author", {}).get("mtid")
            eredeti_tanszek = szerzo.get("label", "").split("]")[-1].strip() if "]" in szerzo.get("label", "") else None

            #Tanszék megadásához használjuk az excelbel lévőt, ha kari személyről van szó, más esetben szerzo fájlból kinyertet.
            tanszek_vegleges = self.kari_tanszekek.get(szerzo_mtid, eredeti_tanszek) if szerzo_mtid else eredeti_tanszek

            #Név kiemelése az excelből
            if szerzo_mtid in self.kari_szerzonevek:
                # A nevet szerzo kari oktatók esetében az excelből vegye ki.
                teljes_nev = self.kari_szerzonevek[szerzo_mtid]

                #nevek szétvágásap
                nev_reszek = teljes_nev.split(' ',1)
                if len(nev_reszek) > 1:
                    vezeteknev = nev_reszek[0]
                    keresztnev = nev_reszek[1]
                else:
                    vezeteknev = nev_reszek[0]
                    keresztnev = ""
                    teljes_nev = f"{vezeteknev} {keresztnev}".strip()
            else:
                # Ha nem kari személyről van szó akkor az mtmt-s névrészekből rakja össze szerzo nevet.
                vezeteknev = szerzo.get("familyName", "")
                keresztnev = szerzo.get("givenName", "")
                teljes_nev = f"{vezeteknev} {keresztnev}".strip()

            szerzo_informaciok = {
                "Név": teljes_nev,
                "Vezetéknév": vezeteknev,
                "Keresztnév": keresztnev,
                "mtid": szerzo_mtid,
                "felelősszerző-e": szerzo.get("corresponding", False), # a felesős szerző-e( true/false szerzo fájlban)
                "Tanszék": tanszek_vegleges
            }

            minden_szerzo_listaja.append(szerzo_informaciok)

            if szerzo_mtid in self.karhoz_tartozo_mtidk:
                kari_szerzok_szama += 1
                kari_szerzok_listaja.append(szerzo_informaciok)

        return {
            "Összes_szerzők_száma": osszes_szerzok_szama,
            "Kari_szerzők_száma": kari_szerzok_szama,
            "Kari_szerzők": kari_szerzok_listaja,
            "Minden_szerző": minden_szerzo_listaja
        }

#idezesek szamat kiemelő metódus
    def szerzo_idezetteseg_szamlalo(self, publikaciok, szerzok):
        #Összeadja az összes publikációból a idézések számát és lementi a személyekhez, akik a karon dolgoznak.
        for mtid in szerzok:
            szerzok[mtid]["Hivatkozások_száma"] = 0
        for publikacio in publikaciok:
            hivatkozasok_szama=publikacio.get("Hivatkozások_száma",0)
            minden_szerzo=publikacio["Szerzőinformációk"]["Minden_szerző"]

            for szerzo in minden_szerzo:
                mtid=szerzo.get("mtid")
                if mtid and mtid in szerzok:
                    szerzok[mtid]["Hivatkozások_száma"]+=hivatkozasok_szama

        return  szerzok

        #publikációs típusok kigyüjtése
    def publikacio_tipuskigyujto(self):

        publikacio_tipusok = defaultdict(int)
        publikacio_altipusok = defaultdict(int)

        for publikacio in self.publikaciok:
            publikacio_tipus = publikacio.get("Típus", {})
            if isinstance(publikacio_tipus, dict):  # szürt publikációk kezelése a publikációtípus lista alapján
                altalanos = publikacio_tipus.get("Általános")
                specifikus = publikacio_tipus.get("Altípus")

                if altalanos:
                    publikacio_tipusok[altalanos]+=1
                if specifikus:
                    publikacio_altipusok[specifikus]+=1

            #rendezett lista--> tuple
        rendezett_tipusok = sorted(publikacio_tipusok.items(), key=lambda x: (-x[1], x[0]))
        rendezett_altipusok = sorted(publikacio_altipusok.items(), key=lambda x: (-x[1], x[0]))

        return rendezett_tipusok, rendezett_altipusok

    def adatosszegzes_frissitese(self):
        if not self.publikaciok:
            return

        osszes_publikacio = len(self.publikaciok)
        kari_szerzok_szama = len(self.karhoz_tartozo_mtidk)

        # Év köz
        ev_lista = [publikacio["Publikálás éve"] for publikacio in self.publikaciok if publikacio["Publikálás éve"]]
        ev_tartomany = f"{min(ev_lista)}-{max(ev_lista)}" if ev_lista else "Ismeretlen év"

        # Kari publikációk
        kari_publikaciok = sum(1 for p in self.publikaciok if p["Szerzőinformációk"]["Kari_szerzők_száma"] > 0)

        # Tiszta Kari publikációk (csak kari szerzők által)
        tiszta_kari_publikaciok  = sum(1 for publikacio in self.publikaciok
                                if publikacio["Szerzőinformációk"]["Kari_szerzők_száma"] > 0 and
                                publikacio["Szerzőinformációk"]["Kari_szerzők_száma"] == publikacio["Szerzőinformációk"]["Összes_szerzők_száma"])

        osszegzes = f"""
Betöltött publikációk száma: {osszes_publikacio}
Kari szerzők száma: {kari_szerzok_szama}
Kari tanszékek száma: {len(self.Kari_tanszekek_nevei)}
Év köz: {ev_tartomany}

Publikáció statisztikák:
- Publikációk kari vonatkozással: {kari_publikaciok}
- Tiszta kari publikációk: {tiszta_kari_publikaciok }
- Vegyes publikációk(előző 2 külömbsége): {kari_publikaciok - tiszta_kari_publikaciok }

Kész az adatok betöltése!
        """
# 2025.09.19. a doglozatban lényegében eddig lett leírva mit csinál a program.
        self.rovid_adatelemzes.delete(1.0, tk.END)
        self.rovid_adatelemzes.insert(1.0, osszegzes.strip())

    def publikaciok_szurese(self):
        #Publikációk szűrése

        szurt = self.publikaciok.copy()

        #Év szűrő
        if self.megjelenes_eve_alapu_szures.get():
            ev_tol = int(self.kezdeti_ev.get())
            ev_ig = int(self.ev_ig.get())
            szurt = [publikacio for publikacio in szurt if publikacio["Publikálás éve"] and ev_tol <= publikacio["Publikálás éve"] <= ev_ig]

        if self.csak_valodi_publikaciok.get():
            szurt = [
                publikacio for publikacio in szurt
                if publikacio.get("Típus", {}).get("Altípus") in self.valodi_publikacio_tipusok]

        return szurt

    def halozat_generalas_szalon(self):
        #Hálózat generálás más szálon való futtatás

        if not self.publikaciok:
            messagebox.showerror("Hiba!", "Kérlek tölsd be az adatokat a generálás elött!")
            return

        self.halozat_generalas_gomb_vaz.configure(state='disabled')
        self.folyamatcsik_vaz.start()

        szal = threading.Thread(target=self.halozat_elkeszitese)
        szal.daemon = True
        szal.start()

    def halozat_elkeszitese(self):

        try:
            # pulikációk szűrése
            szurt_publikaciok = self.publikaciok_szurese()

            # Hálózat generálás típus alapján
            halozattipus = self.halozat_tipusa.get()

            if halozattipus == "teljes":
                szerzok, egyuttmukodesek = self.tejles_halozat_generalas(szurt_publikaciok)
            elif halozattipus == "tanszek_halozat":
                # kari hálózat a tanszékekkel(csomópontok az IKs tanszékek
                szerzok, egyuttmukodesek = self.tanszeki_halozat_generalas(szurt_publikaciok)
            else:  # Kari hálózat személyekkel( csak IK-s személyek)
                szerzok, egyuttmukodesek = self.kari_halozat_generalas(szurt_publikaciok)

            # közös publikációszám szűrő
            if self.kozos_publikacio_szuro.get():
                minimum_egyuttmukodesek = int(self.minimum_egyuttmukodesek_szama.get())
                egyuttmukodesek = {kulcs: ertek for kulcs, ertek in egyuttmukodesek.items() if ertek >= minimum_egyuttmukodesek}

            # fájlok generálása
            prefix = self.kimeneti_fajl_prefixje.get()
            self.cytoscape_csvk_generalasa(szerzok, egyuttmukodesek,f"{prefix}_csomopontok.csv", f"{prefix}_elek.csv")
            # Adatfrissítés
            self.root.after(0, self.eredmenyek_frissitese, szerzok, egyuttmukodesek, szurt_publikaciok, halozattipus)

        except Exception as e:
            error_msg = f"Hálózat generálás sikertelen: {str(e)}"
            self.root.after(0, lambda msg=error_msg: messagebox.showerror("Hiba!", msg))
        finally:
            self.root.after(0, self.generalas_befelyezese)

    def tejles_halozat_generalas(self, publikaciok):
        #Teljes(minden szerzős) hálózat generálása

        szerzok = {}
        egyuttmukodesek_szama = defaultdict(int)

        for publikacio in publikaciok:
            ervenyes_szerzok = []
            for szerzo in publikacio["Szerzőinformációk"]["Minden_szerző"]:
                if szerzo["mtid"]:
                    mtid = szerzo["mtid"]
                    if mtid not in szerzok:
                        szerzok[mtid] = {
                            "mtid": mtid,
                            "Név": szerzo["Név"],
                            "Vezetéknév": szerzo["Vezetéknév"],
                            "Keresztnév": szerzo["Keresztnév"],
                            "Publikációk_száma": 0,
                            "Kari-e": mtid in self.karhoz_tartozo_mtidk,
                            "Tanszék": set()
                        }

                    szerzok[mtid]["Publikációk_száma"] += 1
                    if szerzo.get("Tanszék"):
                        szerzok[mtid]["Tanszék"].add(szerzo["Tanszék"])
                    ervenyes_szerzok.append(mtid)

            # Közös munka generálás: kapcsolat
            for szerzo1, szerzo2 in combinations(ervenyes_szerzok, 2):
                el_kulcs = tuple(sorted([szerzo1, szerzo2]))
                egyuttmukodesek_szama[el_kulcs] += 1

        #szerzok frissitése idézések számával
        szerzok = self.szerzo_idezetteseg_szamlalo(publikaciok, szerzok)
        return szerzok, egyuttmukodesek_szama

    def tanszeki_halozat_generalas(self, publikaciok):
        #Kari hálózat generálása, tanszékre osztva

        tanszekek = {}
        egyuttmukodesek_szama = defaultdict(int)

        # Előfeldolgozás

        kari_tanszeknev_lower = {instancia.lower(): instancia for instancia in self.Kari_tanszekek_nevei}

        for publikacio in publikaciok:
            if publikacio["Szerzőinformációk"]["Kari_szerzők_száma"] == 0:
                continue

            minden_szerzo = publikacio["Szerzőinformációk"]["Minden_szerző"]
            ervenyes_kari_szerzok = []

            for szerzo in minden_szerzo:
                tanszek_nev = szerzo.get("Tanszék", "")
                if not tanszek_nev:
                    # Tanszék nélküli szerző átugrása
                     continue #break

                # tanszék keresés
                megtalalt = False
                for excel_talalat_lower, excel_talalat in kari_tanszeknev_lower.items():
                    if excel_talalat_lower in tanszek_nev.lower():
                        # tanszék név használat excelből
                        szerzo["Parositott_tanszek"] = excel_talalat
                        megtalalt = True
                        continue #break

                if not megtalalt:
                    # Nem találtunk párosítható tanszéket
                    continue #break

                ervenyes_kari_szerzok.append(szerzo)

            # Csoportosítás a duplikációk elkerülése végett
            if len(ervenyes_kari_szerzok) == len(minden_szerzo):
                # csoportosítás
                pub_tanszekek = set()
                for szerzo in ervenyes_kari_szerzok:
                    tanszek = szerzo["Parositott_tanszek"]
                    pub_tanszekek.add(tanszek)

                    # tanszék infó frissítés
                    if tanszek not in tanszekek:
                        tanszekek[tanszek] = {
                            "mtid": tanszek,
                            "Név": tanszek,
                            "Vezetéknév": tanszek.split()[-1] if tanszek != "Ismeretlen Tanszék" else "Ismeretlen",
                            "Keresztnév": tanszek.split()[0] if tanszek != "Ismeretlen Tanszék" else "Ismeretlen",
                            "Publikációk_száma": 0,
                            "Kari-e": True,
                            "Tanszék": {tanszek}
                        }
                    tanszekek[tanszek]["Publikációk_száma"] += 1

                # tanszék-együttműködések elkészítése
                if len(pub_tanszekek) > 1:
                    for tanszek1, tanszek2 in combinations(pub_tanszekek, 2):
                        el_kulcs = tuple(sorted([tanszek1, tanszek2]))
                        egyuttmukodesek_szama[el_kulcs] += 1
        # tanszéki adatok frissitése idézések számával
        tanszekek = self.szerzo_idezetteseg_szamlalo(publikaciok, tanszekek)
        return tanszekek, egyuttmukodesek_szama

    def kari_halozat_generalas(self, publikaciok):
        # Minden kari személy bevezetése a hálózatba

        szerzok = {
            mtid: {
            "mtid": mtid,
            "Név": "",
            "Vezetéknév": "",
            "Keresztnév": "",
            "Publikációk_száma": 0,
            "Kari-e": True,
            "Tanszék": set()
        } for mtid in self.karhoz_tartozo_mtidk}

        egyuttmukodesek_szama = defaultdict(int)

        # Publikációkból kiszedjük a szerzők neveit
        for publikacio in publikaciok:
            for szerzo in publikacio["Szerzőinformációk"]["Minden_szerző"]:
                mtid = szerzo.get("mtid")
                if mtid in szerzok:
                    # Szerzőadatok frissítése a fájlokból
                    if not szerzok[mtid]["Név"]:  # Csak akkor frissítsük ha még nem találtuk meg
                        szerzok[mtid].update({
                            "Név": szerzo["Név"],
                            "Vezetéknév": szerzo["Vezetéknév"],
                            "Keresztnév": szerzo["Keresztnév"]
                        })
                    if szerzo.get("Tanszék"):
                        szerzok[mtid]["Tanszék"].add(szerzo["Tanszék"])

        # Publikációk és együttműködések megszámolása
        for publikacio in publikaciok:
            # kari szerzők összeszedése
            kari_publikaciok = [a for a in publikacio["Szerzőinformációk"]["Minden_szerző"]
                                if a.get("mtid") in self.karhoz_tartozo_mtidk]

            # munkák megszámolása személyenként
            for szerzo in kari_publikaciok:
                mtid = szerzo["mtid"]
                szerzok[mtid]["Publikációk_száma"] += 1

            # személyek közötti együttműködések létrehozása
            kari_mtidk_publikaciokban = {a["mtid"] for a in kari_publikaciok}
            for szerzo1, szerzo2 in combinations(kari_mtidk_publikaciokban, 2):
                el_kulcs = tuple(sorted([szerzo1, szerzo2]))
                egyuttmukodesek_szama[el_kulcs] += 1

            # szerzok frissitése idézések számával
            szerzok = self.szerzo_idezetteseg_szamlalo(publikaciok, szerzok)
        return szerzok, egyuttmukodesek_szama
    def publikacio_tipus_lementes(self):

        if not self.publikaciok:
            messagebox.showerror("Hiba", "Nincsenek betöltött publikációk!")
            return

        try:
            altalanos_tipusok, altipusok = self.publikacio_tipuskigyujto()

            # Rövidebb lista megtoldása hogy azonos hosszúságú legyen
            max_hosszusag = max(len(altalanos_tipusok), len(altipusok))
            adat = {
                "Általános_típus": [t[0] for t in altalanos_tipusok] + [''] * (max_hosszusag - len(altalanos_tipusok)),
                "Általános_típus előfordulása": [t[1] for t in altalanos_tipusok] + [''] * (max_hosszusag - len(altalanos_tipusok)),
                "Specifikus_altípus": [t[0] for t in altipusok] + [''] * (max_hosszusag - len(altipusok)),
                "Specifikus_altípus előfordulása": [t[1] for t in altipusok] + [''] * (max_hosszusag - len(altipusok))
            }

            # Publikációtípusok kimentésére dataframe készítés
            publikaciotipusok_df = pd.DataFrame(adat)

            # Mentési hely bekérése
            fajl_utvonal = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel fájl", "*.xlsx"), ("CSV fájl", "*.csv")],
                title="Publikációtípusok mentési helye: "
            )

            if fajl_utvonal:
                if fajl_utvonal.endswith('.csv'):
                    publikaciotipusok_df.to_csv(fajl_utvonal, index=False, encoding='utf-8-sig')
                else:
                    publikaciotipusok_df.to_excel(fajl_utvonal, index=False)

                messagebox.showinfo("Kész", "A publikációtípusok sikeresen exportálva lettek!")

        except Exception as e:
            messagebox.showerror("Hiba", f"Hiba történt a publikációtípusok exportálás közben: {str(e)}")

        # Cytoscape fájlok generálása
    @staticmethod
    def cytoscape_csvk_generalasa(szerzok, egyuttmukodesek_szama, csomopont_fajl, el_fajl):

        # Csomópont adatok létrehozása
        csomopont_adatok = []
        for mtid, info in szerzok.items():
            tanszek_nev = "; ".join(info["Tanszék"]) if info["Tanszék"] else "Ismeretlen_Tanszéknév"

            csomopont_adatok.append({
                "id": mtid,
                "mtid": mtid,
                "Név": info["Név"],
                "Vezetéknév": info["Vezetéknév"],
                "Keresztnév": info["Keresztnév"],
                "Publikációk_száma": info["Publikációk_száma"],
                "Gyök_Publikációk_száma": info["Publikációk_száma"]** 0.5,
                "Hivatkozások_száma":info.get("Hivatkozások_száma", 0),
                "Kari-e": info["Kari-e"],
                "Tanszék": tanszek_nev,
            })

        #Összekötési adatok
        el_adatok = []
        for (szerzo1, szerzo2), suly in egyuttmukodesek_szama.items():
            elsoszerzo = szerzok[szerzo1]
            masodikszerzo = szerzok[szerzo2]

            if elsoszerzo["Kari-e"] and masodikszerzo["Kari-e"]:
                kari_kapcsolat = "belsős"
            elif elsoszerzo["Kari-e"] or masodikszerzo["Kari-e"]:
                kari_kapcsolat = "vegyes"
            else:
                kari_kapcsolat = "külsős"

            tanszek1 = elsoszerzo["Tanszék"]
            tanszek2 = masodikszerzo["Tanszék"]

            if tanszek1 == tanszek2 and tanszek1 != "Ismeretlen_Tanszék":
                tanszeki_kapcsolat = "tanszéken belüli"
            else:
                tanszeki_kapcsolat = "tanszékek közti"
            el_adatok.append({
                "source": szerzo1, # marad angol cytoscape miatt
                "target": szerzo2, # marad angol cytoscape miatt
                "Közös_publikációk_száma": suly,
                "Kari_kapcsolat": kari_kapcsolat,
                "Tanszéki_kapcsolat": tanszeki_kapcsolat
            })

        # CSV fájlba mentés
        csomopontok_df = pd.DataFrame(csomopont_adatok)
        elek_df = pd.DataFrame(el_adatok)
        csomopontok_df.to_csv(csomopont_fajl, index=False, encoding='utf-8-sig')
        elek_df.to_csv(el_fajl, index=False, encoding='utf-8-sig')

    def eredmenyek_frissitese(self, szerzok, egyuttmukodesek, szurt_publikaciok, halozat_tipusa):
        minden_szerzo_szama = len(szerzok)
        kari_szerzok_szama = sum(1 for a in szerzok.values() if a["Kari-e"])
        kulsos_szerzok_szama = minden_szerzo_szama - kari_szerzok_szama
        egyuttmukodesek_szama = len(egyuttmukodesek)
        osszes_sulyozott_egyuttmukodesek_szama = sum(egyuttmukodesek.values())

        # Legtöbbet publikáló szerző
        legtermekenyebb = sorted(szerzok.items(), key=lambda x: x[1]["Publikációk_száma"], reverse=True)[:5]
        legszorosabb_egyuttmukodes = sorted(egyuttmukodesek.items(), key=lambda x: x[1], reverse=True)[:5]

#végső eredmények kiíratása
        eredmenyek = f"""
=== HÁLÓZAT GENERÁLÁS EREDMÉNYEI ===

Hálózat típusa: {halozat_tipusa.replace('_', ' ').title()}
Használt publikációk száma: {len(szurt_publikaciok)}
Alkalmazott szürések:
- Év szűrés: {'Igen' if self.megjelenes_eve_alapu_szures.get() else 'Nem'}
- Közös publikációszám szűrés: {'Igen' if self.kozos_publikacio_szuro.get() else 'Nem'}

HÁLÓZAT STATISZTIKÁK:
Szerzők száma: {minden_szerzo_szama}
  - Kari szerzők száma: {kari_szerzok_szama}
  - Külsős szerzők száma: {kulsos_szerzok_szama}
Összes egyedi együtműködések száma: {egyuttmukodesek_szama}
Hálózat súlya: {osszes_sulyozott_egyuttmukodesek_szama}

TOP 5 LEGTERMÉKYENEBB SZERZŐ:
"""

        for mtid, info in legtermekenyebb:
            eredmenyek += f"  {info['Név']}: {info['Publikációk_száma']} publikáció\n"

        eredmenyek += "\nTOP 5 LEGGYAKORIBB EGYÜTTMŰKÖDÉS:\n"
        for (author1, author2), count in legszorosabb_egyuttmukodes:
            nev1 = szerzok[author1]["Név"]
            nev2 = szerzok[author2]["Név"]
            eredmenyek += f"  {nev1} <-> {nev2}: {count} együttműködés\n"

        eredmenyek += f"\nGenerált fájlok: {self.kimeneti_fajl_prefixje.get()}_csomopontok.csv, {self.kimeneti_fajl_prefixje.get()}_elek.csv"

        self.eredmenyek_szovege_vaz.delete(1.0, tk.END)
        self.eredmenyek_szovege_vaz.insert(1.0, eredmenyek)

    def generalas_befelyezese(self):
            self.folyamatcsik_vaz.stop()
            self.halozat_generalas_gomb_vaz.configure(state='normal')

if __name__ == "__main__":
        gyoker = tk.Tk()
        program = HalozatGeneraloGrafikusFelulettel(gyoker)
        gyoker.mainloop()