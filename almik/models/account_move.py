from odoo import fields, models


class ProductCustomerInfo(models.Model):
    _inherit = "account.move"

    serie = fields.Selection(
        selection=[
            ("fd", "FD"),
            ("fdi", "FDI"),
            ("fp", "FP"),
            ("fpe", "FPE"),
            ("ncd", "NCD"),
            ("cdf", "CDF"),
            ("dev", "DEV"),
            ("ncg", "NCG"),
            ("ant", "ANT"),
            ("ref", "REF"),
            ("md", "MD"),
            ("pte_can_sat", "PTE CAN SAT"),
            ("cancelled", "CANCELLED DOCUMENT"),
        ],
    )
