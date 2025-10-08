from datetime import date, timedelta

from odoo import fields
from odoo.tests import common


class TestTrainingEvent(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.event_model = self.env["training.event"]
        self.module_model = self.env["training.module"]
        self.session_model = self.env["training.session"]

    def test_event_creation_duration(self):
        today = date.today()
        event = self.event_model.create(
            {
                "name": "Evento Test",
                "event_type": "course",
                "date_start": today,
                "date_end": today + timedelta(days=2),
            }
        )
        self.assertTrue(event.code.startswith("EVT/"))
        self.assertEqual(event.duration_days, 3)
        self.assertEqual(event.state, "draft")

    def test_session_count_computation(self):
        today = fields.Date.today()
        event = self.event_model.create(
            {
                "name": "Evento con sessioni",
                "event_type": "seminar",
                "date_start": today,
                "date_end": today,
            }
        )
        module = self.module_model.create(
            {
                "name": "Modulo",
                "event_id": event.id,
            }
        )
        now = fields.Datetime.now()
        self.session_model.create(
            {
                "name": "Sessione 1",
                "module_id": module.id,
                "date_start": now,
                "date_end": now + timedelta(hours=2),
            }
        )
        self.session_model.create(
            {
                "name": "Sessione 2",
                "module_id": module.id,
                "date_start": now + timedelta(hours=3),
                "date_end": now + timedelta(hours=5),
            }
        )
        self.assertEqual(event.session_count, 2)
