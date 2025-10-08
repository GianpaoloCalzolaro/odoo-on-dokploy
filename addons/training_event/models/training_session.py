from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class TrainingSession(models.Model):
    """Individual training session belonging to a module."""

    _name = "training.session"
    _description = "Training Session"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date_start, sequence, name"

    name = fields.Char(string=_("Titolo Sessione"), required=True, tracking=True)
    module_id = fields.Many2one(
        string=_("Modulo"),
        comodel_name="training.module",
        required=True,
        ondelete="cascade",
        tracking=True,
    )
    event_id = fields.Many2one(
        string=_("Evento"),
        comodel_name="training.event",
        related="module_id.event_id",
        store=True,
        readonly=True,
    )
    date_start = fields.Datetime(string=_("Data/Ora Inizio"), required=True, tracking=True)
    date_end = fields.Datetime(string=_("Data/Ora Fine"), required=True, tracking=True)
    duration_hours = fields.Float(
        string=_("Durata (ore)"),
        compute="_compute_duration_hours",
        store=True,
        tracking=True,
    )
    description = fields.Html(string=_("Descrizione"), sanitize=True, sanitize_attributes=False)
    materials = fields.Text(string=_("Materiali"))
    attachment_ids = fields.Many2many(
        string=_("Allegati"),
        comodel_name="ir.attachment",
        relation="training_session_attachment_rel",
        column1="session_id",
        column2="attachment_id",
    )
    trainer_ids = fields.Many2many(
        string=_("Formatori"),
        comodel_name="res.users",
        relation="training_session_trainer_rel",
        column1="session_id",
        column2="user_id",
        tracking=True,
    )
    state = fields.Selection(
        selection=[
            ("idea", _("Ideata")),
            ("designed", _("Progettata")),
            ("closed", _("Chiusa")),
        ],
        string=_("Stato"),
        default="idea",
        required=True,
        tracking=True,
    )
    notes = fields.Text(string=_("Note"))
    sequence = fields.Integer(string=_("Sequenza"), default=10)
    active = fields.Boolean(string=_("Attivo"), default=True)

    @api.depends("date_start", "date_end")
    def _compute_duration_hours(self):
        for record in self:
            if record.date_start and record.date_end and record.date_end > record.date_start:
                delta = record.date_end - record.date_start
                record.duration_hours = round(delta.total_seconds() / 3600.0, 2)
            else:
                record.duration_hours = 0.0

    @api.constrains("date_start", "date_end")
    def _check_dates(self):
        for record in self:
            if record.date_start and record.date_end and record.date_end <= record.date_start:
                raise ValidationError(
                    _("L'orario di fine deve essere successivo all'orario di inizio.")
                )

    @api.constrains("date_start", "date_end", "event_id")
    def _check_overlap(self):
        for record in self:
            if not (record.date_start and record.date_end and record.event_id):
                continue
            domain = [
                ("id", "!=", record.id),
                ("event_id", "=", record.event_id.id),
                ("date_start", "<", record.date_end),
                ("date_end", ">", record.date_start),
            ]
            overlap = self.search(domain, limit=1)
            if overlap:
                raise ValidationError(
                    _(
                        "Sovrapposizione rilevata con la sessione '%(name)s' (%(start)s - %(end)s)."
                    )
                    % {
                        "name": overlap.name,
                        "start": fields.Datetime.to_string(overlap.date_start),
                        "end": fields.Datetime.to_string(overlap.date_end),
                    }
                )
