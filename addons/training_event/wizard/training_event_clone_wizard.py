from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class TrainingEventCloneWizard(models.TransientModel):
    """Wizard used to clone a training event with new dates."""

    _name = "training.event.clone.wizard"
    _description = "Training Event Clone Wizard"

    event_id = fields.Many2one(
        string=_("Evento Origine"),
        comodel_name="training.event",
        required=True,
        readonly=True,
    )
    new_name = fields.Char(string=_("Nuovo Titolo"), required=True)
    new_date_start = fields.Date(string=_("Nuova Data Inizio"), required=True)
    new_date_end = fields.Date(string=_("Nuova Data Fine"), required=True)
    new_duration_days = fields.Integer(
        string=_("Nuova Durata"),
        compute="_compute_new_duration_days",
    )

    @api.depends("new_date_start", "new_date_end")
    def _compute_new_duration_days(self):
        for wizard in self:
            if wizard.new_date_start and wizard.new_date_end and wizard.new_date_end >= wizard.new_date_start:
                wizard.new_duration_days = (wizard.new_date_end - wizard.new_date_start).days + 1
            else:
                wizard.new_duration_days = 0

    @api.constrains("new_date_start", "new_date_end")
    def _check_dates(self):
        for wizard in self:
            if wizard.new_date_start and wizard.new_date_end and wizard.new_date_end < wizard.new_date_start:
                raise ValidationError(
                    _("La data di fine deve essere successiva o uguale alla data di inizio.")
                )

    @api.constrains("new_duration_days", "event_id")
    def _check_duration(self):
        for wizard in self:
            if (
                wizard.event_id
                and wizard.new_duration_days
                and wizard.new_duration_days < wizard.event_id.duration_days
            ):
                raise ValidationError(
                    _(
                        "La durata del nuovo evento (%(new)d giorni) deve essere almeno pari a quella dell'evento originale (%(old)d giorni)."
                    )
                    % {
                        "new": wizard.new_duration_days,
                        "old": wizard.event_id.duration_days,
                    }
                )

    def action_clone(self):
        self.ensure_one()
        event = self.event_id
        new_event = event.copy(
            {
                "name": self.new_name,
                "date_start": self.new_date_start,
                "date_end": self.new_date_end,
                "state": "draft",
                "participant_ids": [(5, 0, 0)],
            }
        )
        return {
            "type": "ir.actions.act_window",
            "res_model": "training.event",
            "view_mode": "form",
            "res_id": new_event.id,
            "target": "current",
        }
