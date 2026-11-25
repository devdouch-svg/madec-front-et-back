"""Cash fee rate setting — disabled; prices come from Sabile without surcharge."""
from __future__ import annotations

import pytest

from tests.conftest import auth, make_product


class TestCashFeeRate:
    def test_get_returns_zero(self, client, buyer_token):
        r = client.get("/api/v1/settings/cash-fee-rate", headers=auth(buyer_token))
        assert r.status_code == 200
        assert r.json()["rate"] == pytest.approx(0.0)

    def test_admin_update_is_noop_returns_zero(self, client, admin_token):
        r = client.put(
            "/api/v1/settings/cash-fee-rate",
            json={"rate": 0.25},
            headers=auth(admin_token),
        )
        assert r.status_code == 200
        assert r.json()["rate"] == pytest.approx(0.0)

        r2 = client.get("/api/v1/settings/cash-fee-rate", headers=auth(admin_token))
        assert r2.json()["rate"] == pytest.approx(0.0)

    def test_non_admin_cannot_update(self, client, buyer_token):
        r = client.put(
            "/api/v1/settings/cash-fee-rate",
            json={"rate": 0.30},
            headers=auth(buyer_token),
        )
        assert r.status_code == 403

    def test_rate_out_of_range_rejected(self, client, admin_token):
        assert client.put(
            "/api/v1/settings/cash-fee-rate", json={"rate": 25}, headers=auth(admin_token)
        ).status_code == 422
        assert client.put(
            "/api/v1/settings/cash-fee-rate", json={"rate": -0.1}, headers=auth(admin_token)
        ).status_code == 422

    def test_especes_order_has_no_added_fee(self, client, db, acheteur, buyer_token, admin_token):
        """Order total equals Sabile product price — no fixedtax surcharge."""
        make_product(db, code="PRODFEE", base_price=100.0)
        client.put(
            "/api/v1/settings/cash-fee-rate", json={"rate": 0.20}, headers=auth(admin_token)
        )
        r = client.post(
            "/api/v1/orders",
            json={"lines": [{"product_code": "PRODFEE", "quantity": 1}]},
            headers=auth(buyer_token),
        )
        assert r.status_code in (200, 201)
        order = r.json()[0]
        assert float(order["fixedtax"]) == pytest.approx(0.0, abs=0.01)
        assert float(order["dueamount"]) == pytest.approx(100.0, abs=0.01)
