import json

from zeep import Client
from zeep.transports import Transport

from odoo import _, models


class AccountEdiFormat(models.Model):
    _inherit = "account.edi.format"

    # pylint: disable=too-many-return-statements
    def _l10n_mx_edi_cancel_invoice(self, invoice):
        """Overwrite to 03 and 04"""
        sat_process = self._l10n_mx_edi_cancel_status(invoice)
        if sat_process:
            return sat_process

        # == Check the configuration ==
        errors = self._l10n_mx_edi_check_configuration(invoice)
        if errors:
            return {invoice: {"error": self._l10n_mx_edi_format_error_message(_("Invalid configuration:"), errors)}}

        # == Call the web-service ==
        pac_name = invoice.company_id.l10n_mx_edi_pac

        credentials = getattr(self, "_l10n_mx_edi_get_%s_credentials" % pac_name)(invoice.company_id)
        if credentials.get("errors"):
            return {
                invoice: {
                    "error": self._l10n_mx_edi_format_error_message(
                        _("PAC authentification error:"), credentials["errors"]
                    )
                }
            }

        if invoice.l10n_mx_edi_cancellation in ("01", "02"):
            result = super()._l10n_mx_edi_cancel_invoice(invoice)
            if not result[invoice].get("error"):
                return self._l10n_mx_edi_get_status(result, invoice, credentials)
            related = self._l10n_mx_edi_get_related(invoice, credentials)
            if related:
                result[invoice]["error"] = "%s\n%s" % (result[invoice].get("error", ""), related[0])
            return result

        uuid_replace = invoice.l10n_mx_edi_cancel_move_id.l10n_mx_edi_cfdi_uuid
        case = invoice.l10n_mx_edi_cancellation
        res = getattr(self, "_l10n_mx_edi_%s_cancel_case" % pac_name)(
            invoice.l10n_mx_edi_cfdi_uuid, invoice.company_id, credentials, uuid_replace=uuid_replace, case=case
        )
        if res.get("errors"):
            return {
                invoice: {
                    "error": self._l10n_mx_edi_format_error_message(_("PAC failed to cancel the CFDI:"), res["errors"])
                }
            }

        res = self._l10n_mx_edi_get_status(res, invoice, credentials)
        edi_result = {invoice: res}

        # == Chatter ==
        invoice.with_context(no_new_invoice=True).message_post(
            body=_("The CFDI document has been successfully cancelled."),
            subtype_xmlid="account.mt_invoice_validated",
        )

        return edi_result

    def _l10n_mx_edi_cancel_payment(self, payment):
        """Overwrite to 03 and 04"""
        sat_process = self._l10n_mx_edi_cancel_status(payment)
        if sat_process:
            return sat_process

        if payment.l10n_mx_edi_cancellation in ("01", "02"):
            return super()._l10n_mx_edi_cancel_payment(payment)

        # == Check the configuration ==
        errors = self._l10n_mx_edi_check_configuration(payment)
        if errors:
            return {payment: {"error": self._l10n_mx_edi_format_error_message(_("Invalid configuration:"), errors)}}

        # == Call the web-service ==
        pac_name = payment.company_id.l10n_mx_edi_pac

        credentials = getattr(self, "_l10n_mx_edi_get_%s_credentials" % pac_name)(payment.company_id)
        if credentials.get("errors"):
            return {
                payment: {
                    "error": self._l10n_mx_edi_format_error_message(
                        _("PAC authentification error:"), credentials["errors"]
                    )
                }
            }

        uuid_replace = payment.l10n_mx_edi_cancel_move_id.l10n_mx_edi_cfdi_uuid
        case = payment.l10n_mx_edi_cancellation
        res = getattr(self, "_l10n_mx_edi_%s_cancel_case" % pac_name)(
            payment.l10n_mx_edi_cfdi_uuid, payment.company_id, credentials, uuid_replace=uuid_replace, case=case
        )
        if res.get("errors"):
            return {
                payment: {
                    "error": self._l10n_mx_edi_format_error_message(_("PAC failed to cancel the CFDI:"), res["errors"])
                }
            }

        res = self._l10n_mx_edi_get_status(res, payment, credentials)
        edi_result = {payment: res}

        # == Chatter ==
        message = _("The CFDI document has been successfully cancelled.")
        payment.message_post(body=message)
        if payment.payment_id:
            payment.payment_id.message_post(body=message)

        return edi_result

    def _l10n_mx_edi_finkok_cancel_case(self, uuid, company, credentials, uuid_replace=None, case=None):
        certificates = company.l10n_mx_edi_certificate_ids
        certificate = certificates.sudo()._get_valid_certificate()
        cer_pem = certificate._get_pem_cer(certificate.content)
        key_pem = certificate._get_pem_key(certificate.key, certificate.password)
        try:
            transport = Transport(timeout=20)
            client = Client(credentials["cancel_url"], transport=transport)
            factory = client.type_factory("apps.services.soap.core.views")
            uuid_type = factory.UUID()
            uuid_type.UUID = uuid
            uuid_type.Motivo = case
            if uuid_replace:
                uuid_type.FolioSustitucion = uuid_replace
            docs_list = factory.UUIDArray(uuid_type)
            response = client.service.cancel(
                docs_list,
                credentials["username"],
                credentials["password"],
                company.vat,
                cer_pem,
                key_pem,
            )
        except Exception as e:
            return {
                "errors": [_("The Finkok service failed to cancel with the following error: %s", str(e))],
            }

        if not getattr(response, "Folios", None):
            code = getattr(response, "CodEstatus", None)
            msg = (
                _("Cancelling got an error") if code else _("A delay of 2 hours has to be respected before to cancel")
            )
        else:
            code = getattr(response.Folios.Folio[0], "EstatusUUID", None)
            cancelled = code in ("201", "202")  # cancelled or previously cancelled
            # no show code and response message if cancel was success
            code = "" if cancelled else code
            msg = "" if cancelled else _("Cancelling got an error")

        errors = []
        if code:
            errors.append(_("Code : %s", code))
        if msg:
            errors.append(_("Message : %s", msg))
        if errors:
            return {"errors": errors}

        return {"success": True}

    def _l10n_mx_edi_get_related(self, move, credentials):
        """Return the EDI documents related with the SAT system."""
        username = credentials["username"]
        password = credentials["password"]
        supplier_rfc = move.l10n_mx_edi_cfdi_supplier_rfc
        # Verify if document can be cancelled
        sat_status = self._l10n_mx_edi_finkok_get_status(
            move,
            username,
            password,
            supplier_rfc,
            move.l10n_mx_edi_cfdi_customer_rfc,
            move.l10n_mx_edi_cfdi_uuid,
            move.amount_total,
        )
        if not sat_status or sat_status.sat and (sat_status.sat.EsCancelable or "").upper() != "NO CANCELABLE":
            return []

        certificates = move.company_id.l10n_mx_edi_certificate_ids
        certificate = certificates.sudo()._get_valid_certificate()
        cer_pem = certificate._get_pem_cer(certificate.content)
        key_pem = certificate._get_pem_key(certificate.key, certificate.password)
        url = self._l10n_mx_edi_get_finkok_credentials(move.company_id)["cancel_url"]
        try:
            transport = Transport(timeout=20)
            client = Client(url, transport=transport)
            documents = client.service.get_related(
                username, password, supplier_rfc, uuid=move.l10n_mx_edi_cfdi_uuid, cer=cer_pem, key=key_pem
            )
        except Exception:
            return []

        if getattr(documents, "Padres", None) is None:
            return []

        # Get the documents related to the invoice to cancel
        uuids = []
        for padre in documents.Padres.Padre:
            uuids.append(getattr(padre, "uuid", ""))

        return [_("The next fiscal folios are related with this document: %s", "\n".join(uuids))]

    def _l10n_mx_edi_get_status(self, result, move, credentials):
        """Ensure that the SAT has received the cancel request"""
        sat_status = self._l10n_mx_edi_finkok_get_status(
            move,
            credentials["username"],
            credentials["password"],
            move.l10n_mx_edi_cfdi_supplier_rfc,
            move.l10n_mx_edi_cfdi_customer_rfc,
            move.l10n_mx_edi_cfdi_uuid,
            move.amount_total,
        )
        status = (
            sat_status and getattr(sat_status, "sat", None) and getattr(sat_status["sat"], "EstatusCancelacion", None)
        )
        if status == "En proceso":
            return {
                move: {
                    "error": self._l10n_mx_edi_format_error_message(
                        _("PAC failed to cancel the CFDI:"),
                        [
                            _(
                                "The PAC has sent this document for cancellation, but the customer has not yet "
                                "accepted it. Please wait for customer approval and try again in a few minutes, or "
                                "wait for the automatic action."
                            ),
                            _(
                                "SAT status for cancellation: %s",
                                getattr(sat_status, "EsCancelable", _("Not defined")),
                            ),
                        ],
                    )
                }
            }
        if not status or status == "None":
            return {
                move: {
                    "error": self._l10n_mx_edi_format_error_message(
                        _("PAC failed to cancel the CFDI:"),
                        [
                            _(
                                "The PAC has sent this document to cancel, but the SAT has not processed it yet. "
                                "Please try again in a few minutes or wait for the automatic action."
                            ),
                            _(
                                "SAT status for cancellation: %s",
                                getattr(sat_status, "EsCancelable", _("Not defined")),
                            ),
                        ],
                    )
                }
            }
        self._l10n_mx_edi_get_receipt(move, credentials)
        return result

    def _l10n_mx_edi_get_receipt(self, move, credentials):
        """Get the cancellation data from finkok"""
        response = self._l10n_mx_edi_finkok_get_receipt(
            move, credentials["username"], credentials["password"], move.company_id.vat, move.l10n_mx_edi_cfdi_uuid
        )
        if not response or not getattr(response, "date", None):
            return
        date = response.date
        move.l10n_mx_edi_cancellation_date = date.split("T")[0]
        move.l10n_mx_edi_cancellation_time = date.split("T")[1][:8]
        return

    def _l10n_mx_edi_finkok_get_status(self, move, username, password, supplier_rfc, customer_rfc, uuid, total):
        """Check the possible form of cancellation and the status of the CFDI.

        It allows to identify if the CFDI is cancellable.
        :param username: The username provided by the Finkok platform.
        :type str
        :param password: The password provided by the Finkok platform.
        :type str
        :param supplier_rfc: Taxpayer id - The RFC issuer of the invoices to consult.
        :type str
        :param customer_rfc: Rtaxpayer_id - The RFC receiver of the CFDI to consult.
        :type str
        :param uuid: The UUID of the CFDI to consult.
        :type str
        :param total:The value of the total attribute of the CFDI.
        :type float
        :returns: AcuseSatEstatus statusResponse  https://wiki.finkok.com/doku.php?id=get_sat_status
        :rtype: suds.sudsobject
        """
        url = self._l10n_mx_edi_get_finkok_credentials(move.company_id)["cancel_url"]
        try:
            transport = Transport(timeout=20)
            client = Client(url, transport=transport)
            return client.service.get_sat_status(
                username, password, supplier_rfc, customer_rfc, uuid=uuid, total=total
            )
        except Exception:
            return False

    def _l10n_mx_edi_finkok_get_receipt(self, move, username, password, vat, uuid, client=False):
        """get_receipt from finkok"""
        if not client:
            url = self._l10n_mx_edi_get_finkok_credentials(move.company_id)["cancel_url"]
            transport = Transport(timeout=20)
            client = Client(url, transport=transport)
        try:
            return client.service.get_receipt(username, password, vat, uuid)
        except Exception as e:
            self.l10n_mx_edi_log_error(str(e))
        return False

    def __l10n_mx_edi_sw_cancel(self, move, credentials, cfdi):
        """Overwrite the cancel method to:
        - Adapt to the new SAT changes where is required the cancellation type"""

        uuid_replace = move.l10n_mx_edi_cancel_invoice_id.l10n_mx_edi_cfdi_uuid
        headers = {"Authorization": "bearer " + credentials["token"], "Content-Type": "application/json"}
        certificates = move.company_id.l10n_mx_edi_certificate_ids
        certificate = certificates.sudo().get_valid_certificate()
        cancellation_data = (move.l10n_mx_edi_cancellation or "").split("|")
        payload_dict = {
            "rfc": move.company_id.vat,
            "b64Cer": certificate.content.decode("UTF-8"),
            "b64Key": certificate.key.decode("UTF-8"),
            "password": certificate.password,
            "uuid": move.l10n_mx_edi_cfdi_uuid,
            "motivo": cancellation_data[0],
        }
        if uuid_replace:
            payload_dict["folioSustitucion"] = uuid_replace
        payload = json.dumps(payload_dict)

        response_json = self._l10n_mx_edi_sw_call(credentials["cancel_url"], headers, payload=payload.encode("UTF-8"))

        cancelled = response_json["status"] == "success"
        if cancelled:
            return {"success": cancelled}

        code = response_json.get("message")
        msg = response_json.get("messageDetail")
        errors = []
        if code:
            errors.append(_("Code : %s", code))
        if msg:
            errors.append(_("Message : %s", msg))
        return {"errors": errors}

    def _l10n_mx_edi_cancel_status(self, invoice):
        """Call before to try to cancel in the PAC o ensure that is not already cancelled or in process
        to cancel, to avoid affect the PAC process"""
        edi_result = {}
        result = invoice._l10n_mx_edi_cancel_status()
        if not result:
            return edi_result
        if result.get("success"):
            edi_result[invoice] = {"success": True}
            invoice.with_context(no_new_invoice=True).message_post(
                body=_("The CFDI document has been successfully cancelled."),
                subtype_xmlid="account.mt_invoice_validated",
            )
        elif result.get("error"):
            edi_result[invoice] = {
                "error": self._l10n_mx_edi_format_error_message(
                    _("PAC failed to cancel the CFDI:"),
                    _(
                        "The cancel process is waiting by the customer approval, please retry when the customer "
                        "accept the cancellation."
                    ),
                )
            }

        return edi_result
