import json
from collections import defaultdict

from odoo import api, models
from odoo.tools.float_utils import float_round

EQUIVALENCIADR_PRECISION_DIGITS = 10


class AccountEdiFormat(models.Model):
    _inherit = "account.edi.format"

    @api.model
    def _l10n_mx_edi_get_serie_and_folio(self, move):
        res = super()._l10n_mx_edi_get_serie_and_folio(move)
        res.update(**self._l10n_mx_edi_update_currency_data(move))
        res.update(**self._l10n_mx_edi_get_values_for_cfdi_from_invoice(move))
        return res

    @api.model
    def _l10n_mx_edi_get_payment_cfdi_values(self, move):
        self.ensure_one()
        res = super()._l10n_mx_edi_get_payment_cfdi_values(move)
        res.update(**self._l10n_mx_edi_update_currency_data(move))
        res.update(**self._l10n_mx_edi_get_values_for_cfdi_from_invoice(move))

        return res

    def _l10n_mx_edi_update_currency_data(self, move):  # pylint: disable=too-complex
        def get_tax_cfdi_name(env, tax_detail_vals):
            tags = set()
            for detail in tax_detail_vals["group_tax_details"]:
                for tag in env["account.tax.repartition.line"].browse(detail["tax_repartition_line_id"]).tag_ids:
                    tags.add(tag)
            tags = list(tags)
            if len(tags) == 1:
                return {"ISR": "001", "IVA": "002", "IEPS": "003"}.get(tags[0].name)
            if tax_detail_vals["tax"].l10n_mx_tax_type == "Exento":
                return "002"
            return None

        def divide_tax_details(env, invoice, tax_details, amount_paid):
            percentage_paid = amount_paid / invoice.amount_total
            precision = invoice.currency_id.decimal_places
            for detail in tax_details["tax_details"].values():
                tax = detail["tax"]
                tax_amount = (
                    abs(tax.amount) / 100.0
                    if tax.amount_type != "fixed"
                    else abs(detail["tax_amount_currency"] / detail["base_amount_currency"])
                )
                base_val_proportion = float_round(detail["base_amount_currency"] * percentage_paid, precision)
                tax_val_proportion = float_round(base_val_proportion * tax_amount, precision)
                detail.update(
                    {
                        "base_val_prop_amt_curr": base_val_proportion,
                        "tax_val_prop_amt_curr": tax_val_proportion if tax.l10n_mx_tax_type != "Exento" else False,
                        "tax_class": get_tax_cfdi_name(env, detail),
                        "tax_amount": tax_amount,
                    }
                )
            return tax_details

        if self.env["ir.config_parameter"].sudo().get_param("skip_sign_with_l10n_mx_edi_payment_split"):
            return {}

        if not move.payment_id.payment_split_data:
            return {}

        currency = move.payment_id.currency_id

        # === Decode the reconciliation to extract invoice data ===
        pay_rec_lines = move.line_ids.filtered(
            lambda line: line.account_type in ("asset_receivable", "liability_payable")
        )
        exchange_move_x_invoice = {}
        reconciliation_vals = defaultdict(
            lambda: {
                "amount_currency": 0.0,
                "balance": 0.0,
                "exchange_balance": 0.0,
            }
        )
        for match_field in ("credit", "debit"):

            # Peek the partials linked to exchange difference first in order to separate them from the partials
            # linked to invoices.
            for partial in pay_rec_lines[f"matched_{match_field}_ids"].sorted(lambda x: not x.exchange_move_id):
                counterpart_move = partial[f"{match_field}_move_id"].move_id
                if counterpart_move.l10n_mx_edi_cfdi_request:
                    # Invoice.

                    # Gather all exchange moves.
                    if partial.exchange_move_id:
                        exchange_move_x_invoice[partial.exchange_move_id] = counterpart_move

                    invoice_vals = reconciliation_vals[counterpart_move]
                    invoice_vals["amount_currency"] += partial[f"{match_field}_amount_currency"]
                    invoice_vals["balance"] += partial.amount
                elif counterpart_move in exchange_move_x_invoice:
                    # Exchange difference.
                    invoice_vals = reconciliation_vals[exchange_move_x_invoice[counterpart_move]]
                    invoice_vals["exchange_balance"] += partial.amount

        # === Create remaining values to create the CFDI ===
        if currency == move.company_currency_id:
            # Same currency
            payment_exchange_rate = None
        else:
            # Multi-currency
            payment_split_data = json.loads(move.payment_id.payment_split_data)
            lines = payment_split_data.get("payment_invoice_ids", [])
            total_amount_currency = abs(sum(line.get("payment_currency_amount") for line in lines))
            total_amount = abs(sum(line.get("company_currency_amount") for line in lines))
            payment_exchange_rate = float_round(
                total_amount / total_amount_currency,
                precision_digits=6,
                rounding_method="UP",
            )

        # === Create the list of invoice data ===
        invoice_vals_list = []
        for invoice, invoice_vals in reconciliation_vals.items():

            # Compute 'number_of_payments' & add amounts from exchange difference.
            payment_ids = set()
            inv_pay_rec_lines = invoice.line_ids.filtered(
                lambda line: line.account_type in ("asset_receivable", "liability_payable")
            )
            for field in ("debit", "credit"):
                for partial in inv_pay_rec_lines[f"matched_{field}_ids"]:
                    counterpart_move = partial[f"{field}_move_id"].move_id

                    if counterpart_move.payment_id or counterpart_move.statement_line_id:
                        payment_ids.add(counterpart_move.id)
            number_of_payments = len(payment_ids)

            if invoice.currency_id == currency:
                # Same currency
                invoice_exchange_rate = None
            elif currency == move.company_currency_id:
                # Payment expressed in MXN but the invoice is expressed in another currency.
                # The payment has been reconciled using the currency of the invoice, not the MXN.
                # Then, we retrieve the rate from amounts gathered from the reconciliation using the balance of the
                # exchange difference line allowing to switch from the "invoice rate" to the "payment rate".
                invoice_exchange_rate = float_round(
                    invoice_vals["amount_currency"] / (invoice_vals["balance"] + invoice_vals["exchange_balance"]),
                    precision_digits=EQUIVALENCIADR_PRECISION_DIGITS,
                    rounding_method="UP",
                )
            elif invoice.currency_id == move.company_currency_id:
                # Invoice expressed in MXN but Payment expressed in other currency
                invoice_exchange_rate = payment_exchange_rate
            else:
                # Multi-currency
                invoice_exchange_rate = float_round(
                    invoice_vals["amount_currency"] / invoice_vals["balance"],
                    precision_digits=6,
                    rounding_method="UP",
                )

            # for CFDI 4.0
            cfdi_values = self._l10n_mx_edi_get_invoice_cfdi_values(invoice)
            tax_details_transferred = divide_tax_details(
                self.env, invoice, cfdi_values["tax_details_transferred"], invoice_vals["amount_currency"]
            )
            tax_details_withholding = divide_tax_details(
                self.env, invoice, cfdi_values["tax_details_withholding"], invoice_vals["amount_currency"]
            )

            invoice_vals_list.append(
                {
                    "invoice": invoice,
                    "exchange_rate": invoice_exchange_rate,
                    "payment_policy": invoice.l10n_mx_edi_payment_policy,
                    "number_of_payments": number_of_payments,
                    "amount_paid": invoice_vals["amount_currency"],
                    "amount_before_paid": invoice.amount_residual + invoice_vals["amount_currency"],
                    "tax_details_transferred": tax_details_transferred,
                    "tax_details_withholding": tax_details_withholding,
                    "equivalenciadr_precision_digits": EQUIVALENCIADR_PRECISION_DIGITS,
                    **self._l10n_mx_edi_get_serie_and_folio(invoice),
                }
            )

        # CFDI 4.0: prepare the tax summaries
        rate_payment_curr_mxn_40 = payment_exchange_rate or 1
        mxn_currency = self.env["res.currency"].search([("name", "=", "MXN")], limit=1)
        total_taxes_paid = {}
        total_taxes_withheld = {
            "001": {"amount_curr": 0.0, "amount_mxn": 0.0},
            "002": {"amount_curr": 0.0, "amount_mxn": 0.0},
            "003": {"amount_curr": 0.0, "amount_mxn": 0.0},
            None: {"amount_curr": 0.0, "amount_mxn": 0.0},
        }
        for inv_vals in invoice_vals_list:
            wht_detail = list(inv_vals["tax_details_withholding"]["tax_details"].values())
            trf_detail = list(inv_vals["tax_details_transferred"]["tax_details"].values())
            for detail in wht_detail + trf_detail:
                tax = detail["tax"]
                tax_class = detail["tax_class"]
                key = (float_round(tax.amount / 100, 6), tax.l10n_mx_tax_type, tax_class)
                base_val_pay_curr = detail["base_val_prop_amt_curr"] / (inv_vals["exchange_rate"] or 1.0)
                tax_val_pay_curr = detail["tax_val_prop_amt_curr"] / (inv_vals["exchange_rate"] or 1.0)
                if key in total_taxes_paid:
                    total_taxes_paid[key]["base_value"] += base_val_pay_curr
                    total_taxes_paid[key]["tax_value"] += tax_val_pay_curr
                elif tax.amount >= 0:
                    total_taxes_paid[key] = {
                        "base_value": base_val_pay_curr,
                        "tax_value": tax_val_pay_curr,
                        "tax_amount": float_round(detail["tax_amount"], 6),
                        "tax_type": tax.l10n_mx_tax_type,
                        "tax_class": tax_class,
                        "tax_spec": "W" if tax.amount < 0 else "T",
                    }
                else:
                    total_taxes_withheld[tax_class]["amount_curr"] += tax_val_pay_curr

        # CFDI 4.0: rounding needs to be done after all DRs are added
        for v in total_taxes_paid.values():
            v["base_value"] = float_round(v["base_value"], move.currency_id.decimal_places)
            v["tax_value"] = float_round(v["tax_value"], move.currency_id.decimal_places)
            v["base_value_mxn"] = float_round(v["base_value"] * rate_payment_curr_mxn_40, mxn_currency.decimal_places)
            v["tax_value_mxn"] = float_round(v["tax_value"] * rate_payment_curr_mxn_40, mxn_currency.decimal_places)
        for v in total_taxes_withheld.values():
            v["amount_curr"] = float_round(v["amount_curr"], move.currency_id.decimal_places)
            v["amount_mxn"] = float_round(v["amount_curr"] * rate_payment_curr_mxn_40, mxn_currency.decimal_places)

        cfdi_values = {
            "currency": currency,
            "amount": move.payment_id.amount,
            "amount_mxn": float_round(move.payment_id.amount * rate_payment_curr_mxn_40, mxn_currency.decimal_places),
            "rate_payment_curr_mxn": payment_exchange_rate,
            "rate_payment_curr_mxn_40": rate_payment_curr_mxn_40,
            "tax_summary": total_taxes_paid,
            "withholding_summary": total_taxes_withheld,
        }
        return cfdi_values

    def _l10n_mx_edi_get_values_for_cfdi_from_invoice(self, invoice):
        if self.env["ir.config_parameter"].sudo().get_param("skip_sign_with_l10n_mx_edi_payment_split"):
            return {}

        values = {}

        move = self._context.get("l10n_mx_edi_payment_split")

        if not move or not move.payment_id.payment_split_data:
            return values

        res = invoice.invoice_payments_widget
        if not res:
            return values
        content = res.get("content", [])
        if not content:
            return values

        invoice_line = invoice.line_ids.filtered(
            lambda line: line.account_id.account_type in ("asset_receivable", "liability_payable")
        )
        exchange_journal = invoice.company_id.currency_exchange_journal_id
        apr_records = invoice_line.matched_debit_ids | invoice_line.matched_credit_ids
        fx_lines = (apr_records.debit_move_id | apr_records.credit_move_id).filtered(
            lambda line: line.journal_id == exchange_journal
        )
        exchange_move = fx_lines.mapped("move_id")

        # Let us exclude the FX Journal Entry from the content
        # content gives us how many installments have been made to this invoice
        content = [
            line for line in content if line.get("move_id") not in exchange_move.ids and not line.get("is_exchange")
        ]
        previous = [line for line in content if line.get("move_id") != move.id]
        this_payment = [line for line in content if line.get("move_id") == move.id]
        previous_payments = sum(x.get("amount") for x in previous)
        amount_before_paid = invoice.amount_total - previous_payments
        amount_paid = sum(x.get("amount") for x in this_payment)

        values = {
            "payment_policy": invoice.l10n_mx_edi_payment_policy,
            "amount_paid": amount_paid,
            "amount_before_paid": amount_before_paid,
        }
        if move.currency_id == invoice.currency_id:
            values["exchange_rate"] = None
            return values

        try:
            # NOTE: We have all the data on how the this payment was computed by
            # the user saved at `payment_split_data` field
            payment_split_data = json.loads(move.payment_id.payment_split_data)
            payment_invoice_ids = payment_split_data["payment_invoice_ids"]
            pline = [x for x in payment_invoice_ids if x.get("invoice_id") == invoice.id]
            values["exchange_rate"] = float_round(
                pline[0]["payment_amount"] / pline[0]["payment_currency_amount"],
                precision_digits=10,
                rounding_method="UP",
            )
        except json.decoder.JSONDecodeError:
            values = {}
        except KeyError:
            values = {}
        except IndexError:
            values = {}
        except TypeError:
            values = {}
        except ZeroDivisionError:
            values = {}

        return values

    def _l10n_mx_edi_export_payment_cfdi(self, move):
        # NOTE: This method is done this way to avoid tampering with the
        # signing process for the payments that are created through the core
        # functionality. Only our payments coming from Payment Split will be
        # using our way of signing. As an afterthought: Maybe this code get ridden?
        if not move.payment_id or not move.payment_id.payment_split_data:
            return super()._l10n_mx_edi_export_payment_cfdi(move)
        # Let us pass the move (payment) as a context in order to cache it later
        return super(
            AccountEdiFormat, self.with_context(l10n_mx_edi_payment_split=move)
        )._l10n_mx_edi_export_payment_cfdi(move)
