from odoo import api, fields, models


class ConcorsoEdizione(models.Model):
    _name = 'concorso.edizione'
    _description = 'Edizione del Concorso Letterario'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'anno desc, name'

    name = fields.Char(string='Nome', required=True, tracking=True)
    anno = fields.Integer(string='Anno', required=True)
    data_inizio = fields.Date(string='Data Inizio', required=True, tracking=True)
    data_fine = fields.Date(string='Data Fine', required=True, tracking=True)
    stato = fields.Selection(
        selection=[
            ('bozza', 'Bozza'),
            ('aperto', 'Aperto'),
            ('chiuso', 'Chiuso'),
            ('archiviato', 'Archiviato'),
        ],
        string='Stato',
        default='bozza',
        required=True,
        tracking=True,
    )
    note = fields.Html(string='Note')

    elaborato_ids = fields.One2many(
        'concorso.elaborato',
        'edizione_id',
        string='Elaborati',
    )
    sezione_ids = fields.One2many(
        'concorso.sezione',
        'edizione_id',
        string='Sezioni',
    )

    # --- Campi statistiche (ODOO18-004 / ODOO18-006) ------------------------
    # Sei campi computed con @api.depends corretti e aggregazione via
    # _read_group: nessun loop con search separata per ogni edizione.
    totale_elaborati = fields.Integer(
        string='Totale Elaborati',
        compute='_compute_statistiche',
    )
    totale_partecipanti = fields.Integer(
        string='Totale Partecipanti',
        compute='_compute_statistiche',
    )
    totale_valutati = fields.Integer(
        string='Valutati',
        compute='_compute_statistiche',
    )
    totale_premiati = fields.Integer(
        string='Premiati',
        compute='_compute_statistiche',
    )
    media_punteggi_generale = fields.Float(
        string='Media Punteggi',
        compute='_compute_statistiche',
        digits=(6, 2),
    )
    totale_sezioni = fields.Integer(
        string='Totale Sezioni',
        compute='_compute_statistiche',
    )

    @api.depends(
        'elaborato_ids.stato',
        'elaborato_ids.partecipante_id',
        'elaborato_ids.media_punteggi',
        'sezione_ids',
    )
    def _compute_statistiche(self):
        """Aggrega le statistiche dell'edizione evitando il pattern N+1.

        Fix ODOO18-004 / ODOO18-006: invece di eseguire 2 search + mapped()
        per ogni edizione in loop, vengono eseguite quattro chiamate
        ``_read_group`` aggregate che coprono tutte le edizioni del recordset
        in un unico passaggio.

        Complessità: O(4) query per batch, indipendentemente dal numero di
        edizioni in ``self``.
        """
        if not self.ids:
            for edizione in self:
                edizione._azzera_statistiche()
            return

        # 1. Totale elaborati e media punteggi — una sola query
        base_groups = self.env['concorso.elaborato']._read_group(
            domain=[('edizione_id', 'in', self.ids)],
            groupby=['edizione_id'],
            aggregates=['__count', 'media_punteggi:avg'],
        )
        base_stats: dict[int, tuple[int, float]] = {
            edi.id: (cnt, avg) for edi, cnt, avg in base_groups
        }

        # 2. Elaborati per stato (valutato / premiato) — una sola query
        stato_groups = self.env['concorso.elaborato']._read_group(
            domain=[
                ('edizione_id', 'in', self.ids),
                ('stato', 'in', ['valutato', 'premiato']),
            ],
            groupby=['edizione_id', 'stato'],
            aggregates=['__count'],
        )
        stato_stats: dict[int, dict[str, int]] = {}
        for edi, stato, cnt in stato_groups:
            stato_stats.setdefault(edi.id, {})[stato] = cnt

        # 3. Partecipanti distinti: raggruppiamo per (edizione, partecipante)
        #    e contiamo le coppie univoche per edizione — una sola query
        part_groups = self.env['concorso.elaborato']._read_group(
            domain=[('edizione_id', 'in', self.ids)],
            groupby=['edizione_id', 'partecipante_id'],
            aggregates=['__count'],
        )
        partecipanti: dict[int, int] = {}
        for edi, partner, _cnt in part_groups:
            if partner:
                partecipanti[edi.id] = partecipanti.get(edi.id, 0) + 1

        # 4. Sezioni per edizione — una sola query
        sezione_groups = self.env['concorso.sezione']._read_group(
            domain=[('edizione_id', 'in', self.ids)],
            groupby=['edizione_id'],
            aggregates=['__count'],
        )
        sezione_stats: dict[int, int] = {edi.id: cnt for edi, cnt in sezione_groups}

        for edizione in self:
            eid = edizione.id
            cnt, avg = base_stats.get(eid, (0, None))
            edizione.totale_elaborati = cnt
            edizione.totale_partecipanti = partecipanti.get(eid, 0)
            stati = stato_stats.get(eid, {})
            edizione.totale_valutati = stati.get('valutato', 0)
            edizione.totale_premiati = stati.get('premiato', 0)
            edizione.media_punteggi_generale = avg if avg is not None else 0.0
            edizione.totale_sezioni = sezione_stats.get(eid, 0)

    def _azzera_statistiche(self):
        """Azzera tutti i campi statistici dell'edizione."""
        self.totale_elaborati = 0
        self.totale_partecipanti = 0
        self.totale_valutati = 0
        self.totale_premiati = 0
        self.media_punteggi_generale = 0.0
        self.totale_sezioni = 0

    # --- Cron ---------------------------------------------------------------
    @api.model
    def _cron_chiudi_bandi_scaduti(self):
        """Chiude automaticamente le edizioni con data fine nel passato.

        Metodo referenziato dal cron giornaliero in ``data/ir_cron_data.xml``.
        """
        oggi = fields.Date.today()
        scadute = self.search([
            ('stato', '=', 'aperto'),
            ('data_fine', '<', oggi),
        ])
        if scadute:
            scadute.write({'stato': 'chiuso'})

    # --- Statistiche per sezione/sottosezione (usate nei report QWeb) -------
    def get_statistiche_per_sezione(self):
        """Restituisce le statistiche aggregate per sezione dell'edizione.

        Fix ODOO18-009: sostituisce il loop con search separata per ogni
        sezione con un'unica chiamata ``_read_group`` aggregata.
        """
        self.ensure_one()
        groups = self.env['concorso.elaborato']._read_group(
            domain=[('edizione_id', '=', self.id)],
            groupby=['sezione_id'],
            aggregates=['__count', 'media_punteggi:avg'],
        )
        return [
            {
                'sezione_id': sezione.id,
                'sezione_nome': sezione.name or '',
                'totale_elaborati': cnt,
                'media_punteggi': avg if avg is not None else 0.0,
            }
            for sezione, cnt, avg in groups
        ]

    def get_statistiche_per_sottosezione(self):
        """Restituisce le statistiche aggregate per sottosezione dell'edizione.

        Fix ODOO18-009: sostituisce il loop annidato con search separata per
        ogni sezione/sottosezione con un'unica chiamata ``_read_group``
        aggregata con doppio groupby.
        """
        self.ensure_one()
        groups = self.env['concorso.elaborato']._read_group(
            domain=[('edizione_id', '=', self.id)],
            groupby=['sezione_id', 'sottosezione_id'],
            aggregates=['__count', 'media_punteggi:avg'],
        )
        return [
            {
                'sezione_id': sezione.id,
                'sezione_nome': sezione.name or '',
                'sottosezione_id': sottosezione.id,
                'sottosezione_nome': sottosezione.name or '',
                'totale_elaborati': cnt,
                'media_punteggi': avg if avg is not None else 0.0,
            }
            for sezione, sottosezione, cnt, avg in groups
        ]

    # --- Azioni stato -------------------------------------------------------
    def action_apri(self):
        self.write({'stato': 'aperto'})

    def action_chiudi(self):
        self.write({'stato': 'chiuso'})

    def action_archivia(self):
        self.write({'stato': 'archiviato'})
