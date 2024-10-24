from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    origin_of_cogs_aml_id = fields.Many2one(
        "account.move.line",
        index=True,
        copy=False,
        help="Technical field used to keep track in the originating line of the anglo-saxon lines.",
    )

    def _stock_account_prepare_anglo_saxon_interim_line_val(self, balance, price_unit, account):
        # /!\ NOTE: after https://github.com/odoo/odoo/pull/78972 merging this
        # method can be refactored to only update `origin_of_cogs_aml_id` field
        return {
            "name": self.name[:64],
            "move_id": self.move_id.id,
            "product_id": self.product_id.id,
            "product_uom_id": self.product_uom_id.id,
            "quantity": self.quantity,
            "price_unit": price_unit,
            "debit": -min(balance, 0.0),
            "credit": max(balance, 0.0),
            "account_id": account.id,
            "display_type": "cogs",
            "origin_of_cogs_aml_id": self.id,
        }

    def _stock_account_prepare_anglo_saxon_expense_line_val(self, balance, price_unit, account):
        # /!\ NOTE: after https://github.com/odoo/odoo/pull/78972 merging this
        # method can be refactored to only update `origin_of_cogs_aml_id` field
        return {
            "name": self.name[:64],
            "move_id": self.move_id.id,
            "product_id": self.product_id.id,
            "product_uom_id": self.product_uom_id.id,
            "quantity": self.quantity,
            "price_unit": -price_unit,
            "debit": max(balance, 0.0),
            "credit": -min(balance, 0.0),
            "account_id": account.id,
            "analytic_distribution": self.analytic_distribution,
            "display_type": "cogs",
            "origin_of_cogs_aml_id": self.id,
        }
