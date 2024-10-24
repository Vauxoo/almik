from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    observations_per_line = fields.Char()
    margin = fields.Monetary(groups="almik.group_can_see_sale_margin")
    margin_percent = fields.Float(groups="almik.group_can_see_sale_margin")
