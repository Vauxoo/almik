from odoo import fields, models


class UomUom(models.Model):
    _inherit = "uom.uom"

    factor_conversion = fields.Char(help="Information about equivalencies.")
    product_ids = fields.Many2many(
        "product.product",
        "product_uom_rel",
        "uom_id",
        "product_id",
        string="Products",
        help="Products which use this conversion.",
    )
    relation = fields.Selection(
        selection=[
            ("no", "No Conversion"),
            ("box_pcs", "Box / Pieces"),
            ("kg_ea", "kg / EA"),
            ("kg_mt", "kg / Meter"),
            ("kg_pcs", "kg / Pieces"),
            ("kg_pack", "kg / Pack"),
            ("kg_roll", "kg / Roll"),
            ("kg_lbs", "kg / lbs"),
            ("mt_ft", "Meter / Feet"),
            ("lbs_box", "lbs / Box"),
            ("ft_kg", "Feet / kg"),
            ("ft_pcs", "Feet / Pieces"),
            ("ft_ton", "Feet / Ton"),
            ("pcs_ea", "Pieces / EA"),
            ("pcs_box", "Pieces / Box"),
            ("pcs_kg", "Pieces / kg"),
            ("pcs_mt", "Pieces / Meter"),
            ("pcs_ft", "Pieces / Feet"),
            ("pcs_ton", "Pieces / Ton"),
            ("pcs_roll", "Pieces / Roll"),
            ("pcs_lbs", "Pieces / lbs"),
            ("roll_ft", "Roll / Feet"),
            ("roll_pcs", "Roll / Pieces"),
        ],
        help="The two units of measure which are used for conversion.",
    )
