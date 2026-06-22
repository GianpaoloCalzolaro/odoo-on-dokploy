import base64
import logging

from odoo import _, http
from odoo.http import request

_logger = logging.getLogger(__name__)

_CONFIG_KEY_FILE_MAX_SIZE = 'concorso.file_max_size'
_DEFAULT_FILE_MAX_SIZE_MB = 5


class ConcorsoController(http.Controller):

    @http.route(
        '/concorso/submit',
        type='http',
        auth='public',
        methods=['POST'],
        csrf=True,
    )
    def submit_elaborato(self, edizione_id=None, titolo=None, nome=None,
                         email=None, elaborato=None, **kwargs):
        """Endpoint pubblico per la sottomissione di elaborati al concorso."""
        # Lettura del limite dimensione file dalla configurazione.
        # La chiave 'concorso.file_max_size' è la stessa scritta da
        # ResConfigSettings (ODOO18-002: chiave allineata).
        max_size_mb = int(
            request.env['ir.config_parameter'].sudo().get_param(
                _CONFIG_KEY_FILE_MAX_SIZE,
                default=str(_DEFAULT_FILE_MAX_SIZE_MB),
            )
        )
        max_size_bytes = max_size_mb * 1024 * 1024

        if elaborato and hasattr(elaborato, 'read'):
            data = elaborato.read()
            if len(data) > max_size_bytes:
                return request.make_response(
                    _('Il file supera la dimensione massima consentita (%d MB).') % max_size_mb,
                    status=413,
                )

        try:
            edizione = request.env['concorso.edizione'].sudo().browse(int(edizione_id))
            if not edizione.exists() or edizione.stato != 'aperto':
                return request.make_response(_('Edizione non disponibile.'), status=400)

            partner = request.env['res.partner'].sudo().search(
                [('email', '=', email)], limit=1
            )
            if not partner:
                partner = request.env['res.partner'].sudo().create({
                    'name': nome or email,
                    'email': email,
                })

            vals = {
                'name': titolo or _('Senza titolo'),
                'partecipante_id': partner.id,
                'edizione_id': edizione.id,
                'stato': 'inviato',
            }

            if elaborato and hasattr(elaborato, 'read'):
                attachment = request.env['ir.attachment'].sudo().create({
                    'name': elaborato.filename,
                    'datas': base64.b64encode(data),
                    'res_model': 'concorso.elaborato',
                })
                vals['attachment_ids'] = [(4, attachment.id)]

            request.env['concorso.elaborato'].sudo().create(vals)

        except Exception:
            _logger.exception('Errore durante la sottomissione dell\'elaborato')
            return request.make_response(_('Errore interno. Riprova più tardi.'), status=500)

        return request.redirect('/concorso/submit/grazie')

    @http.route(
        '/concorso/submit/grazie',
        type='http',
        auth='public',
        methods=['GET'],
        website=False,
    )
    def submit_grazie(self, **kwargs):
        return request.make_response(
            '<html><body><p>Grazie per aver partecipato!</p></body></html>',
            headers=[('Content-Type', 'text/html')],
        )
