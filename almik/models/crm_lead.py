from odoo import _, api, fields, models, tools
from odoo.exceptions import ValidationError


class Lead(models.Model):
    _inherit = "crm.lead"

    can_delete_initiatives_opportunity = fields.Boolean(compute="_compute_user_can_delete_initiatives_opportunity")

    @api.constrains("expected_revenue")
    def _check_expected_revenue(self):
        for record in self:
            if (
                tools.float_is_zero(record.expected_revenue, precision_digits=2)
                and record.type == "opportunity"
                and record.active
            ):
                raise ValidationError(_("Expected revenue should be different from 0.00"))

    @api.constrains("probability")
    def _check_probability(self):
        for record in self:
            if tools.float_is_zero(record.probability, precision_digits=2) and record.active:
                raise ValidationError(_("Probability should be different from 0.00"))

    def _compute_user_can_delete_initiatives_opportunity(self):
        self.can_delete_initiatives_opportunity = self.env.user.has_group("almik.group_delete_initiatives_opportunity")
