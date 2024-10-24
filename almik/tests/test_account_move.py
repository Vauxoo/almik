from odoo.tests import tagged

from .common import AlmikTransactionCase


@tagged("post_install", "-at_install")
class TestAccountMove(AlmikTransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.company = cls.env.ref("l10n_mx.demo_company_mx")

    def test_01_shipment_invoice(self):
        """Tests the case into which we send the goods to the customer before
        making the invoice
        """
        self.product.standard_price = 100.0

        order = self.create_so(price=150.0)
        order.action_confirm()

        picking = order.picking_ids
        picking.action_assign()
        picking.move_ids.quantity_done = 1.0
        picking.button_validate()

        invoice = self.create_invoice_from_so(order)
        invoice.action_post()

        self.assertEqual(
            len(invoice.invoice_line_ids.cogs_aml_ids),
            2,
            "There should be two Cogs Entry Lines related",
        )
        # Expected gross_profit_margin = 150 - 100 = 50
        self.assertEqual(
            invoice.invoice_line_ids.gross_profit_margin,
            50,
            "Gross Profit Margin is wrong",
        )
