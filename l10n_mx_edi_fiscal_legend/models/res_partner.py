from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    l10n_mx_edi_legend_ids = fields.Many2many(
        "l10n_mx_edi.fiscal.legend",
        string="Fiscal Legends",
        help="Legends under tax provisions, other than those contained in the Mexican CFDI standard. "
        "This field will be used as the default value in new invoices for this partner.",
    )
