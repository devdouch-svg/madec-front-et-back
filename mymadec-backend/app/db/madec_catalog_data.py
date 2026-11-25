"""
MADEC catalogue — gammes, familles, marques (sous-familles) et produits démo.

Sources:
  https://www.madec.ma/marques-madec-food.html
  https://www.madec.ma/marques-madec-non-food.html
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ProductSeed:
    code: str
    name: str
    description: str
    unit: str = "u"
    price: float = 0.0
    discount: float = 0.0
    psg: str = "FOOD"
    society: str = "MADEC"


@dataclass
class FamilleSeed:
    name: str
    sous_familles: list[str]
    products: list[ProductSeed] = field(default_factory=list)


@dataclass
class GammeSeed:
    name: str
    familles: list[FamilleSeed]


# fmt: off
MADEC_CATALOG: list[GammeSeed] = [
    GammeSeed("Alimentaire", [
        FamilleSeed("Aides culinaires", ["Ideal", "Assila"], [
            ProductSeed("IDEAL-LEV-001", "Levure pâtissière Idéal 11g x10", "Levure pour pâtisserie", "bt", 12.50),
            ProductSeed("ASS-SAU-001", "Sauce tomate Assila 400g", "Sauce tomate cuisinée", "u", 9.90),
            ProductSeed("ASS-HAR-001", "Harissa Assila 380g", "Harissa traditionnelle", "u", 14.00),
        ]),
        FamilleSeed("Condiments et sauces", ["Del Pacha"], [
            ProductSeed("DP-KET-001", "Ketchup Del Pacha 500g", "Ketchup tomate", "u", 18.00),
            ProductSeed("DP-MAY-001", "Mayonnaise Del Pacha 470g", "Mayonnaise", "u", 16.50),
        ]),
        FamilleSeed("Bouillons", ["Damti"], [
            ProductSeed("DAM-BOU-001", "Bouillon cube poulet Damti x24", "Bouillon cube poulet", "bt", 18.90),
            ProductSeed("DAM-BOU-002", "Bouillon cube légumes Damti bio x12", "Bouillon bio légumes", "bt", 14.50),
            ProductSeed("DAM-BOU-003", "Bouillon cube bœuf Damti x24", "Bouillon cube bœuf", "bt", 18.90),
        ]),
        FamilleSeed("Confitures et conserves", ["El Baraka"], [
            ProductSeed("EBK-CONF-001", "Confiture fraise El Baraka 430g", "Confiture extra fraise", "u", 32.50),
            ProductSeed("EBK-CONF-002", "Confiture abricot El Baraka 430g", "Confiture extra abricot", "u", 32.50, 5),
            ProductSeed("EBK-CONF-003", "Confiture figue El Baraka 430g", "Confiture extra figue", "u", 34.00),
        ]),
        FamilleSeed("Conserves fruits et légumes", ["El Baraka"], [
            ProductSeed("EBK-LEG-001", "Petits pois El Baraka 400g", "Petits pois extra fins", "u", 11.00),
            ProductSeed("EBK-LEG-002", "Maïs doux El Baraka 300g", "Maïs doux en grains", "u", 10.50),
        ]),
        FamilleSeed("Conserves de poisson", ["El Baraka"], [
            ProductSeed("EBK-POIS-001", "Thon à l'huile El Baraka 170g", "Thon à l'huile végétale", "u", 16.80),
            ProductSeed("EBK-POIS-002", "Sardines à l'huile El Baraka 125g", "Sardines à l'huile", "u", 9.50),
        ]),
        FamilleSeed("Chocolat et boissons", ["Chocao"], [
            ProductSeed("CHOC-001", "Chocao poudre chocolatée 400g", "Boisson cacaotée instantanée", "u", 28.00, 10),
            ProductSeed("CHOC-002", "Chocao poudre 200g", "Format familial réduit", "u", 16.00),
        ]),
        FamilleSeed("Vinaigre", ["MADEC"], [
            ProductSeed("VIN-001", "Vinaigre blanc 1L", "Vinaigre blanc alimentaire", "u", 8.50),
            ProductSeed("VIN-002", "Vinaigre de cidre 50cl", "Vinaigre de cidre", "u", 12.00),
        ]),
        FamilleSeed("Colorants alimentaires", ["La Chaîne"], [
            ProductSeed("LC-COL-001", "Colorant alimentaire rouge 28ml", "Colorant synthétique rouge", "u", 6.90),
            ProductSeed("LC-COL-002", "Colorant alimentaire jaune 28ml", "Colorant synthétique jaune", "u", 6.90),
        ]),
        FamilleSeed("Épices", ["MADEC"], [
            ProductSeed("EP-CUM-001", "Cumin moulu 100g", "Cumin moulu", "u", 12.00),
            ProductSeed("EP-PAP-001", "Paprika doux 100g", "Paprika doux", "u", 11.50),
            ProductSeed("EP-CAN-001", "Cannelle moulue 50g", "Cannelle moulue", "u", 9.00),
        ]),
        FamilleSeed("Crèmes végétales", ["Mayfine"], [
            ProductSeed("MAY-CRE-001", "Crème végétale cuisine 200ml", "Crème végétale légère", "u", 15.50),
            ProductSeed("MAY-CRE-002", "Crème végétale fouettée 250ml", "Crème à fouetter", "u", 17.00),
        ]),
        FamilleSeed("Confiserie et gourmandises", ["Jelly", "Chobedo"], [
            ProductSeed("JEL-BON-001", "Bonbons Jelly assortis 150g", "Bonbons gélifiés", "u", 8.00),
            ProductSeed("CHO-GOU-001", "Barre chocolatée Chobedo 30g x12", "Barres chocolatées", "bt", 24.00),
        ]),
        FamilleSeed("Biscuits sucrés", ["Delicio"], [
            ProductSeed("DEL-BIS-001", "Biscuits fourrés chocolat 300g", "Biscuits chocolat", "u", 22.00),
            ProductSeed("DEL-CAK-001", "Cake chocolat Delicio 250g", "Cake moelleux chocolat", "u", 19.50),
        ]),
        FamilleSeed("Biscuits salés", ["Temtem"], [
            ProductSeed("TEM-BIS-001", "Biscuits salés méditerranéens 200g", "Biscuits apéritif", "u", 13.00),
            ProductSeed("TEM-BIS-002", "Crackers Temtem 300g", "Crackers salés", "u", 14.50),
        ]),
    ]),
    GammeSeed("Non alimentaire", [
        FamilleSeed("Gel nettoyant", ["MADEC"], [
            ProductSeed("NET-GEL-001", "Gel nettoyant multi-surfaces 750ml", "Gel nettoyant ménager", "u", 24.90, 0, "NONFOOD"),
            ProductSeed("NET-GEL-002", "Gel nettoyant cuisine 500ml", "Dégraissant cuisine", "u", 21.00, 0, "NONFOOD"),
        ]),
        FamilleSeed("Entretien ménager", ["Exet", "Clorel"], [
            ProductSeed("EXE-NET-001", "Nettoyant vitres 500ml", "Nettoyant vitres", "u", 19.50, 5, "NONFOOD"),
            ProductSeed("CLO-JAV-001", "Eau de javel Clorel concentrée 1L", "Javel concentrée à diluer", "u", 14.00, 0, "NONFOOD"),
            ProductSeed("EXE-DES-001", "Désinfectant multi-usages 1L", "Nettoyant désinfectant", "u", 22.00, 0, "NONFOOD"),
        ]),
        FamilleSeed("Couches", ["Evybaby"], [
            ProductSeed("EVY-COU-001", "Couches Evybaby taille 3 (44u)", "Couches bébé taille 3", "u", 89.00, 0, "NONFOOD"),
            ProductSeed("EVY-COU-002", "Couches Evybaby taille 4 (40u)", "Couches bébé taille 4", "u", 92.00, 0, "NONFOOD"),
        ]),
        FamilleSeed("Soins capillaires", ["MADEC"], [
            ProductSeed("SOI-SHAM-001", "Shampooing cheveux normaux 400ml", "Shampooing usage fréquent", "u", 26.50, 0, "NONFOOD"),
            ProductSeed("SOI-SHAM-002", "Après-shampooing 400ml", "Démêlant cheveux", "u", 28.00, 0, "NONFOOD"),
        ]),
        FamilleSeed("Rasage", ["MADEC"], [
            ProductSeed("RAS-MOU-001", "Mousse à raser 200ml", "Mousse à raser", "u", 21.00, 0, "NONFOOD"),
            ProductSeed("RAS-APR-001", "Après-rasage 100ml", "Lotion après-rasage", "u", 24.00, 0, "NONFOOD"),
        ]),
        FamilleSeed("Hygiène corporelle", ["MADEC"], [
            ProductSeed("HYG-SAV-001", "Savon liquide mains 500ml", "Savon liquide", "u", 18.00, 0, "NONFOOD"),
            ProductSeed("HYG-GEL-001", "Gel douche 500ml", "Gel douche extraits naturels", "u", 20.00, 0, "NONFOOD"),
        ]),
    ]),
]
# fmt: on

# Mobile-app taxonomy (independent from sync gamme/famille/sous-famille)
MOBILE_CATEGORIES: list[tuple[str, list[str]]] = [
    ("Épicerie sucrée", ["Confitures", "Chocolat & boissons", "Confiserie", "Biscuits sucrés"]),
    ("Épicerie salée", ["Conserves", "Condiments", "Bouillons", "Épices", "Aides culinaires", "Biscuits salés"]),
    ("Hygiène & entretien", ["Nettoyage", "Hygiène", "Bébé"]),
]


def mobile_labels_for_famille(gamme: str, famille: str) -> tuple[str, str]:
    """Map sync famille → mobile (catégorie, sous-catégorie) for demo seed."""
    fam = famille.lower()
    if gamme == "Non alimentaire":
        if "couche" in fam:
            return "Hygiène & entretien", "Bébé"
        if "gel nettoyant" in fam or "entretien" in fam:
            return "Hygiène & entretien", "Nettoyage"
        return "Hygiène & entretien", "Hygiène"
    if "confiture" in fam:
        return "Épicerie sucrée", "Confitures"
    if "chocolat" in fam or "boisson" in fam:
        return "Épicerie sucrée", "Chocolat & boissons"
    if "confiserie" in fam or "gourmand" in fam:
        return "Épicerie sucrée", "Confiserie"
    if "biscuits sucr" in fam:
        return "Épicerie sucrée", "Biscuits sucrés"
    if "conserves" in fam or "poisson" in fam:
        return "Épicerie salée", "Conserves"
    if "condiment" in fam or "sauce" in fam:
        return "Épicerie salée", "Condiments"
    if "bouillon" in fam:
        return "Épicerie salée", "Bouillons"
    if "épice" in fam:
        return "Épicerie salée", "Épices"
    if "aide" in fam or "crème" in fam or "colorant" in fam or "vinaigre" in fam:
        return "Épicerie salée", "Aides culinaires"
    if "biscuits sal" in fam:
        return "Épicerie salée", "Biscuits salés"
    return "Épicerie salée", famille
