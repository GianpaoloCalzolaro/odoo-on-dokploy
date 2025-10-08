from odoo import api, fields, models, _


class TrainingModule(models.Model):
    """Model describing a training module within an event."""

    _name = "training.module"
    _description = "Training Module"
    _order = "event_id, sequence, name"

    name = fields.Char(string=_("Titolo Modulo"), required=True, tracking=True)
    description = fields.Text(string=_("Descrizione"))
    notes = fields.Text(string=_("Note"))
    event_id = fields.Many2one(
        string=_("Evento"),
        comodel_name="training.event",
        required=True,
        ondelete="cascade",
        tracking=True,
    )
    session_ids = fields.One2many(
        string=_("Sessioni"),
        comodel_name="training.session",
        inverse_name="module_id",
    )
    sequence = fields.Integer(string=_("Sequenza"), default=10)
    session_count = fields.Integer(
        string=_("N. Sessioni"),
        compute="_compute_session_count",
        tracking=True,
    )
    active = fields.Boolean(string=_("Attivo"), default=True)

    @api.depends("session_ids")
    def _compute_session_count(self):
        for record in self:
            record.session_count = len(record.session_ids)
