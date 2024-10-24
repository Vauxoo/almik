from lxml.objectify import fromstring

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    l10n_mx_edi_legend_ids = fields.Many2many(
        "l10n_mx_edi.fiscal.legend",
        string="Fiscal Legends",
        compute="_compute_l10n_mx_edi_legends_ids",
        store=True,
        readonly=False,
        tracking=True,
        help="Legends under tax provisions, other than those contained in the Mexican CFDI standard.",
    )

    @api.depends("partner_id")
    def _compute_l10n_mx_edi_legends_ids(self):
        for move in self:
            move.l10n_mx_edi_legend_ids = move.partner_id.l10n_mx_edi_legend_ids or move.l10n_mx_edi_legend_ids

    def _l10n_mx_edi_decode_cfdi(self, cfdi_data=None):
        """If the CFDI was signed, try to adds the schemaLocation correctly"""
        result = super()._l10n_mx_edi_decode_cfdi(cfdi_data=cfdi_data)
        if not cfdi_data:
            return result
        if not isinstance(cfdi_data, bytes):
            cfdi_data = cfdi_data.encode()
        cfdi_data = cfdi_data.replace(b"xmlns__leyendasFisc", b"xmlns:leyendasFisc")
        cfdi = fromstring(cfdi_data)
        if "leyendasFisc" not in cfdi.nsmap:
            return result
        cfdi.attrib["{http://www.w3.org/2001/XMLSchema-instance}schemaLocation"] = "%s %s %s" % (
            cfdi.get("{http://www.w3.org/2001/XMLSchema-instance}schemaLocation"),
            "http://www.sat.gob.mx/leyendasFiscales",
            "http://www.sat.gob.mx/sitio_internet/cfd/leyendasFiscales/leyendasFisc.xsd",
        )
        result["cfdi_node"] = cfdi
        return result
