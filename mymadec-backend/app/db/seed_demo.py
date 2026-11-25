"""
Demo / fake data seeder for local testing.

Inserts users, products, orders, notifications, and banners directly into the DB.
No emails are sent. Idempotent — skips if demo marker user already exists.

All demo accounts use password: Test1234!
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.banner import Banner
from app.models.notification import Notification
from app.models.order import Order, OrderLine, OrderStatusHistory
from app.models.product import Product
from app.models.user import User

logger = logging.getLogger("mymadec.seed_demo")

DEMO_PASSWORD = "Test1234!"
MARKER_EMAIL = "acheteur1@mymadec.test"


def seed_demo_data(db: Session) -> None:
    if db.query(User).filter(User.email == MARKER_EMAIL).first():
        logger.info("Demo data already present — skipping")
        return

    logger.info("Seeding demo data...")
    pw = hash_password(DEMO_PASSWORD)

    # ── Users ───────────────────────────────────────────────────────────────
    admin = db.query(User).filter(User.email == "admin@mymadec.com").first()
    if admin:
        admin.hashed_password = pw
        admin.first_name = admin.first_name or "Admin"
        admin.last_name = admin.last_name or "Demo"

    users = {
        "gestionnaire": User(
            email="gestionnaire@mymadec.test",
            hashed_password=pw,
            first_name="Marie",
            last_name="Dupont",
            phone="06 12 34 56 78",
            role="gestionnaire",
            payment_mode="carte",
            is_active=True,
        ),
        "acheteur1": User(
            email=MARKER_EMAIL,
            hashed_password=pw,
            first_name="Jean",
            last_name="Martin",
            phone="06 98 76 54 32",
            role="acheteur",
            payment_mode="especes",
            plafond_mensuel=5000.00,
            productsalesgroup_code="GRP01",
            is_active=True,
        ),
        "acheteur2": User(
            email="acheteur2@mymadec.test",
            hashed_password=pw,
            first_name="Sophie",
            last_name="Bernard",
            phone="07 11 22 33 44",
            role="acheteur",
            payment_mode="carte",
            plafond_mensuel=2000.00,
            productsalesgroup_code="GRP02",
            is_active=True,
        ),
        "acheteur3": User(
            email="acheteur3@mymadec.test",
            hashed_password=pw,
            first_name="Pierre",
            last_name="Leroy",
            role="acheteur",
            payment_mode="especes",
            plafond_mensuel=None,
            productsalesgroup_code="GRP01",
            is_active=True,
        ),
        "service": User(
            email="service@mymadec.test",
            hashed_password=pw,
            first_name="ETL",
            last_name="Service",
            role="service",
            payment_mode="carte",
            is_active=True,
        ),
        "inactive": User(
            email="inactif@mymadec.test",
            hashed_password=pw,
            first_name="Compte",
            last_name="Inactif",
            role="acheteur",
            is_active=False,
        ),
    }
    for u in users.values():
        db.add(u)
    db.flush()

    # ── Products ────────────────────────────────────────────────────────────
    # Gammes alignées sur le portefeuille MADEC (food / non-food)
    products_data = [
        ("EBK-CONF-001", "Confiture fraise El Baraka 430g", "Confiture extra fraise", "u", "Alimentaire", "Confiture", "El Baraka", "GRP01", "SOC01", 32.50, 0),
        ("EBK-CONF-002", "Confiture abricot El Baraka 430g", "Confiture extra abricot", "u", "Alimentaire", "Confiture", "El Baraka", "GRP01", "SOC01", 32.50, 5),
        ("DAM-BOU-001", "Bouillon cube poulet Damti x24", "Bouillon cube poulet", "bt", "Alimentaire", "Bouillons", "Damti", "GRP01", "SOC01", 18.90, 0),
        ("DAM-BOU-002", "Bouillon cube légumes Damti bio x12", "Bouillon bio légumes", "bt", "Alimentaire", "Bouillons", "Damti", "GRP01", "SOC01", 14.50, 0),
        ("MAD-EPICE-001", "Cumin moulu 100g", "Épice cumin moulu", "u", "Alimentaire", "Épices", "MADEC", "GRP01", "SOC01", 12.00, 0),
        ("MAD-EPICE-002", "Paprika doux 100g", "Épice paprika doux", "u", "Alimentaire", "Épices", "MADEC", "GRP01", "SOC01", 11.50, 0),
        ("CON-POIS-001", "Thon à l'huile 170g", "Conserve thon à l'huile", "u", "Alimentaire", "Conserves", "Poisson", "GRP01", "SOC02", 16.80, 0),
        ("CHOC-001", "Chocao poudre chocolatée 400g", "Poudre chocolatée enfant", "u", "Alimentaire", "Chocolat", "Chocao", "GRP01", "SOC02", 28.00, 10),
        ("ASS-001", "Sauce tomate Assila 400g", "Sauce tomate cuisinée", "u", "Alimentaire", "Aides culinaires", "Assila", "GRP01", "SOC01", 9.90, 0),
        ("CREM-001", "Crème végétale cuisine 200ml", "Crème végétale légère", "u", "Alimentaire", "Crèmes végétales", "MADEC", "GRP01", "SOC01", 15.50, 0),
        ("BISC-001", "Biscuits fourrés chocolat 300g", "Biscuits chocolat", "u", "Alimentaire", "Biscuits", "MADEC", "GRP01", "SOC02", 22.00, 0),
        ("VIN-001", "Vinaigre blanc 1L", "Vinaigre blanc alimentaire", "u", "Alimentaire", "Vinaigre", "MADEC", "GRP01", "SOC01", 8.50, 0),
        ("COL-001", "Colorant alimentaire rouge 28ml", "Colorant alimentaire", "u", "Alimentaire", "Aides culinaires", "MADEC", "GRP01", "SOC01", 6.90, 0),
        ("NET-GEL-001", "Gel nettoyant multi-surfaces 750ml", "Gel nettoyant ménager", "u", "Non alimentaire", "Gel nettoyant", "MADEC", "GRP02", "SOC01", 24.90, 0),
        ("NET-VIT-001", "Nettoyant vitres 500ml", "Nettoyant vitres", "u", "Non alimentaire", "Entretien ménager", "MADEC", "GRP02", "SOC01", 19.50, 5),
        ("CLO-JAV-001", "Eau de javel Clorel concentrée 1L", "Javel concentrée à diluer", "u", "Non alimentaire", "Entretien ménager", "Clorel", "GRP02", "SOC01", 14.00, 0),
        ("HYG-SAV-001", "Savon liquide mains 500ml", "Savon liquide", "u", "Non alimentaire", "Hygiène", "MADEC", "GRP02", "SOC02", 18.00, 0),
        ("EVY-COU-001", "Couches Evybaby taille 3 (44u)", "Couches bébé taille 3", "u", "Non alimentaire", "Couches", "Evybaby", "GRP02", "SOC02", 89.00, 0),
        ("SOI-SHAM-001", "Shampooing cheveux normaux 400ml", "Shampooing cheveux normaux", "u", "Non alimentaire", "Soins capillaires", "MADEC", "GRP02", "SOC02", 26.50, 0),
        ("RAS-001", "Mousse à raser 200ml", "Mousse à raser", "u", "Non alimentaire", "Rasage", "MADEC", "GRP02", "SOC03", 21.00, 0),
        # Gamme Promptinos — page dédiée frontend
        ("PRM-SNACK-001", "Promptino croquant cacao 200g", "Biscuit croquant enrobé cacao", "u", "Promptinos", "Snacking", "Croquant", "GRP01", "SOC01", 19.90, 10),
        ("PRM-SNACK-002", "Promptino fourré vanille 300g", "Biscuit fourré saveur vanille", "u", "Promptinos", "Snacking", "Fourré", "GRP01", "SOC01", 24.50, 0),
        ("PRM-BOISS-001", "Promptino boisson cacahuète 1L", "Boisson végétale cacahuète", "u", "Promptinos", "Boissons", "Végétales", "GRP01", "SOC02", 17.80, 5),
        ("PRM-EPICE-001", "Promptino mélange tajine 80g", "Mélange d'épices pour tajine", "u", "Promptinos", "Épicerie", "Épices", "GRP01", "SOC01", 13.20, 0),
    ]

    products: dict[str, Product] = {}
    for code, name, desc, unit, gamme, famille, sf, psg, soc, price, disc in products_data:
        p = Product(
            product_code=code,
            name=name,
            description=desc,
            unit=unit,
            gamme=gamme,
            famille=famille,
            sous_famille=sf,
            productsalesgroup_code=psg,
            society_code=soc,
            base_price=price,
            discount_rate=disc,
            is_active=True,
        )
        db.add(p)
        products[code] = p
    db.flush()

    # ── Banners ─────────────────────────────────────────────────────────────
    banner_data = [
        (0, "Gamme El Baraka", "Confitures et conserves de qualité", True),
        (1, "Non alimentaire", "Gels nettoyants et entretien ménager", True),
        (2, "Épices MADEC", "La plus large gamme d'épices", False),
    ]
    existing_banners = db.query(Banner).order_by(Banner.position).all()
    for i, (pos, title, subtitle, active) in enumerate(banner_data):
        if i < len(existing_banners):
            b = existing_banners[i]
            b.title = title
            b.subtitle = subtitle
            b.is_active = active
            b.position = pos
        else:
            db.add(Banner(title=title, subtitle=subtitle, position=pos, is_active=active))

    # ── Orders ────────────────────────────────────────────────────────────────
    now = datetime.now(timezone.utc)
    acheteur1 = users["acheteur1"]
    acheteur2 = users["acheteur2"]
    gestionnaire = users["gestionnaire"]

    orders_spec = [
        # (user, status, payment, lines[(code, qty)], days_ago, flagged, bl?)
        (acheteur1, "pending", "especes", [("EBK-CONF-001", 6), ("DAM-BOU-001", 4)], 1, False, None),
        (acheteur1, "validated", "especes", [("MAD-EPICE-001", 10), ("VIN-001", 5)], 3, False, None),
        (acheteur1, "processing", "especes", [("CHOC-001", 8), ("ASS-001", 12)], 5, False, None),
        (acheteur1, "ready", "carte", [("NET-GEL-001", 6), ("CLO-JAV-001", 4)], 7, False, None),
        (acheteur1, "delivered", "carte", [("EVY-COU-001", 2), ("SOI-SHAM-001", 3)], 14, False, 257.50),
        (acheteur2, "pending", "carte", [("NET-VIT-001", 8), ("HYG-SAV-001", 6)], 0, True, None),
        (acheteur2, "cancelled", "carte", [("RAS-001", 5)], 10, False, None),
        (acheteur2, "delivered", "carte", [("EBK-CONF-002", 4), ("BISC-001", 6)], 20, False, 262.00),
    ]

    seq = db.query(Order).count() + 1
    for user, status, payment, line_items, days_ago, flagged, bl_amount in orders_spec:
        psg = line_items[0][0][:3] if line_items else "GEN"
        code = f"SMD_{seq:06d}_{psg}"
        seq += 1

        total = 0.0
        order_lines = []
        for pcode, qty in line_items:
            prod = products[pcode]
            price = prod.final_price or 0.0
            amount = round(price * qty, 2)
            total += amount
            order_lines.append((prod, pcode, qty, price, amount))

        fixedtax = 0.0
        dueamount = round(total + fixedtax, 2)
        created = now - timedelta(days=days_ago)

        order = Order(
            sorder_code=code,
            user_id=user.id,
            productsalesgroup_code=products[line_items[0][0]].productsalesgroup_code,
            sorder_status=status,
            payment_mode=payment,
            amount=total,
            fixedtax=fixedtax,
            dueamount=dueamount,
            bl_amount=bl_amount,
            is_flagged=flagged,
            created_at=created,
            updated_at=created,
        )
        db.add(order)
        db.flush()

        for prod, pcode, qty, price, amount in order_lines:
            bl_qty = qty if bl_amount and status == "delivered" else None
            db.add(OrderLine(
                order_id=order.id,
                product_id=prod.id,
                product_code=pcode,
                product_name=prod.name,
                unit_price=price,
                quantity=qty,
                bl_quantity=bl_qty,
                line_amount=amount,
            ))

        db.add(OrderStatusHistory(
            order_id=order.id,
            status="pending",
            notes="Commande créée",
            created_at=created,
        ))
        if status != "pending":
            db.add(OrderStatusHistory(
                order_id=order.id,
                status=status,
                changed_by_id=gestionnaire.id,
                notes=f"Statut → {status}",
                created_at=created + timedelta(hours=2),
            ))

    # ── Notifications ─────────────────────────────────────────────────────────
    notifs = [
        (acheteur1.id, "Commande en cours", "Votre commande SMD_000003 est en traitement.", "order_status", False),
        (acheteur1.id, "Plafond mensuel", "Il vous reste 3 200 € sur votre plafond ce mois.", "general", False),
        (acheteur1.id, "Bienvenue !", "Bienvenue sur My Madec. Explorez le catalogue.", "general", True),
        (acheteur2.id, "Commande signalée", "Une commande nécessite votre attention.", "order_status", False),
        (acheteur2.id, "Promo confitures", "Remise sur la gamme El Baraka ce mois-ci.", "promo", True),
        (users["gestionnaire"].id, "Nouvelle commande", "Jean Martin a passé une commande.", "order_status", True),
    ]
    for uid, title, body, ntype, is_read in notifs:
        db.add(Notification(
            user_id=uid,
            title=title,
            body=body,
            type=ntype,
            is_read=is_read,
        ))

    db.commit()

    logger.warning("=" * 60)
    logger.warning("DEMO DATA SEEDED — all accounts use password: %s", DEMO_PASSWORD)
    logger.warning("  admin@mymadec.com          (admin)")
    logger.warning("  gestionnaire@mymadec.test  (gestionnaire)")
    logger.warning("  acheteur1@mymadec.test     (acheteur — plafond 5000€)")
    logger.warning("  acheteur2@mymadec.test     (acheteur — plafond 2000€)")
    logger.warning("  acheteur3@mymadec.test     (acheteur — plafond illimité)")
    logger.warning("  service@mymadec.test       (service)")
    logger.warning("  inactif@mymadec.test       (inactif — compte désactivé)")
    logger.warning("  + %d products, %d orders, notifications, banners", len(products_data), len(orders_spec))
    logger.warning("=" * 60)
