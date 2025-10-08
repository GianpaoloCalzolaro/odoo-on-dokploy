from base64 import b64encode
from io import BytesIO

import xlsxwriter

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class TrainingEvent(models.Model):
    """Main model representing a multi-day training event."""

    _name = "training.event"
    _description = "Training Event"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date_start desc, name"

    name = fields.Char(string=_("Titolo"), required=True, tracking=True)
    code = fields.Char(
        string=_("Codice"),
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: self.env["ir.sequence"].next_by_code("training.event"),
        tracking=True,
    )
    event_type = fields.Selection(
        selection=[
            ("course", _("Corso")),
            ("workshop", _("Workshop")),
            ("seminar", _("Seminario")),
            ("conference", _("Conferenza")),
        ],
        string=_("Tipologia"),
        required=True,
        tracking=True,
    )
    date_start = fields.Date(string=_("Data Inizio"), required=True, tracking=True)
    date_end = fields.Date(string=_("Data Fine"), required=True, tracking=True)
    duration_days = fields.Integer(
        string=_("Durata (giorni)"),
        compute="_compute_duration_days",
        store=True,
        tracking=True,
    )
    state = fields.Selection(
        selection=[
            ("draft", _("Bozza")),
            ("programmed", _("Programmato")),
            ("designed", _("Progettato")),
            ("in_progress", _("In Corso")),
            ("in_review", _("In Verifica")),
            ("closed", _("Chiuso")),
        ],
        string=_("Stato"),
        required=True,
        default="draft",
        tracking=True,
    )
    notes = fields.Text(string=_("Note"))
    module_ids = fields.One2many(
        string=_("Moduli"),
        comodel_name="training.module",
        inverse_name="event_id",
    )
    participant_ids = fields.Many2many(
        string=_("Partecipanti"),
        comodel_name="training.participant",
        relation="training_event_participant_rel",
        column1="event_id",
        column2="participant_id",
    )
    session_count = fields.Integer(
        string=_("N. Sessioni"),
        compute="_compute_session_count",
        tracking=True,
    )
    active = fields.Boolean(string=_("Attivo"), default=True)

    _sql_constraints = [
        ("training_event_code_unique", "unique(code)", _("Il codice evento deve essere univoco.")),
    ]

    @api.depends("date_start", "date_end")
    def _compute_duration_days(self):
        for record in self:
            if record.date_start and record.date_end and record.date_end >= record.date_start:
                record.duration_days = (record.date_end - record.date_start).days + 1
            else:
                record.duration_days = 0

    @api.depends("module_ids.session_ids")
    def _compute_session_count(self):
        for record in self:
            record.session_count = len(record.mapped("module_ids.session_ids"))

    @api.constrains("date_start", "date_end")
    def _check_dates(self):
        for record in self:
            if record.date_start and record.date_end and record.date_end < record.date_start:
                raise ValidationError(
                    _("La data di fine deve essere successiva o uguale alla data di inizio.")
                )

    def action_clone_event(self):
        """Open the clone wizard prefilled with current event."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Clona Evento"),
            "res_model": "training.event.clone.wizard",
            "view_mode": "form",
            "view_id": self.env.ref("training_event.training_event_clone_wizard_form_view").id,
            "target": "new",
            "context": {
                "default_event_id": self.id,
                "default_new_name": _("%s (Copia)") % self.name,
                "default_new_date_start": self.date_start,
                "default_new_date_end": self.date_end,
            },
        }

    def action_export_excel(self):
        """Export the event program to an Excel workbook."""
        self.ensure_one()
        output = BytesIO()
        workbook = self._create_excel_workbook(output)
        workbook.close()
        output.seek(0)
        filename = "evento_%s_attivita_%s.xlsx" % (
            self.code or "senza_codice",
            fields.Datetime.now().strftime("%Y%m%d_%H%M%S"),
        )
        data = b64encode(output.read()).decode()
        return {
            "type": "ir.actions.act_url",
            "url": "data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,%s"
            % data,
            "target": "new",
            "no_session_store": True,
            "close_on_report_download": True,
            "name": filename,
        }

    def _create_excel_workbook(self, output):
        workbook = xlsxwriter.Workbook(output, {"in_memory": True})
        header_format = workbook.add_format(
            {
                "bold": True,
                "bg_color": "#4F81BD",
                "font_color": "#FFFFFF",
                "border": 1,
            }
        )
        wrap_format = workbook.add_format({"text_wrap": True})
        date_format = workbook.add_format({"num_format": "dd/mm/yyyy"})
        datetime_format = workbook.add_format({"num_format": "dd/mm/yyyy hh:mm"})

        self._fill_excel_info_sheet(workbook, header_format, wrap_format, date_format)
        self._fill_excel_modules_sheet(workbook, header_format, wrap_format)
        self._fill_excel_sessions_sheet(workbook, header_format, wrap_format, datetime_format)
        self._fill_excel_participants_sheet(workbook, header_format, wrap_format)
        return workbook

    def _fill_excel_info_sheet(self, workbook, header_format, wrap_format, date_format):
        sheet = workbook.add_worksheet(_("Informazioni Evento"))
        sheet.write(0, 0, _("Codice"), header_format)
        sheet.write(0, 1, self.code or "")
        sheet.write(1, 0, _("Titolo"), header_format)
        sheet.write(1, 1, self.name or "")
        sheet.write(2, 0, _("Tipologia"), header_format)
        sheet.write(2, 1, dict(self._fields["event_type"].selection).get(self.event_type, ""))
        sheet.write(3, 0, _("Data Inizio"), header_format)
        if self.date_start:
            sheet.write_datetime(
                3,
                1,
                fields.Datetime.to_datetime(fields.Date.to_string(self.date_start)),
                date_format,
            )
        sheet.write(4, 0, _("Data Fine"), header_format)
        if self.date_end:
            sheet.write_datetime(
                4,
                1,
                fields.Datetime.to_datetime(fields.Date.to_string(self.date_end)),
                date_format,
            )
        sheet.write(5, 0, _("Durata (giorni)"), header_format)
        sheet.write(5, 1, self.duration_days)
        sheet.write(6, 0, _("Stato"), header_format)
        sheet.write(6, 1, dict(self._fields["state"].selection).get(self.state, ""))
        sheet.write(7, 0, _("N. Moduli"), header_format)
        sheet.write(7, 1, len(self.module_ids))
        sheet.write(8, 0, _("N. Sessioni"), header_format)
        sheet.write(8, 1, self.session_count)
        sheet.write(9, 0, _("N. Partecipanti"), header_format)
        sheet.write(9, 1, len(self.participant_ids))
        sheet.set_column("A:A", 20)
        sheet.set_column("B:B", 50, wrap_format)

    def _fill_excel_modules_sheet(self, workbook, header_format, wrap_format):
        sheet = workbook.add_worksheet(_("Moduli"))
        headers = [_("Codice Evento"), _("Sequenza"), _("Titolo Modulo"), _("Descrizione"), _("N. Sessioni")]
        for idx, header in enumerate(headers):
            sheet.write(0, idx, header, header_format)
        row = 1
        for module in self.module_ids.sorted(key=lambda m: (m.sequence, m.name or "")):
            sheet.write(row, 0, self.code or "")
            sheet.write(row, 1, module.sequence)
            sheet.write(row, 2, module.name or "")
            sheet.write(row, 3, module.description or "", wrap_format)
            sheet.write(row, 4, module.session_count)
            row += 1
        sheet.set_column("A:A", 18)
        sheet.set_column("B:B", 12)
        sheet.set_column("C:C", 40)
        sheet.set_column("D:D", 50, wrap_format)
        sheet.set_column("E:E", 15)

    def _fill_excel_sessions_sheet(self, workbook, header_format, wrap_format, datetime_format):
        sheet = workbook.add_worksheet(_("Sessioni"))
        headers = [
            _("Codice Evento"),
            _("Modulo"),
            _("Titolo Sessione"),
            _("Data/Ora Inizio"),
            _("Data/Ora Fine"),
            _("Durata (ore)"),
            _("Formatori"),
            _("Stato"),
            _("Materiali"),
            _("Note"),
        ]
        for idx, header in enumerate(headers):
            sheet.write(0, idx, header, header_format)
        row = 1
        for session in self.module_ids.mapped("session_ids").sorted(key=lambda s: (s.date_start, s.sequence)):
            sheet.write(row, 0, self.code or "")
            sheet.write(row, 1, session.module_id.name or "")
            sheet.write(row, 2, session.name or "")
            if session.date_start:
                sheet.write_datetime(
                    row,
                    3,
                    fields.Datetime.to_datetime(fields.Datetime.to_string(session.date_start)),
                    datetime_format,
                )
            if session.date_end:
                sheet.write_datetime(
                    row,
                    4,
                    fields.Datetime.to_datetime(fields.Datetime.to_string(session.date_end)),
                    datetime_format,
                )
            sheet.write(row, 5, session.duration_hours)
            sheet.write(row, 6, ", ".join(session.trainer_ids.mapped("name")) or "", wrap_format)
            sheet.write(row, 7, dict(session._fields["state"].selection).get(session.state, ""))
            sheet.write(row, 8, session.materials or "", wrap_format)
            sheet.write(row, 9, session.notes or "", wrap_format)
            row += 1
        sheet.set_column("A:A", 18)
        sheet.set_column("B:B", 30)
        sheet.set_column("C:C", 40)
        sheet.set_column("D:E", 22)
        sheet.set_column("F:F", 15)
        sheet.set_column("G:G", 40, wrap_format)
        sheet.set_column("H:H", 15)
        sheet.set_column("I:J", 40, wrap_format)

    def _fill_excel_participants_sheet(self, workbook, header_format, wrap_format):
        sheet = workbook.add_worksheet(_("Partecipanti"))
        headers = [_("Codice Evento"), _("Nome"), _("Email"), _("Telefono"), _("Ruolo")]
        for idx, header in enumerate(headers):
            sheet.write(0, idx, header, header_format)
        row = 1
        for participant in self.participant_ids.sorted(key=lambda p: p.name or ""):
            sheet.write(row, 0, self.code or "")
            sheet.write(row, 1, participant.name or "")
            sheet.write(row, 2, participant.email or "")
            sheet.write(row, 3, participant.phone or "")
            sheet.write(row, 4, dict(participant._fields["role"].selection).get(participant.role, ""))
            row += 1
        sheet.set_column("A:A", 18)
        sheet.set_column("B:B", 35)
        sheet.set_column("C:C", 40)
        sheet.set_column("D:D", 20)
        sheet.set_column("E:E", 15)

    def _get_calendar_state_colors(self):
        """Return mapping state->color used in calendar views."""
        return {
            "draft": "gray",
            "programmed": "blue",
            "designed": "light-green",
            "in_progress": "green",
            "in_review": "orange",
            "closed": "dark-gray",
        }

    def _get_sessions_grouped_by_day(self):
        """Return sessions grouped by date for reporting purposes."""
        self.ensure_one()
        Session = self.env["training.session"]
        grouped = []
        current_day = None
        current_sessions = Session
        for session in self.module_ids.mapped("session_ids").sorted(
            key=lambda s: (s.date_start, s.sequence)
        ):
            if not session.date_start:
                continue
            day = session.date_start.date()
            if day != current_day:
                if current_sessions:
                    grouped.append(
                        {
                            "day": current_day,
                            "sessions": current_sessions,
                            "duration": sum(current_sessions.mapped("duration_hours")),
                        }
                    )
                current_day = day
                current_sessions = Session
            current_sessions |= session
        if current_sessions:
            grouped.append(
                {
                    "day": current_day,
                    "sessions": current_sessions,
                    "duration": sum(current_sessions.mapped("duration_hours")),
                }
            )
        return grouped
