from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    """Pre-migration hook placeholder for future changes."""
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    env.cr.execute("SELECT 1")
