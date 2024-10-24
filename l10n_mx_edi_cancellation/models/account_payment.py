from odoo import _, models
from odoo.exceptions import UserError


class AccountPayment(models.Model):
    _inherit = "account.payment"

    def action_draft(self):
        if not self._context.get("force_draft") and self.filtered(
            lambda payment: payment.edi_state in ["sent", "to_cancel"] and payment.country_code == "MX"
        ):
            raise UserError(
                _(
                    "You cannot reset to draft a payment that has already been sent or is in the process of being "
                    "canceled. If you want to cancel the payment, you need to request the cancellation of the "
                    "related journal entry.",
                )
            )
        return super().action_draft()
