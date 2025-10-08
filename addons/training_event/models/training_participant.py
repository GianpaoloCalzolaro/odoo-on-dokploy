from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class TrainingParticipant(models.Model):
    """Participant for training events (students or trainers)."""

    _name = "training.participant"
    _description = "Training Participant"
    _order = "name"

    partner_id = fields.Many2one(
        string=_("Contatto"),
        comodel_name="res.partner",
        required=True,
        ondelete="restrict",
        tracking=True,
    )
    name = fields.Char(string=_("Nome Completo"), related="partner_id.name", store=True)
    email = fields.Char(string=_("Email"), related="partner_id.email")
    phone = fields.Char(string=_("Telefono"), related="partner_id.phone")
    birthdate = fields.Date(string=_("Data di Nascita"), related="partner_id.birthdate" )
    role = fields.Selection(
        selection=[("student", _("Allievo")), ("trainer", _("Formatore"))],
        string=_("Ruolo"),
        required=True,
        tracking=True,
    )
    user_id = fields.Many2one(
        string=_("Utente"),
        comodel_name="res.users",
        ondelete="restrict",
    )
    notes = fields.Text(string=_("Note"))
    active = fields.Boolean(string=_("Attivo"), default=True)

    _sql_constraints = [
        (
            "training_participant_partner_role_unique",
            "unique(partner_id, role)",
            _("Il contatto è già registrato con lo stesso ruolo."),
        )
    ]

    @api.constrains("role", "user_id")
    def _check_trainer_user(self):
        for record in self:
            if record.role == "trainer" and not record.user_id:
                raise ValidationError(_("I formatori devono avere un utente Odoo associato."))
            if record.role == "student" and record.user_id:
                raise ValidationError(_("Gli allievi non devono avere un utente Odoo associato."))
