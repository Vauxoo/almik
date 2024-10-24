from odoo import fields, models


class MxVehicle(models.Model):
    _inherit = "l10n_mx_edi.vehicle"

    environmental_insurer = fields.Char(
        "Environmental insurance Company",
        help="The name of the insurer that covers the environmental risks of the vehicle",
    )
    environmental_insurance_policy = fields.Char("Environmental insurance Policy Number")
