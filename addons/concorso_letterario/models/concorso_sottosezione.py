from odoo import fields, models


class ConcorsoSottosezione(models.Model):
    _name = 'concorso.sottosezione'
    _description = 'Sottosezione del Concorso Letterario'
    _order = 'sezione_id, eta_min, name'

    name = fields.Char(string='Nome', required=True)
    sezione_id = fields.Many2one(
        'concorso.sezione',
        string='Sezione',
        required=True,
        ondelete='cascade',
    )
    edizione_id = fields.Many2one(
        related='sezione_id.edizione_id',
        string='Edizione',
        store=True,
        readonly=True,
    )
    eta_min = fields.Integer(string='Età Minima', default=0)
    eta_max = fields.Integer(string='Età Massima', default=0)
    note = fields.Text(string='Note')
