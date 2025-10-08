from datetime import date, timedelta

from odoo.tests import common


class TestCloneWizard(common.TransactionCase):
    def setUp(self):
        super().setUp()
        today = date.today()
        self.event = self.env["training.event"].create(
            {
                "name": "Evento Base",
                "event_type": "course",
                "date_start": today,
                "date_end": today + timedelta(days=2),
            }
        )
        self.module = self.env["training.module"].create(
            {
                "name": "Modulo 1",
                "event_id": self.event.id,
            }
        )
        self.session = self.env["training.session"].create(
            {
                "name": "Sessione",
                "module_id": self.module.id,
                "date_start": self.event.date_start,
                "date_end": self.event.date_start + timedelta(hours=2),
            }
        )

    def test_clone_event_success(self):
        wizard = self.env["training.event.clone.wizard"].create(
            {
                "event_id": self.event.id,
                "new_name": "Evento Clonato",
                "new_date_start": self.event.date_start + timedelta(days=30),
                "new_date_end": self.event.date_end + timedelta(days=30),
            }
        )
        action = wizard.action_clone()
        cloned_event = self.event.search([("name", "=", "Evento Clonato")], limit=1)
        self.assertTrue(cloned_event)
        self.assertEqual(len(cloned_event.module_ids), len(self.event.module_ids))
        self.assertEqual(len(cloned_event.module_ids.mapped("session_ids")), len(self.event.module_ids.mapped("session_ids")))
        self.assertEqual(action["res_id"], cloned_event.id)
