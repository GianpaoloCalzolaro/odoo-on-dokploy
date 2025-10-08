from datetime import timedelta

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests import common


class TestTrainingSession(common.TransactionCase):
    def setUp(self):
        super().setUp()
        today = fields.Date.today()
        self.event = self.env["training.event"].create(
            {
                "name": "Evento",
                "event_type": "course",
                "date_start": today,
                "date_end": today,
            }
        )
        self.module = self.env["training.module"].create(
            {
                "name": "Modulo",
                "event_id": self.event.id,
            }
        )

    def test_duration_computation(self):
        now = fields.Datetime.now()
        session = self.env["training.session"].create(
            {
                "name": "Sessione",
                "module_id": self.module.id,
                "date_start": now,
                "date_end": now + timedelta(hours=1, minutes=30),
            }
        )
        self.assertEqual(session.duration_hours, 1.5)

    def test_overlap_validation(self):
        start = fields.Datetime.now()
        self.env["training.session"].create(
            {
                "name": "Sessione 1",
                "module_id": self.module.id,
                "date_start": start,
                "date_end": start + timedelta(hours=2),
            }
        )
        with self.assertRaises(ValidationError):
            self.env["training.session"].create(
                {
                    "name": "Sessione 2",
                    "module_id": self.module.id,
                    "date_start": start + timedelta(minutes=30),
                    "date_end": start + timedelta(hours=3),
                }
            )
