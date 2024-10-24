from odoo import fields, models


class CrmLeadLost(models.TransientModel):
    _inherit = "crm.lead.lost"

    can_delete_initiatives_opportunity = fields.Boolean()

    def default_get(self, name_fields):
        result = super().default_get(name_fields)
        result["can_delete_initiatives_opportunity"] = self.env.user.has_group(
            "almik.group_delete_initiatives_opportunity"
        )
        return result
