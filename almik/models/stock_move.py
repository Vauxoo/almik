from odoo import fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    observations_per_line = fields.Char(related="sale_line_id.observations_per_line")
