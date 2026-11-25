"""Figma mobile sous-categories (73) — parent IDs from original 9-category catalog."""
from __future__ import annotations

# (figma_parent_id, name, sort_order) — from import_sous_categories_figma.sql
FIGMA_SOUS_CATEGORIES: list[tuple[int, str, int]] = [
    (2, "Chocolat en poudre", 0),
    (2, "Confiture", 1),
    (2, "Confitures et miels", 2),
    (2, "Petit déjeuner", 3),
    (6, "Fromagerie & Crémerie", 0),
    (7, "Adoucissant", 0),
    (7, "Barres chocolatées", 1),
    (7, "Biscuits", 2),
    (7, "Biscuits Amada", 3),
    (7, "Biscuits Nooco", 4),
    (7, "Biscuits Ozmo", 5),
    (7, "Boulangerie", 6),
    (7, "Couches bébés", 7),
    (7, "Crèmes fraîches", 8),
    (7, "Eau de Javel", 9),
    (7, "Entretien & Nettoyage", 10),
    (7, "Feuilles de pastilla", 11),
    (7, "Fromage portions", 12),
    (7, "Fromagerie", 13),
    (7, "Gel douche", 14),
    (7, "Genoise", 15),
    (7, "Hygiène & Beauté", 16),
    (7, "Lessive liquide", 17),
    (7, "Lessive poudre", 18),
    (7, "Lessives et soins du linge", 19),
    (7, "Lingettes", 20),
    (7, "Miel", 21),
    (7, "Monde du bébé", 22),
    (7, "Nettoyants cuisine", 23),
    (7, "Nettoyants sol", 24),
    (7, "Nettoyants vitres", 25),
    (7, "Pain", 26),
    (7, "Pain tacos", 27),
    (7, "Produits nettoyants", 28),
    (7, "Pâte feuilletée", 29),
    (7, "Pâtes et dérivés", 30),
    (7, "Salle de bain & WC", 31),
    (7, "Savon", 32),
    (7, "Soins du corps", 33),
    (7, "Tablettes de chocolat", 34),
    (9, "Aides à la pâtisserie et préparations", 0),
    (9, "Autres sauces", 1),
    (9, "Bouillons", 2),
    (9, "Colorants", 3),
    (9, "Conserves", 4),
    (9, "Conserves de poisson", 5),
    (9, "Desserts", 6),
    (9, "Epices en flacon", 7),
    (9, "Epices en sachet", 8),
    (9, "Farine de maïs", 9),
    (9, "Flan", 10),
    (9, "Gelées", 11),
    (9, "Glasses", 12),
    (9, "Jus de citron", 13),
    (9, "Ketchup", 14),
    (9, "Levure", 15),
    (9, "Mayonnaise", 16),
    (9, "Mousses", 17),
    (9, "Moutarde", 18),
    (9, "Olives et cornichons", 19),
    (9, "Poudre de cacao", 20),
    (9, "Préparation culinaire", 21),
    (9, "Préparations pâtissières", 22),
    (9, "Préparations sauces", 23),
    (9, "Préparations soupes", 24),
    (9, "Purée et coulis de tomate", 25),
    (9, "Raib", 26),
    (9, "Sauces asiatiques", 27),
    (9, "Sauces piquantes", 28),
    (9, "Sauces pizza", 29),
    (9, "Sauces snacks", 30),
    (9, "Sel", 31),
    (9, "Vinaigre et vinaigrette", 32),
]

FIGMA_PARENT_NAMES = {
    2: "Boissons chaudes",
    6: "Crémerie",
    7: "Epicerie",
    9: "Sauces et condiments",
}


def resolve_ctgs_category_name(sous_name: str, figma_parent_id: int) -> str:
    """Map Figma sous-categorie -> current CTGS category name in DB."""
    n = sous_name.strip()
    lower = n.lower()

    exact = {
        "Boulangerie": "Boulangerie",
        "Entretien & Nettoyage": "Entretien & Nettoyage",
        "Hygiène & Beauté": "Hygiène & Beauté",
        "Monde du bébé": "Monde du Bébé",
        "Fromagerie & Crémerie": "Fromagerie & Crémerie",
        "Fromagerie": "Fromagerie & Crémerie",
        "Petit déjeuner": "Petit déjeuner",
    }
    if n in exact:
        return exact[n]

    if figma_parent_id == 2:
        return "Petit déjeuner"
    if figma_parent_id == 6:
        return "Fromagerie & Crémerie"

    if any(k in lower for k in ("biscuit", "chocolat", "barre", "genoise", "tablette", "nooco", "ozmo", "amada")):
        return "Biscuiterie, Confiserie & Snacks"
    if any(k in lower for k in ("pain", "pâte", "feuille", "pastilla", "tacos")):
        return "Boulangerie"
    if any(k in lower for k in ("lessive", "nettoy", "javel", "wc", "salle de bain")):
        return "Entretien & Nettoyage"
    if any(k in lower for k in ("savon", "gel douche", "hygiène", "soins du corps", "adoucissant", "lingette")):
        return "Hygiène & Beauté"
    if "bébé" in lower or "couche" in lower:
        return "Monde du Bébé"
    if any(k in lower for k in ("fromage", "crème", "raib")):
        return "Fromagerie & Crémerie"
    if "poisson" in lower:
        return "Poissonnerie"
    if figma_parent_id == 9:
        return "Epicerie"
    return "Epicerie"
