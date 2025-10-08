from datetime import timedelta

from odoo import fields
from odoo.tests import common


class TestTrainingSecurity(common.TransactionCase):
    def setUp(self):
        super().setUp()
        today = fields.Date.today()
        self.event_model = self.env["training.event"].with_context(mail_create_nolog=True)
        self.module_model = self.env["training.module"]
        self.session_model = self.env["training.session"]
        self.event = self.event_model.create(
            {
                "name": "Evento Visibile",
                "event_type": "course",
                "date_start": today,
                "date_end": today,
            }
        )
        module = self.module_model.create(
            {
                "name": "Modulo",
                "event_id": self.event.id,
            }
        )
        self.session = self.session_model.create(
            {
                "name": "Sessione",
                "module_id": module.id,
                "date_start": fields.Datetime.now(),
                "date_end": fields.Datetime.now() + timedelta(hours=2),
            }
        )
        trainer_group = self.env.ref("training_event.group_training_trainer")
        self.trainer_user = self.env["res.users"].create(
            {
                "name": "Trainer Test",
                "login": "trainer_test",
                "email": "trainer@test.com",
                "groups_id": [
                    (
                        6,
                        0,
                        [
                            self.env.ref("base.group_user").id,
                            trainer_group.id,
                        ],
                    )
                ],
            }
        )
        self.session.trainer_ids = [(4, self.trainer_user.id)]

    def test_trainer_sees_only_assigned_sessions(self):
        SessionSudo = self.session_model.with_user(self.trainer_user)
        sessions = SessionSudo.search([])
        self.assertEqual(sessions, self.session)

    def test_trainer_can_update_assigned_session(self):
        SessionSudo = self.session_model.with_user(self.trainer_user)
        self.session.with_user(self.trainer_user).write({"state": "designed"})
        self.assertEqual(SessionSudo.browse(self.session.id).state, "designed")

    def test_trainer_event_visibility(self):
        EventSudo = self.event_model.with_user(self.trainer_user)
        events = EventSudo.search([])
        self.assertEqual(events, self.event)
