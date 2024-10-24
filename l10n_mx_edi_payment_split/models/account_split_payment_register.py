from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.split.payment.register"

    @api.model
    def _l10n_mx_edi_factoring_domain(self):
        if "l10n_mx_edi_factoring_id" not in self.env["account.payment"]._fields:
            return []
        return [("l10n_mx_edi_factoring", "=", True)]

    l10n_mx_edi_payment_method_id = fields.Many2one(
        comodel_name="l10n_mx_edi.payment.method",
        string="Payment Way",
        readonly=False,
        store=True,
        compute="_compute_l10n_mx_edi_payment_method_id",
        help="Indicates the way the payment was/will be received, where the options could be: "
        "Cash, Nominal Check, Credit Card, etc.",
    )
    l10n_mx_edi_show_factoring = fields.Boolean(
        compute="_compute_show_factoring", store=True, help="True if the factoring module is installed"
    )
    l10n_mx_edi_factoring_id = fields.Many2one(
        "res.partner",
        "Financial Factor",
        compute="_compute_factoring_id",
        domain=_l10n_mx_edi_factoring_domain,
        readonly=False,
        store=True,
        help="This payment was received from this factoring.",
    )
    l10n_mx_edi_origin = fields.Char(
        string="CFDI Origin",
        copy=False,
        help="In some cases like payments, credit notes, debit notes, invoices re-signed or invoices that are redone "
        "due to payment in advance will need this field filled, the format is:\n"
        "Origin Type|UUID1, UUID2, ...., UUIDn.\n"
        "Where the origin type could be:\n"
        "- 01: Nota de crédito\n"
        "- 02: Nota de débito de los documentos relacionados\n"
        "- 03: Devolución de mercancía sobre facturas o traslados previos\n"
        "- 04: Sustitución de los CFDI previos\n"
        "- 05: Traslados de mercancias facturados previamente\n"
        "- 06: Factura generada por los traslados previos\n"
        "- 07: CFDI por aplicación de anticipo",
    )

    @api.depends("journal_id")
    def _compute_show_factoring(self):
        is_installed = "l10n_mx_edi_factoring_id" in self.env["account.payment"]._fields
        for record in self:
            record.l10n_mx_edi_show_factoring = is_installed

    @api.depends("journal_id")
    def _compute_factoring_id(self):
        active_ids = self._context.get("active_ids")
        model = self._context.get("active_model")
        if model != "account.move" or not active_ids:
            return
        is_installed = "l10n_mx_edi_factoring_id" in self.env["account.payment"]._fields
        for wizard in self:
            invoice = self.env["account.move"].browse(self._context.get("active_ids", []))
            factor = (
                (invoice.l10n_mx_edi_factoring_id or invoice[0].partner_id.l10n_mx_edi_factoring_id)
                if is_installed
                else False
            )
            wizard.l10n_mx_edi_factoring_id = factor

    # -------------------------------------------------------------------------
    # HELPERS
    # -------------------------------------------------------------------------

    # REVIEWED
    @api.model
    def _get_line_split_batch_key(self, line):
        # OVERRIDE
        # Group moves also using these additional fields.
        res = super()._get_line_split_batch_key(line)
        res["l10n_mx_edi_payment_method_id"] = line.move_id.l10n_mx_edi_payment_method_id.id
        return res

    # -------------------------------------------------------------------------
    # COMPUTE METHODS
    # -------------------------------------------------------------------------

    # REVIEWED
    @api.depends("journal_id")
    def _compute_l10n_mx_edi_payment_method_id(self):
        for wizard in self:
            batches = wizard._get_split_batches(from_compute=True)
            wizard.l10n_mx_edi_payment_method_id = batches[0]["payment_values"]["l10n_mx_edi_payment_method_id"]

    # -------------------------------------------------------------------------
    # BUSINESS METHODS
    # -------------------------------------------------------------------------

    # REVIEWED
    def _create_payment_vals_from_split_batch(self, batch_result):
        # OVERRIDE
        payment_vals = super()._create_payment_vals_from_split_batch(batch_result)
        payment_vals["l10n_mx_edi_payment_method_id"] = self.l10n_mx_edi_payment_method_id.id
        payment_vals["l10n_mx_edi_origin"] = self.l10n_mx_edi_origin
        if "l10n_mx_edi_factoring_id" in self.env["account.payment"]._fields:
            payment_vals["l10n_mx_edi_factoring_id"] = self.l10n_mx_edi_factoring_id.id
        return payment_vals

    @api.constrains("l10n_mx_edi_origin")
    def _check_l10n_mx_edi_origin(self):
        error_message = _(
            "The following CFDI origin %s is invalid and must match the "
            "<code>|<uuid1>,<uuid2>,...,<uuidn> template.\n"
            "Here are the specification of this value:\n"
            "- 01: Nota de crédito\n"
            "- 02: Nota de débito de los documentos relacionados\n"
            "- 03: Devolución de mercancía sobre facturas o traslados previos\n"
            "- 04: Sustitución de los CFDI previos\n"
            "- 05: Traslados de mercancias facturados previamente\n"
            "- 06: Factura generada por los traslados previos\n"
            "- 07: CFDI por aplicación de anticipo\n"
            "For example: 01|89966ACC-0F5C-447D-AEF3-3EED22E711EE,89966ACC-0F5C-447D-AEF3-3EED22E711EE"
        )

        for split_payment in self.filtered("l10n_mx_edi_origin"):
            if not split_payment._l10n_mx_edi_read_cfdi_origin(split_payment.l10n_mx_edi_origin):
                raise ValidationError(error_message % split_payment.l10n_mx_edi_origin)

    @api.model
    def _l10n_mx_edi_read_cfdi_origin(self, cfdi_origin):
        splitted = cfdi_origin.split("|")
        if len(splitted) != 2 or not splitted:
            return False

        try:
            code = int(splitted[0])
        except ValueError:
            return False

        if code < 1 or code > 7:
            return False
        return splitted[0], [uuid.strip() for uuid in splitted[1].split(",")]
