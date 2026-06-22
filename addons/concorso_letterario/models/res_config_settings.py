from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Chiave ir.config_parameter allineata con il controller (ODOO18-002):
    # sia qui che in controllers/main.py si usa 'concorso.file_max_size'.
    concorso_file_max_size = fields.Integer(
        string='Dimensione Massima File (MB)',
        config_parameter='concorso.file_max_size',
        default=5,
        help='Dimensione massima consentita per i file allegati agli elaborati (in MB).',
    )
