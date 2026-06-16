from odoo import fields, models


class ConcorsoSezione(models.Model):
    _name = 'concorso.sezione'
    _description = 'Sezione del Concorso Letterario'
    _order = 'edizione_id, name'

    name = fields.Char(string='Nome', required=True)
    edizione_id = fields.Many2one(
        'concorso.edizione',
        string='Edizione',
        required=True,
        ondelete='cascade',
    )
    sottosezione_ids = fields.One2many(
        'concorso.sottosezione',
        'sezione_id',
        string='Sottosezioni',
    )
    note = fields.Text(string='Note')
