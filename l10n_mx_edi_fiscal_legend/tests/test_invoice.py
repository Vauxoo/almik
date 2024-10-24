from odoo.fields import Command
from odoo.tests.common import tagged

from odoo.addons.l10n_mx_edi_40.tests.common import TestMxEdiCommon


@tagged("fiscal_legends", "post_install", "-at_install")
class TestInvoice(TestMxEdiCommon):
    def test_01_invoice_partner_fiscal_legends(self):
        legend = self.env["l10n_mx_edi.fiscal.legend"]
        fiscal_legend_1 = legend.create({"name": "Demo legend 1"})
        fiscal_legend_2 = legend.create({"name": "Demo legend 2"})
        fiscal_legend_3 = legend.create({"name": "Demo legend 3"})
        fiscal_legend_4 = legend.create({"name": "Demo legend 4"})

        partner_1 = self.env.ref("base.res_partner_1")
        partner_1.write({"l10n_mx_edi_legend_ids": [Command.set([fiscal_legend_1.id, fiscal_legend_2.id])]})
        partner_2 = self.env.ref("base.res_partner_2")
        partner_2.write({"l10n_mx_edi_legend_ids": [Command.set([fiscal_legend_3.id, fiscal_legend_4.id])]})

        move = self.env["account.move"]

        product = self.env.ref("product.product_product_7")
        values = {
            "partner_id": partner_1.id,
            "move_type": "out_invoice",
            "invoice_line_ids": [
                Command.create(
                    {
                        "product_id": product.id,
                        "account_id": product.product_tmpl_id.get_product_accounts()["expense"].id,
                    }
                )
            ],
        }
        invoice = move.create(values)

        self.assertEqual(invoice.l10n_mx_edi_legend_ids, partner_1.l10n_mx_edi_legend_ids)

        values["partner_id"] = partner_2.id
        invoice = move.create(values)

        self.assertEqual(invoice.l10n_mx_edi_legend_ids, partner_2.l10n_mx_edi_legend_ids)
