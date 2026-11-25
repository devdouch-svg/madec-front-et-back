"""
Dashboard aggregation endpoint.

Returns a single payload with all data needed for the mobile home screen
and the admin/gestionnaire overview, minimising round-trips.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.core.dependencies import get_current_user, get_db
from app.core.permissions import require_human_user
from app.models.notification import Notification
from app.models.order import Order
from app.models.product import Product
from app.models.banner import Banner
from app.services import catalog as catalog_svc
from app.services.user import get_plafond_status

router = APIRouter(prefix="/dashboard", tags=["dashboard"], dependencies=[Depends(require_human_user)])


MONTHS_FR_SHORT = [
    "janv.", "févr.", "mars", "avr.", "mai", "juin",
    "juil.", "août", "sept.", "oct.", "nov.", "déc.",
]

PERIOD_VALUES = ("week", "last_week", "month", "last_month", "year", "custom")


def _first_of_month(dt: datetime) -> datetime:
    return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def _parse_day(value: str | None, fallback: datetime) -> datetime:
    """Parse a YYYY-MM-DD (or ISO) string into a UTC midnight datetime."""
    if not value:
        return fallback
    try:
        d = datetime.fromisoformat(value)
    except ValueError:
        return fallback
    return d.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)


def _period_range(
    now: datetime,
    period: str,
    date_from: str | None = None,
    date_to: str | None = None,
) -> tuple[datetime, datetime]:
    """
    Resolve (start_inclusive, end_exclusive) for the selected window.

    Buckets compare with ``start <= created_at < end``.
    """
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = midnight + timedelta(days=1)

    if period == "week":                                   # trailing 7 days incl. today
        return midnight - timedelta(days=6), tomorrow
    if period == "last_week":                              # 7 days before this week
        return midnight - timedelta(days=13), midnight - timedelta(days=6)
    if period == "last_month":                             # full previous calendar month
        first_this = _first_of_month(midnight)
        last_month_end = first_this                        # exclusive
        last_month_start = _first_of_month(first_this - timedelta(days=1))
        return last_month_start, last_month_end
    if period == "year":                                   # 1 Jan → now
        return midnight.replace(month=1, day=1), tomorrow
    if period == "custom":
        start = _parse_day(date_from, _first_of_month(midnight))
        end_day = _parse_day(date_to, midnight)
        end = end_day + timedelta(days=1)                  # make date_to inclusive
        if end <= start:                                   # guard against inverted range
            end = start + timedelta(days=1)
        return start, end
    return _first_of_month(midnight), tomorrow             # month (default)


def _build_series(
    rows: list[tuple[datetime, float]],
    start: datetime,
    end: datetime,
    monthly: bool,
):
    """Bucket (created_at, amount) rows into an ordered {label, count, amount} series."""
    buckets: list[dict] = []
    index: dict[str, int] = {}

    if monthly:
        # one bucket per calendar month in [start, end)
        y, m = start.year, start.month
        while (y, m) < (end.year, end.month) or (y == end.year and m == end.month and start <= end):
            key = f"{y}-{m:02d}"
            if key in index:
                break
            index[key] = len(buckets)
            label = MONTHS_FR_SHORT[m - 1]
            if start.year != (end - timedelta(days=1)).year:
                label = f"{label} {str(y)[2:]}"            # disambiguate multi-year ranges
            buckets.append({"label": label, "count": 0, "amount": 0.0})
            m += 1
            if m > 12:
                m, y = 1, y + 1
            if len(buckets) > 120:                          # safety cap
                break
        for created_at, amount in rows:
            i = index.get(f"{created_at.year}-{created_at.month:02d}")
            if i is not None:
                buckets[i]["count"] += 1
                buckets[i]["amount"] += float(amount or 0)
        return buckets

    # daily buckets over [start, end)
    days = (end.date() - start.date()).days
    for i in range(max(days, 1)):
        d = (start + timedelta(days=i)).date()
        index[d.isoformat()] = i
        buckets.append({"label": f"{d.day:02d}/{d.month:02d}", "count": 0, "amount": 0.0})
    for created_at, amount in rows:
        i = index.get(created_at.date().isoformat())
        if i is not None:
            buckets[i]["count"] += 1
            buckets[i]["amount"] += float(amount or 0)
    return buckets


@router.get("")
def get_dashboard(
    period: str = Query("month", pattern="^(week|last_week|month|last_month|year|custom)$"),
    date_from: str | None = Query(None, description="custom range start (YYYY-MM-DD)"),
    date_to: str | None = Query(None, description="custom range end, inclusive (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Unified home-screen payload.

    - **acheteur**: plafond status, recent orders, active banners, unread count
    - **admin / gestionnaire**: adds platform-wide order & user stats

    ``period`` scopes the admin KPIs, the status breakdown and the activity
    series: ``week`` | ``last_week`` | ``month`` | ``last_month`` | ``year`` |
    ``custom`` (with ``date_from`` / ``date_to``).
    """
    now = datetime.now(timezone.utc)
    if period not in PERIOD_VALUES:
        period = "month"

    # ── banners ───────────────────────────────────────────────────────────────
    banners = (
        db.query(Banner)
        .filter(Banner.is_active == True)
        .order_by(Banner.position)
        .all()
    )

    # ── notifications unread count ────────────────────────────────────────────
    unread_notifs = (
        db.query(func.count(Notification.id))
        .filter(
            Notification.user_id == current_user.id,
            Notification.is_read == False,
        )
        .scalar()
        or 0
    )

    # ── recent orders ─────────────────────────────────────────────────────────
    is_staff = current_user.role in ("admin", "gestionnaire")

    if is_staff:
        recent_orders_q = (
            db.query(Order)
            .options(joinedload(Order.user))
            .order_by(Order.created_at.desc())
            .limit(8)
            .all()
        )
        recent_orders = [
            {
                "id": o.id,
                "sorder_code": o.sorder_code,
                "sorder_status": o.sorder_status,
                "dueamount": float(o.dueamount),
                "created_at": o.created_at.isoformat(),
                "buyer_name": o.user_name or o.user_email,
            }
            for o in recent_orders_q
        ]
    else:
        recent_orders_q = (
            db.query(Order)
            .options(joinedload(Order.lines))
            .filter(Order.user_id == current_user.id)
            .order_by(Order.created_at.desc())
            .limit(5)
            .all()
        )
        product_codes = {
            line.product_code for order in recent_orders_q for line in order.lines
        }
        products_by_code: dict[str, str | None] = {}
        if product_codes:
            products_by_code = dict(
                db.query(Product.product_code, Product.image_path)
                .filter(Product.product_code.in_(product_codes))
                .all()
            )

        recent_orders = []
        for order in recent_orders_q:
            sorted_lines = sorted(
                order.lines,
                key=lambda line: (line.sorder_line_code or 0, line.id),
            )
            recent_orders.append(
                {
                    "id": order.id,
                    "sorder_code": order.sorder_code,
                    "sorder_status": order.sorder_status,
                    "dueamount": float(order.dueamount),
                    "created_at": order.created_at.isoformat(),
                    "line_count": len(sorted_lines),
                    "lines": [
                        {
                            "product_code": line.product_code,
                            "product_name": line.product_name,
                            "image_path": products_by_code.get(line.product_code),
                        }
                        for line in sorted_lines[:2]
                    ],
                }
            )

    # ── plafond status ────────────────────────────────────────────────────────
    plafond = get_plafond_status(db, current_user)

    payload: dict = {
        "user": {
            "id": current_user.id,
            "full_name": current_user.full_name,
            "email": current_user.email,
            "role": current_user.role,
            "payment_mode": current_user.payment_mode,
        },
        "plafond": plafond,
        "recent_orders": recent_orders,
        "banners": [
            {
                "id": b.id,
                "title": b.title,
                "subtitle": b.subtitle,
                "image_path": b.image_path,
                "link_url": b.link_url,
                "position": b.position,
            }
            for b in banners
        ],
        "unread_notifications": unread_notifs,
        "mobile_catalog": catalog_svc.get_categories_tree(db, include_inactive=False),
    }

    # ── admin / gestionnaire extras ───────────────────────────────────────────
    if current_user.role in ("admin", "gestionnaire"):
        period_start, period_end = _period_range(now, period, date_from, date_to)

        # Orders within the selected period (fetched once, reused for KPIs + series)
        period_rows = (
            db.query(Order.created_at, Order.dueamount, Order.sorder_status)
            .filter(Order.created_at >= period_start, Order.created_at < period_end)
            .all()
        )

        count_month = sum(1 for _, _, st in period_rows if st != "cancelled")
        revenue_month = float(
            sum(amt or 0 for _, amt, st in period_rows if st != "cancelled")
        )

        # Activity series: monthly buckets for "year" or long custom spans, else daily
        span_days = (period_end.date() - period_start.date()).days
        use_monthly = period == "year" or span_days > 92
        series = _build_series(
            [(ca, amt) for ca, amt, st in period_rows if st != "cancelled"],
            period_start,
            period_end,
            use_monthly,
        )

        # Orders by status, scoped to the selected period
        orders_by_status: dict[str, int] = {}
        for _, _, st in period_rows:
            orders_by_status[st] = orders_by_status.get(st, 0) + 1

        # Total active products / users
        active_products = db.query(func.count(Product.id)).filter(Product.is_active == True).scalar() or 0
        from app.models.user import User
        total_users = db.query(func.count(User.id)).filter(User.is_active == True).scalar() or 0

        # Pending orders needing attention
        pending_count = db.query(func.count(Order.id)).filter(
            Order.sorder_status == "pending"
        ).scalar() or 0

        from app.services import product as product_svc

        uncategorized_mobile = product_svc.count_missing_mobile_category(db)

        payload["admin_stats"] = {
            "period": period,
            "range_from": period_start.date().isoformat(),
            "range_to": (period_end - timedelta(days=1)).date().isoformat(),
            "orders_this_month": count_month or 0,
            "revenue_this_month": revenue_month,
            "orders_by_status": orders_by_status,
            "series": series,
            "active_products": active_products,
            "active_users": total_users,
            "pending_orders": pending_count,
            "uncategorized_mobile_products": uncategorized_mobile,
        }

    return payload
