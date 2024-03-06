# -*- coding: utf-8 -*-

from odoo import api,models,fields
from odoo.tools.translate import _
from datetime import *
import requests
from xml.etree import ElementTree


class res_currency(models.Model):
    _name = "res.currency"
    _description = "Currency"
    _inherit = 'res.currency'

    def execute_rate_exchange(self):
        self._rate_exchange()
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    @api.model
    def _rate_exchange(self):

        response = requests.get('https://www.banxico.org.mx/rsscb/rss?BMXC_canal=fix&BMXC_idioma=es')
        tree = ElementTree.fromstring(response.content)
        tipo_cambio = float(tree[1][8][2][0].text)
        #fecha = tree[1][3].text
        fecha = fields.datetime.now()
        data = { 'name': fecha,
                'currency_id': 2,
                'rate': 1/tipo_cambio}
        self.env['res.currency.rate'].create(data)
        self.envio_mail(tipo_cambio)

    def envio_mail(self, tipo_cambio):
        template_id = self.env.ref('almik-dev.notificacion_tc').id
        mail = self.env['mail.template'].browse(template_id)
        
        mail.send_mail(self.id,email_values={
            'auto_delete': False,
            'subject':f'Almik | TC dia {tipo_cambio}',
            'reply_to':'',
            'email_to': 'tlr@almik.com.mx, xochitl.martinez@rye.mx, ricardo.avila@rye.mx',
            'email_cc': ''
        }, email_layout_xmlid = 'mail.mail_notification_light')   