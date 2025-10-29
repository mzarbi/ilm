import unittest

from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from sqlalchemy import create_engine, event
import server.models as m
from server import create_app
from server.extensions import Base
import server.extensions as ext
from server.database import init_session_factory


class APITestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = ext.ENGINE

        # Make sure models are registered on Base BEFORE create_all
        import server.models  # noqa: F401

        # Create schema on THIS engine
        Base.metadata.drop_all(cls.engine)
        Base.metadata.create_all(cls.engine)
        # Wire the app’s session factory to THIS engine
        ext.ENGINE = cls.engine
        init_session_factory()

    def setUp(self):
        # 👈 pass the SAME engine into create_app
        self.app = create_app(engine=self.engine)
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

        # seed (unchanged)
        def get_or_create(session: Session, Model, **where):
            obj = session.query(Model).filter_by(**where).one_or_none()
            if obj is None:
                obj = Model(**where)
                session.add(obj)
                session.flush()
            return obj

        with Session(self.engine) as s, s.begin():
            get_or_create(s, m.PraActivity, code="buyout", label="Buyout")
            get_or_create(s, m.CounterpartyType, code="bank", label="Bank")
            get_or_create(s, m.Currency, code="EUR", name="Euro")
            get_or_create(s, m.Country, iso2="FR", iso3="FRA", name="France")
            get_or_create(s, m.Sector, code="FIN", label="Financials", description="Financial sector")

            if s.query(m.LegalEntity).filter_by(rmpm_code="SPN001", rmpm_type="INTERNAL").one_or_none() is None:
                s.add(m.LegalEntity(rmpm_code="SPN001", rmpm_type="INTERNAL", name="Sponsor SA"))
            if s.query(m.LegalEntity).filter_by(rmpm_code="CPTY01", rmpm_type="INTERNAL").one_or_none() is None:
                s.add(m.LegalEntity(rmpm_code="CPTY01", rmpm_type="INTERNAL", name="Counterparty Ltd"))
            if s.query(m.Project).filter_by(name="Project Neptune").one_or_none() is None:
                s.add(m.Project(name="Project Neptune", code="NEP", description="Test project"))


    # ---------- Helper methods ----------

    def get_first_id(self, url: str) -> int:
        rv = self.client.get(url)
        self.assertEqual(rv.status_code, 200, rv.get_json())
        items = rv.get_json().get("items") or []
        self.assertTrue(items, f"No items at {url}")
        return items[0]["id"]

    # ---------- Tests ----------

    def test_health(self):
        rv = self.client.get("/health")
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv.get_json()["status"], "ok")

    def test_create_and_get_legal_entity(self):
        # Create
        payload = {"rmpm_code": "EXT001", "rmpm_type": "EXTERNAL", "name": "External Corp"}
        rv = self.client.post("/api/legal-entities", json=payload)
        self.assertEqual(rv.status_code, 201, rv.get_json())
        entity = rv.get_json()
        self.assertGreater(entity["id"], 0)
        self.assertEqual(entity["name"], "External Corp")

        # Get
        rv = self.client.get(f"/api/legal-entities/{entity['id']}")
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv.get_json()["rmpm_code"], "EXT001")

    def test_interlinkage_create_get_update_list(self):
        sponsor_id = self.get_first_id("/api/legal-entities?name=Sponsor%20SA")
        cpty_id = self.get_first_id("/api/legal-entities?name=Counterparty%20Ltd")
        project_id = self.get_first_id("/api/projects?name=Project%20Neptune")
        pra_id = self.get_first_id("/api/pra-activities?code=buyout")
        cpty_type_id = self.get_first_id("/api/counterparty-types?code=bank")
        eur_id = self.get_first_id("/api/currencies?code=EUR")

        payload = {
            "sponsor_id": sponsor_id,
            "counterparty_id": cpty_id,
            "project_id": project_id,
            "pra_activity_id": pra_id,
            "counterparty_type_id": cpty_type_id,
            "deal_date": "2024-12-31",
            "effective_date": "2025-01-01",
            "notional_amount": "1000000.00",
            "currency_id": eur_id,
            "status": "draft",
            "purpose": "Testing deal",
        }
        rv = self.client.post("/api/interlinkages", json=payload)
        self.assertEqual(rv.status_code, 201, rv.get_json())
        inter_id = rv.get_json()["id"]

        # Get
        rv = self.client.get(f"/api/interlinkages/{inter_id}")
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv.get_json()["status"], "draft")

        # Update
        rv = self.client.patch(f"/api/interlinkages/{inter_id}", json={"status": "validated"})
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv.get_json()["status"], "validated")

        # List with filter/sort/pagination
        rv = self.client.get("/api/interlinkages?page=1&page_size=10&status=validated&sort=deal_date:desc")
        self.assertEqual(rv.status_code, 200)
        data = rv.get_json()
        self.assertGreaterEqual(data["total"], 1)
        ids = [it["id"] for it in data["items"]]
        self.assertIn(inter_id, ids)

    def test_soft_delete_and_include_deleted(self):
        # Create entity
        rv = self.client.post("/api/legal-entities", json={"rmpm_code": "TMP01", "rmpm_type": "INTERNAL", "name": "TempCo"})
        self.assertEqual(rv.status_code, 201, rv.get_json())
        le_id = rv.get_json()["id"]

        # Soft delete
        rv = self.client.post(f"/api/legal-entities/{le_id}/delete")
        self.assertEqual(rv.status_code, 204)

        # Hidden by default
        rv = self.client.get(f"/api/legal-entities/{le_id}")
        self.assertEqual(rv.status_code, 404)

        # Visible with include_deleted
        rv = self.client.get(f"/api/legal-entities/{le_id}?include_deleted=true")
        self.assertEqual(rv.status_code, 200)
        self.assertTrue(rv.get_json()["is_deleted"])

    def test_validation_error_on_interdependence(self):
        sponsor_id = self.get_first_id("/api/legal-entities?name=Sponsor%20SA")
        cpty_id = self.get_first_id("/api/legal-entities?name=Counterparty%20Ltd")
        project_id = self.get_first_id("/api/projects?name=Project%20Neptune")

        inter = self.client.post("/api/interlinkages", json={
            "sponsor_id": sponsor_id,
            "counterparty_id": cpty_id,
            "project_id": project_id,
            "status": "draft"
        }).get_json()
        inter_id = inter["id"]

        # Invalid enum for level
        bad = self.client.post("/api/interdependences", json={
            "interlinkage_id": inter_id,
            "interdependence_identifier": "EDGE-1",
            "type": "technical",
            "level": "very_high"  # invalid
        })
        self.assertEqual(bad.status_code, 400)
        body = bad.get_json()
        self.assertEqual(body["error"], "validation_error")
        self.assertIn("level", body["messages"])

    def test_hard_delete_fk_restrict(self):
        sponsor_id = self.get_first_id("/api/legal-entities?name=Sponsor%20SA")
        cpty_id = self.get_first_id("/api/legal-entities?name=Counterparty%20Ltd")
        project_id = self.get_first_id("/api/projects?name=Project%20Neptune")

        inter = self.client.post("/api/interlinkages", json={
            "sponsor_id": sponsor_id,
            "counterparty_id": cpty_id,
            "project_id": project_id,
            "status": "draft"
        }).get_json()

        # Try HARD delete sponsor (FK RESTRICT should block; app likely returns 500 with FK message
        rv = self.client.post(f"/api/legal-entities/{sponsor_id}/delete?soft=0")
        self.assertIn(rv.status_code, (409, 500))
        # Optional assertion on error message
        body = rv.get_json()
        if isinstance(body, dict) and "message" in body:
            msg = (body.get("message") or "").lower()
            self.assertTrue("foreign key" in msg or "constraint" in msg or rv.status_code in (400, 409))


if __name__ == "__main__":
    unittest.main(verbosity=2)
