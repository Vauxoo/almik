from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _stock_account_prepare_anglo_saxon_out_lines_vals(self):
        # NOTE: By @hbto: This method is being overriden in order to allow
        # keeping tracking of the journal items created by the COGS lines
        # A PR has been proposed to Odoo at:
        # https://github.com/odoo/odoo/pull/78972
        # After merging of that MR this method can be got ridden.

        lines_vals_list = []
        lines = self.env["account.move.line"].search(
            [
                ("id", "in", self.invoice_line_ids.ids),
                ("company_id.anglo_saxon_accounting", "=", True),
                ("move_id.move_type", "in", self.get_sale_types(include_receipts=True)),
                ("product_id.type", "=", "product"),
                ("product_id.valuation", "=", "real_time"),
            ],
        )
        for line in lines:
            # Retrieve accounts needed to generate the COGS.
            accounts = line.product_id.product_tmpl_id.with_company(line.company_id.id).get_product_accounts(
                fiscal_pos=line.move_id.fiscal_position_id
            )
            debit_interim_account = accounts["stock_output"]
            credit_expense_account = accounts["expense"] or self.journal_id.default_account_id
            if not debit_interim_account or not credit_expense_account:
                continue

            # Compute accounting fields.
            sign = -1 if line.move_id.move_type == "out_refund" else 1
            price_unit = line._stock_account_get_anglo_saxon_price_unit()
            balance = sign * line.quantity * price_unit

            # Add interim account line.
            lines_vals_list.append(
                line._stock_account_prepare_anglo_saxon_interim_line_val(
                    balance,
                    price_unit,
                    debit_interim_account,
                )
            )

            # Add expense account line.
            lines_vals_list.append(
                line._stock_account_prepare_anglo_saxon_expense_line_val(
                    balance,
                    price_unit,
                    credit_expense_account,
                )
            )
        return lines_vals_list
