from odoo.tests import Form, TransactionCase


class AlmikTransactionCase(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env.ref("base.res_partner_2")
        cls.product = cls.env.ref("product.product_product_6")

    def create_so(self, partner=None, **line_kwargs):
        if partner is None:
            partner = self.partner
        order = Form(self.env["sale.order"])
        order.partner_id = partner
        order = order.save()
        self.create_so_line(order, **line_kwargs)
        return order

    def create_so_line(self, order, product=None, quantity=1.0, price=150):
        if product is None:
            product = self.product
        with Form(order) as so, so.order_line.new() as line:
            line.product_id = product
            line.product_uom_qty = quantity
            line.price_unit = price

    def create_invoice_from_so(self, order):
        ctx = {
            "active_id": order.id,
            "active_ids": order.ids,
            "active_model": order._name,
            "open_invoices": True,
        }
        wizard = self.env["sale.advance.payment.inv"].with_context(**ctx).create({})
        wizard_res = wizard.create_invoices()
        invoice_id = wizard_res["res_id"]
        return self.env["account.move"].browse(invoice_id)
