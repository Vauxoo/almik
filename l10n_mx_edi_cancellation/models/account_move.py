# Copyright 2019 Vauxoo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import requests
from lxml.objectify import fromstring

from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_repr


class AccountMove(models.Model):
    _inherit = "account.move"

    l10n_mx_edi_cancellation_date = fields.Date(
        "Cancellation Date", readonly=True, copy=False, help="Save the cancellation date of the CFDI in the SAT"
    )
    l10n_mx_edi_cancellation_time = fields.Char(
        "Cancellation Time", readonly=True, copy=False, help="Save the cancellation time of the CFDI in the SAT"
    )
    date_cancel = fields.Date(
        "Cancel Date",
        readonly=True,
        copy=False,
        help='Save the moment when the invoice state change to "cancel" in Odoo.',
    )
    l10n_mx_edi_cancellation = fields.Char(
        string="Cancellation Case",
        copy=False,
        tracking=True,
        help="The SAT has 4 cases in which an invoice could be cancelled, please fill this field based on your case:\n"
        "Case 1: The invoice was generated with errors and must be re-invoiced, the format must be:\n"
        '"01" The UUID will be take from the new invoice related to the record.\n'
        "Case 2: The invoice has an error on the customer, this will be cancelled and replaced by a new with the "
        'customer fixed. The format must be:\n "02", only is required the case number.\n'
        "Case 3: The invoice was generated but the operation was cancelled, this will be cancelled and not must be "
        'generated a new invoice. The format must be:\n "03", only is required the case number.\n'
        'Case 4: Global invoice. The format must be:\n "04", only is required the case number.',
    )

    @api.depends("state", "edi_document_ids.state", "l10n_mx_edi_cancellation")
    def _compute_show_reset_to_draft_button(self):
        # OVERRIDE
        res = super()._compute_show_reset_to_draft_button()

        for move in self:
            for doc in move.edi_document_ids:
                move_applicability = doc.edi_format_id._get_move_applicability(move)
                check = (
                    doc.edi_format_id._needs_web_services()
                    and doc.state in ("sent", "to_cancel")
                    and move_applicability
                    and move_applicability.get("cancel")
                    and move.l10n_mx_edi_cancellation == "01"
                )
                if check:
                    move.show_reset_to_draft_button = True
                    break
        return res

    def button_draft(self):
        self.write({"date_cancel": False})
        inv_mx = self.filtered(lambda inv: inv.company_id.country_id == self.env.ref("base.mx"))
        if not inv_mx:
            return super().button_draft()
        # Avoid reset the EDI values if cancellation is 01
        cfdi_format = self.env.ref("l10n_mx_edi.edi_cfdi_3_3")
        cfdi_documents = self.edi_document_ids.filtered(lambda d: d.edi_format_id == cfdi_format)
        data = cfdi_documents.read(["state", "error"])
        # Invoices reverted out of period not must be reset 2 draft
        out_period = inv_mx._l10n_mx_edi_get_moves_out_period()
        res = super(AccountMove, self - out_period).button_draft()
        cfdi_documents.l10n_mx_edi_reset_edi_state(data)
        return res

    def button_cancel(self):
        """Mexican customer invoices/refunds are considered."""
        # Ignore draft records
        draft_records = self.filtered(lambda i: not i.posted_before)
        records = self - draft_records

        records.write({"date_cancel": fields.Date.today()})
        inv_mx = records.filtered(
            lambda inv: inv.move_type in ("out_invoice", "out_refund")
            and inv.company_id.country_id == self.env.ref("base.mx")
        )
        # Not Mexican customer/refund invoices
        result = super(AccountMove, self - inv_mx).button_cancel()
        if not inv_mx:
            return result

        # Avoid reset the EDI values if cancellation is 01
        cfdi_format = self.env.ref("l10n_mx_edi.edi_cfdi_3_3")
        edi_documents = self.edi_document_ids.filtered(lambda d: d.edi_format_id == cfdi_format)
        data = edi_documents.read(["state", "error"])

        invoices = inv_mx._l10n_mx_edi_action_cancel_checks()

        inv_no_mx = self - inv_mx
        to_cancel = inv_no_mx + invoices

        # Case 02, 03 and 04 must be cancelled first in the SAT
        to_request = to_cancel.filtered(lambda i: i.l10n_mx_edi_cancellation in ("02", "03", "04"))
        # Invoices reverted out of period not must be reset 2 draft
        out_period = to_request._l10n_mx_edi_get_moves_out_period()
        super(AccountMove, to_request - out_period).button_cancel()

        # To avoid the Odoo message that not allow cancel an invoice if is not cancelled in the SAT, force the
        # context that is used when is called from the cron
        result = super(AccountMove, (to_cancel - to_request).with_context(called_from_cron=True)).button_cancel()

        edi_documents.l10n_mx_edi_reset_edi_state(data)
        return result

    def _l10n_mx_edi_action_cancel_checks(self):
        # Ensure that cancellation case is defined correctly for customer invoices
        out_invoices = self.filtered(lambda inv: inv.move_type in ("out_invoice", "out_refund"))
        if out_invoices.filtered(lambda i: i.edi_state in ("sent", "to_cancel") and not i.l10n_mx_edi_cancellation):
            raise UserError(_("In order to allow cancel, please define the cancellation case."))
        if out_invoices.filtered(
            lambda i: i.edi_state in ("sent", "to_cancel")
            and i.l10n_mx_edi_cancellation.split("|")[0] not in ["01", "02", "03", "04"]
        ):
            raise UserError(_("In order to allow cancel, please define a correct cancellation case."))

        # Ensure that invoices are not paid
        inv_paid = self.filtered(lambda inv: inv.payment_state in ["in_payment", "paid"])
        for inv in inv_paid:
            inv.message_post(body=_("Invoice must be in draft or open state in order to be cancelled."))

        return self - inv_paid

    def button_cancel_with_reversal(self):
        """Used on posted invoices in a closed period.
        This action will to mark the invoice to be cancelled with reversal when the customer accept the cancellation"""
        self._l10n_mx_edi_action_cancel_checks()
        if self.filtered(lambda i: i.state != "posted"):
            raise UserError(_("This option only could be used on posted invoices."))

        lock_date = self._get_lock_date()
        if not lock_date:
            raise UserError(_("This option only could be used if the accounting closing dates are defined."))

        invoices = self.filtered(lambda inv: inv.invoice_date and inv.invoice_date <= lock_date)
        if not invoices:
            raise UserError(_("This option only could be used on invoices out of period."))

        for inv in invoices:
            default_values_list = [{"date": fields.Date.today(), "invoice_date": fields.Date.today()}]
            inv.button_mx_cancel_posted_moves()

            # If the invoice already is cancelled, the PAC status is cancelled to avoid call the WebService
            if inv.l10n_mx_edi_sat_status == "cancelled":
                inv.edi_document_ids.filtered(lambda edi: edi.state == "to_cancel").write(
                    {"state": "cancelled", "error": False, "blocking_level": False}
                )

            if (
                inv.move_type in ("out_invoice", "out_refund")
                and inv.company_id.l10n_mx_edi_reversal_customer_journal_id
            ):
                default_values_list[0]["journal_id"] = inv.company_id.l10n_mx_edi_reversal_customer_journal_id.id
            elif (
                inv.move_type in ("in_invoice", "in_refund")
                and inv.company_id.l10n_mx_edi_reversal_supplier_journal_id
            ):
                default_values_list[0]["journal_id"] = inv.company_id.l10n_mx_edi_reversal_supplier_journal_id.id
            reversal = inv.sudo()._reverse_moves(default_values_list=default_values_list, cancel=True)
            reversal.edi_document_ids.unlink()
            reversal.l10n_mx_edi_origin = ""

    def button_mx_cancel_posted_moves(self):
        """Mark the edi.document related to this move to be canceled. Duplicated from button_cancel_posted_moves to
        avoid check_fiscalyear_lock_date on this module"""
        to_cancel_documents = self.env["account.edi.document"]
        for move in self:
            is_move_marked = False
            for doc in move.edi_document_ids:
                move_applicability = doc.edi_format_id._get_move_applicability(move)
                if (
                    doc.edi_format_id._needs_web_services()
                    and doc.state == "sent"
                    and move_applicability
                    and move_applicability.get("cancel")
                ):
                    to_cancel_documents |= doc
                    is_move_marked = True
            if is_move_marked:
                move.message_post(body=_("A cancellation of the EDI has been requested."))

        to_cancel_documents.write({"state": "to_cancel", "error": False, "blocking_level": False})

    def _get_lock_date(self):
        """Returns the lock date based on company's period and fiscal year lock dates."""
        company = self[:1].company_id
        lock_date = (
            max(company.period_lock_date, company.fiscalyear_lock_date)
            if company.period_lock_date and company.fiscalyear_lock_date
            else company.period_lock_date or company.fiscalyear_lock_date
        )

        if self.user_has_groups("account.group_account_manager"):
            lock_date = company.fiscalyear_lock_date
        if self._context.get("force_cancellation_date"):
            lock_date = fields.Datetime.from_string(self._context["force_cancellation_date"]).date()

        return lock_date

    def _l10n_mx_edi_get_moves_out_period(self):
        """Return the reverted invoices out of period"""
        if not self:
            return self
        company = self[0].company_id
        lock_date = (
            max(company.period_lock_date, company.fiscalyear_lock_date)
            if company.period_lock_date and company.fiscalyear_lock_date
            else company.period_lock_date or company.fiscalyear_lock_date
        )

        return self.filtered(
            lambda inv: inv.payment_state == "reversed" and inv.invoice_date and inv.invoice_date <= lock_date
        )

    def _l10n_mx_edi_cancel_status(self):
        self.ensure_one()
        namespace = {"a": "http://schemas.datacontract.org/2004/07/Sat.Cfdi.Negocio.ConsultaCfdi.Servicio"}
        supplier_rfc = self.l10n_mx_edi_cfdi_supplier_rfc
        customer_rfc = self.l10n_mx_edi_cfdi_customer_rfc
        total = float_repr(self.l10n_mx_edi_cfdi_amount, precision_digits=self.currency_id.decimal_places)
        uuid = self.l10n_mx_edi_cfdi_uuid

        response = self._l10n_mx_edi_get_sat_response(supplier_rfc, customer_rfc, total, uuid)
        if isinstance(response, str):
            return {}
        status = response.xpath("//a:Estado", namespaces=namespace)
        if status and status[0] == "Cancelado":
            return {"success": True}
        status = response.xpath("//a:EstatusCancelacion", namespaces=namespace)
        if status and status[0] == "En proceso":
            return {"error": True}
        return {}

    def _l10n_mx_edi_get_sat_response(self, supplier_rfc, customer_rfc, total, uuid):
        """Synchronize both systems: Odoo & SAT to make sure the invoice is valid."""
        url = "https://consultaqr.facturaelectronica.sat.gob.mx/ConsultaCFDIService.svc?wsdl"
        headers = {
            "SOAPAction": "http://tempuri.org/IConsultaCFDIService/Consulta",
            "Content-Type": "text/xml; charset=utf-8",
        }
        template = """<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:ns0="http://tempuri.org/" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
 xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
   <SOAP-ENV:Header/>
   <ns1:Body>
      <ns0:Consulta>
         <ns0:expresionImpresa>${data}</ns0:expresionImpresa>
      </ns0:Consulta>
   </ns1:Body>
</SOAP-ENV:Envelope>"""  # noqa
        params = "<![CDATA[?re=%s&rr=%s&tt=%s&id=%s]]>" % (
            tools.html_escape(supplier_rfc or ""),
            tools.html_escape(customer_rfc or ""),
            total or 0.0,
            uuid or "",
        )
        soap_env = template.format(data=params)
        try:
            soap_xml = requests.post(url, data=soap_env, headers=headers, timeout=20)
            response = fromstring(soap_xml.text)
        except Exception as e:
            return "error %s" % str(e)
        return response
