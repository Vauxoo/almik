from odoo.tests import Form, TransactionCase, tagged


@tagged("post_install", "-at_install", "account_move_line")
class TestAccountMoveLine(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.customer = cls.env.ref("base.res_partner_3")
        cls.product = cls.env.ref("product.product_product_5")

    def create_invoice(self, partner=None, **line_kwargs):
        if partner is None:
            partner = self.customer
        invoice = Form(self.env["account.move"].with_context(default_move_type="out_invoice"))
        invoice.partner_id = partner
        invoice = invoice.save()
        self.create_invoice_line(invoice, **line_kwargs)
        return invoice

    def create_invoice_line(self, invoice, product=None, quantity=1, price=100):
        if product is None:
            product = self.product
        with Form(invoice) as invoice_form, invoice_form.invoice_line_ids.new() as line:
            line.product_id = product
            line.quantity = quantity
            line.price_unit = price

    def test_01_cogs_aml_ids(self):
        # For this purpose, let's modify information from the product and its category
        with Form(self.product.categ_id) as categ:
            categ.property_valuation = "real_time"
        invoice = self.create_invoice()
        invoice.action_post()
        self.assertEqual(
            len(invoice.line_ids.filtered("origin_of_cogs_aml_id")),
            2,
            "There should be two Cogs Entry Lines related",
        )
