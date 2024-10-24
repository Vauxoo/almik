from odoo import models


class ProductCustomerInfo(models.Model):
    _inherit = "product.customerinfo"

    def get_customer_info_name(self):
        if self.product_code and self.product_name:
            return "[%s] %s" % (self.product_code, self.product_name)
        return self.product_code or self.product_name
