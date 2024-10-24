from odoo import fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    ship_to = fields.Text(help="Address for shipping")
    task_id = fields.Many2one("project.task")
