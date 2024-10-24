from odoo import fields, models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    observations_per_line = fields.Char(related="move_id.observations_per_line")
