from odoo import _, api, fields, models
from odoo.osv import expression


class ProductTemplate(models.Model):
    _inherit = "product.template"

    l10n_mx_edi_dangerous_sat_id = fields.Many2one(
        "l10n_mx_edi.product.dangerous.sat.code",
        "Dangerous SAT Code",
        help="This value will be used in the CFDI for carta porte to express the danger type if "
        "the product is dangerous.",
    )
    l10n_mx_edi_packaging_sat_id = fields.Many2one(
        "l10n_mx_edi.product.packaging.sat.code",
        "Packaging SAT Code",
        help="This value will be used in the CFDI for carta porte to express the packaging type that will be used if "
        "the product is dangerous.",
    )
    l10n_mx_edi_packaging_description = fields.Char(
        "Packaging Decription",
        help="This value will be used in the CFDI for carta porte to express the descripcion of the packaging of "
        "the product if is dangerous.",
    )


class ProductUnspscCode(models.Model):
    _inherit = "product.unspsc.code"

    l10n_mx_edi_dangerous_material = fields.Selection(
        selection=[
            ("0", _("Non-dangerous material")),
            ("01", _("Material that could or not be dangerous")),
            ("1", _("Material dangerous")),
        ],
        string="Is dangerous material?",
        default="0",
        help="Indicates if this product type is dangerous according the sat catalog for carta porte. "
        "If the the product code is dangerous, the dangerous type should be specified in the product template. "
        "When the product is marked as could or not be dangerous, the CFDI will send No at MaterialPeligroso if the "
        "dangerous code is not specified in the product.",
    )


class ProductDangerousSatCode(models.Model):
    """Product dangerous Codes from carta porte SAT Data.
    This code must be defined in CFDI 3.3 for carta porte at c_MaterialPeligroso
    """

    _name = "l10n_mx_edi.product.dangerous.sat.code"
    _description = "Product dangerous Codes from carta porte SAT Data."

    name = fields.Char(help="Name defined by SAT catalog to this product", required=True)
    code = fields.Char(
        help="This value is required in CFDI version 3.3 to express the "
        "code of a product or service consider as dangerous by the SAT, "
        "used a key from SAT catalog.",
        required=True,
    )
    class_div = fields.Char(help="Clase o div. Type of danger according SAT catalog.")
    active = fields.Boolean(help="If this record is not active, this cannot be selected.", default=True)

    def name_get(self):
        result = []
        for prod in self:
            result.append((prod.id, "%s %s" % (prod.code, prod.name or "")))
        return result

    @api.model
    def _name_search(self, name, args=None, operator="ilike", limit=100, name_get_uid=None):
        args = args or []
        if operator == "ilike" and not (name or "").strip():
            domain = []
        else:
            domain = ["|", ("name", "ilike", name), ("code", "ilike", name)]
        return self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)


class ProductPackagingSatCode(models.Model):
    """Product packaging Codes from carta porte SAT Data.
    This code must be defined in CFDI 3.3 for carta porte at c_TipoEmbalaje
    """

    _name = "l10n_mx_edi.product.packaging.sat.code"
    _description = "Product packaging Codes from carta porte SAT Data."

    name = fields.Char(help="Name defined by SAT catalog to this packing", required=True)
    code = fields.Char(
        required=True,
        help="This value is required in CFDI version 3.3 to express the "
        "SAT code of the packaging that will be used for this dangerous product.",
    )
    active = fields.Boolean(help="If this record is not active, this cannot be selected.", default=True)

    def name_get(self):
        result = []
        for prod in self:
            result.append((prod.id, "%s %s" % (prod.code, prod.name or "")))
        return result

    @api.model
    def _name_search(self, name, args=None, operator="ilike", limit=100, name_get_uid=None):
        args = args or []
        if operator == "ilike" and not (name or "").strip():
            domain = []
        else:
            domain = ["|", ("name", "ilike", name), ("code", "ilike", name)]
        return self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
