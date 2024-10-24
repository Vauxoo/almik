from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    customs_number_month = fields.Char()
    fiscal_legend = fields.Char(
        help="This is the custom fiscal legend. It takes precedence over the ones configured in the invoice, "
        "but just in the invoice report. The CFDI will still use the ones in the invoice.",
    )
