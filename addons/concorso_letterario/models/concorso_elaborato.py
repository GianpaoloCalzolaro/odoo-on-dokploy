from odoo import api, fields, models

_STATI_ELABORATO = [
    ('bozza', 'Bozza'),
    ('inviato', 'Inviato'),
    ('in_valutazione', 'In Valutazione'),
    ('valutato', 'Valutato'),
    ('premiato', 'Premiato'),
]


class ConcorsoElaborato(models.Model):
    _name = 'concorso.elaborato'
    _description = 'Elaborato del Concorso Letterario'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'edizione_id desc, sottosezione_id, media_punteggi desc'

    name = fields.Char(string='Titolo', required=True, tracking=True)
    partecipante_id = fields.Many2one(
        'res.partner',
        string='Partecipante',
        required=True,
        tracking=True,
    )
    edizione_id = fields.Many2one(
        'concorso.edizione',
        string='Edizione',
        required=True,
        ondelete='cascade',
        tracking=True,
    )
    sezione_id = fields.Many2one(
        'concorso.sezione',
        string='Sezione',
        domain="[('edizione_id', '=', edizione_id)]",
        tracking=True,
    )
    sottosezione_id = fields.Many2one(
        'concorso.sottosezione',
        string='Sottosezione',
        domain="[('sezione_id', '=', sezione_id)]",
        tracking=True,
    )
    stato = fields.Selection(
        selection=_STATI_ELABORATO,
        string='Stato',
        default='bozza',
        required=True,
        tracking=True,
    )
    media_punteggi = fields.Float(
        string='Media Punteggi',
        digits=(6, 2),
        default=0.0,
        tracking=True,
    )
    note = fields.Html(string='Note Commissione')
    attachment_ids = fields.Many2many(
        'ir.attachment',
        string='File Allegati',
    )

    # --- Campo classifica (ODOO18-005 / ODOO18-017) -------------------------
    # Non memorizzato: calcolato al volo con approccio batch per evitare N+1.
    # _compute_posizione_ranking esegue UNA sola search per tutte le
    # sottosezioni presenti nel recordset, anziché una search per record.
    posizione_ranking = fields.Integer(
        string='Posizione in Classifica',
        compute='_compute_posizione_ranking',
        store=False,
        help='Posizione nella classifica della sottosezione (solo per elaborati valutati).',
    )

    @api.depends('media_punteggi', 'sottosezione_id', 'stato')
    def _compute_posizione_ranking(self):
        """Calcola la posizione in classifica nella sottosezione in modalità batch.

        Fix ODOO18-005 / ODOO18-017: invece di eseguire una ``search`` per ogni
        record (pattern N+1), viene eseguita un'unica query per tutte le
        sottosezioni presenti nel recordset corrente.

        Complessità: O(1) query per batch, indipendentemente dal numero di
        record in ``self``.
        """
        sottosezioni = self.filtered('sottosezione_id').mapped('sottosezione_id')
        if not sottosezioni:
            self.posizione_ranking = 0
            return

        # Unica query per tutti gli elaborati delle sottosezioni nel batch
        tutti = self.env['concorso.elaborato'].search(
            [
                ('sottosezione_id', 'in', sottosezioni.ids),
                ('stato', '=', 'valutato'),
            ],
            order='media_punteggi desc, id asc',
        )

        # Costruzione della classifica: {sottosezione_id: {elaborato_id: posizione}}
        ranking: dict[int, dict[int, int]] = {}
        pos_counter: dict[int, int] = {}
        for elab in tutti:
            sid = elab.sottosezione_id.id
            pos_counter[sid] = pos_counter.get(sid, 0) + 1
            ranking.setdefault(sid, {})[elab.id] = pos_counter[sid]

        for record in self:
            sid = record.sottosezione_id.id if record.sottosezione_id else 0
            record.posizione_ranking = ranking.get(sid, {}).get(record.id, 0)
