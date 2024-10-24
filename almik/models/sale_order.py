from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    delivery_type = fields.Selection(
        [
            ("sample_remission", "Sample Remission"),
            ("oc_remission_pending", "OC Remission Pending"),
            ("financial_remission", "Financial Remission"),
        ]
    )
    margin = fields.Monetary(groups="almik.group_can_see_sale_margin")
    margin_percent = fields.Float(groups="almik.group_can_see_sale_margin")
    customer_number = fields.Char(store=True, related="partner_id.ref", string="Customer Number")
    observations = fields.Char()
