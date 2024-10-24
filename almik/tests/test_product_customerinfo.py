from .common import AlmikTransactionCase


class TestProductCustomerinfo(AlmikTransactionCase):
    def test_01_get_customer_info_name(self):
        self.env["product.customerinfo"].create(
            {
                "partner_id": self.partner.id,
                "product_tmpl_id": self.product.product_tmpl_id.id,
                "product_code": "CC",
                "product_name": "Customer Name",
                "price": 100,
            }
        )
        sale_order = self.create_so()
        sale_order.action_confirm()
        self.assertEqual(sale_order.state, "sale")
        picking = sale_order.picking_ids[:1]
        product = picking.move_ids[:1].product_id
        customerinfo = product.customer_ids[:1]
        name = customerinfo.get_customer_info_name()
        self.assertEqual("[CC] Customer Name", name)
