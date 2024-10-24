from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    l10n_mx_edi_payment_method_id = fields.Many2one(
        "l10n_mx_edi.payment.method",
        string="Payment Way",
        default=lambda self: self.env.ref("l10n_mx_edi.payment_method_otros", raise_if_not_found=False),
        help="This payment method will be used by default in the related "
        "documents (invoices, payments, and bank statements).",
    )

    l10n_mx_edi_usage = fields.Selection(
        string="Usage",
        selection=lambda self: self._get_usage_selection(),
        help="This usage will be used instead of the default one for invoices.",
    )

    def _get_usage_selection(self):
        return self.env["account.move"].fields_get().get("l10n_mx_edi_usage").get("selection")
