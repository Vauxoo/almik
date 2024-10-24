from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    observations_per_line = fields.Char(related="sale_line_ids.observations_per_line")
    cogs_aml_ids = fields.One2many("account.move.line", "origin_of_cogs_aml_id")
    has_gross_profit_margin = fields.Boolean(
        compute="_compute_gross_profit_margin",
        compute_sudo=True,
        store=True,
        help="Provides a technical/functional field to look at the Gross Profit Margin",
    )
    cogs = fields.Float(
        compute="_compute_gross_profit_margin",
        compute_sudo=True,
        store=True,
        string="Cost of Goods Sold",
        groups="almik.group_can_see_gross_profit_margin",
        help="This is a technical field to store Cost of Goods Sold associated to this line",
    )
    gross_profit_margin = fields.Float(
        compute="_compute_gross_profit_margin",
        compute_sudo=True,
        store=True,
        groups="almik.group_can_see_gross_profit_margin",
        help="Gross Profit Margin = Sales Revenue - Cost of Goods Sold",
    )
    gross_profit_margin_percentage = fields.Float(
        compute="_compute_gross_profit_margin",
        compute_sudo=True,
        store=True,
        groups="almik.group_can_see_gross_profit_margin",
        help="Gross Profit Margin Percentage = 100 * (Sales Revenue - Cost of Goods Sold) / Sales Revenue",
    )

    @api.depends("cogs_aml_ids")
    def _compute_gross_profit_margin(self):
        """Compute Gross Profit Margin based on the Cost of Goods Sold and the Revenue in the lines computed"""
        for line in self:
            cogs = 0
            gross_profit_margin = ""
            gross_profit_margin_percentage = 0
            has_gross_profit_margin = False
            if line.display_type == "product" and line.cogs_aml_ids:
                cogs = sum(line.mapped("cogs_aml_ids.debit"))
                revenue = line.credit
                gross_profit_margin = revenue - cogs
                gross_profit_margin_percentage = 100 * (gross_profit_margin) / revenue if revenue else 0.0
                has_gross_profit_margin = True
            line.update(
                {
                    "cogs": cogs,
                    "gross_profit_margin": gross_profit_margin,
                    "gross_profit_margin_percentage": gross_profit_margin_percentage,
                    "has_gross_profit_margin": has_gross_profit_margin,
                }
            )
