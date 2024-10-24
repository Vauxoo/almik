from datetime import timedelta

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.l10n_mx_edi_40.tests.common import TestMxEdiCommon


@tagged("post_install", "-at_install")
class TestAccountPaymentReversal(TestMxEdiCommon):
    def setUp(self):
        super().setUp()
        self.company = self.env.user.company_id
        self.company.sudo().search([("name", "=", "ESCUELA KEMPER URGATE")]).write(
            {"name": "ESCUELA KEMPER URGATE TEST"}
        )
        self.company.name = "ESCUELA KEMPER URGATE"
        self.certificate._check_credentials()
        self.company.l10n_mx_edi_pac = "finkok"

    def _invoice_preparation(self, invoice):
        invoice.invoice_date = False
        invoice.currency_id = self.env.ref("base.MXN")
        isr = self.env["account.account.tag"].search([("name", "=", "ISR")])
        iva = self.env["account.account.tag"].search([("name", "=", "IVA")])
        invoice.invoice_line_ids.tax_ids.filtered(lambda t: t.amount <= 0).invoice_repartition_line_ids.tag_ids |= isr
        invoice.invoice_line_ids.tax_ids.filtered(lambda t: t.amount > 0).invoice_repartition_line_ids.tag_ids |= iva
        invoice.l10n_mx_edi_payment_method_id = self.env.ref("l10n_mx_edi.payment_method_efectivo")
        invoice.l10n_mx_edi_usage = "S01"

    def test_cancel_01(self):
        """Try to cancel an invoice with case 01"""
        invoice = self.invoice
        self._invoice_preparation(invoice)
        invoice.action_post()
        generated_files = self._process_documents_web_services(invoice, {"cfdi_3_3"})
        self.assertTrue(generated_files, invoice.edi_error_message)
        self.assertEqual(invoice.edi_state, "sent", invoice.edi_error_message)
        invoice.l10n_mx_edi_cancellation = "01"
        invoice.button_cancel_posted_moves()
        self._process_documents_web_services(invoice, {"cfdi_3_3"})
        invoice.button_draft()
        invoice.button_cancel()
        invoice2 = invoice.copy({"l10n_mx_edi_origin": "04|%s" % invoice.l10n_mx_edi_cfdi_uuid})
        invoice2.action_post()
        self._process_documents_web_services(invoice2, {"cfdi_3_3"})
        self.assertEqual(invoice2.edi_state, "sent", invoice2.edi_error_message)
        self._process_documents_web_services(invoice, {"cfdi_3_3"})
        self.assertTrue(invoice.edi_state in ("cancelled", "to_cancel"), invoice.edi_error_message)

    def _test_cancel_02_sw(self):
        """Try to cancel an invoice with case 02 with Smart Web"""
        self.company.l10n_mx_edi_pac = "sw"
        self.company.l10n_mx_edi_pac_username = "luis_t@vauxoo.com"
        self.company.l10n_mx_edi_pac_password = "VAU.2021.SW"
        invoice = self.invoice
        self._invoice_preparation(invoice)
        invoice.action_post()
        self._process_documents_web_services(invoice, {"cfdi_3_3"})
        self.assertEqual(invoice.edi_state, "sent", invoice.edi_error_message)
        invoice.l10n_mx_edi_cancellation = "02"
        invoice.button_cancel_posted_moves()
        self._process_documents_web_services(invoice, {"cfdi_3_3"})
        self.assertEqual(invoice.edi_state, "cancelled", invoice.edi_error_message)

    def test_cancel_in_draft(self):
        """Ensure that draft invoice is cancelled correctly"""
        invoice = self.invoice
        invoice.button_cancel()
        self.assertEqual(invoice.state, "cancel", invoice.message_ids.mapped("body"))

    def test_invoice_reversal(self):
        """Ensure that draft invoice is cancelled correctly"""
        date_mx = self.env["l10n_mx_edi.certificate"].sudo().get_mx_current_datetime()
        invoice = self.invoice
        self._invoice_preparation(invoice)
        invoice.invoice_date = date_mx - timedelta(days=1)
        invoice.action_post()
        generated_files = self._process_documents_web_services(invoice, {"cfdi_3_3"})
        self.assertTrue(generated_files, invoice.edi_error_message)
        self.assertEqual(invoice.edi_state, "sent", invoice.edi_error_message)

        invoice.l10n_mx_edi_cancellation = "03"
        with self.assertRaisesRegex(
            UserError, "This option only could be used if the accounting closing dates are defined."
        ):
            invoice.button_cancel_with_reversal()

        self._clear_entries()
        invoice.company_id.fiscalyear_lock_date = invoice.invoice_date
        invoice.button_cancel_with_reversal()
        self.assertTrue(invoice.reversal_move_id, invoice.message_ids.mapped("body"))

    def test_cancel_03(self):
        """Try to cancel an invoice with case 03"""
        invoice = self.invoice
        self._invoice_preparation(invoice)
        invoice.action_post()
        generated_files = self._process_documents_web_services(invoice, {"cfdi_3_3"})
        self.assertTrue(generated_files, invoice.edi_error_message)
        self.assertEqual(invoice.edi_state, "sent", invoice.edi_error_message)
        invoice.l10n_mx_edi_cancellation = "03"
        invoice.button_cancel_posted_moves()
        self._process_documents_web_services(invoice, {"cfdi_3_3"})
        self.assertTrue(invoice.edi_state in ("cancelled", "to_cancel"), invoice.edi_error_message)

    def test_cancel_04(self):
        """Try to cancel an invoice out of period"""
        date_mx = self.env["l10n_mx_edi.certificate"].sudo().get_mx_current_datetime()
        invoice = self.invoice
        self._invoice_preparation(invoice)
        invoice.invoice_date = date_mx - timedelta(days=2)
        invoice.action_post()
        generated_files = self._process_documents_web_services(invoice, {"cfdi_3_3"})
        self.assertTrue(generated_files, invoice.edi_error_message)
        self.assertEqual(invoice.edi_state, "sent", invoice.edi_error_message)
        invoice.l10n_mx_edi_cancellation = "03"
        self._clear_entries()
        invoice.company_id.fiscalyear_lock_date = date_mx - timedelta(days=1)
        # To this case, simulate that is a production instance
        self.company.l10n_mx_edi_pac_username = "luis_t@vauxoo.com"
        self.company.l10n_mx_edi_pac_password = "VAU.2021.SW"
        self.l10n_mx_edi_pac_test_env = False
        invoice.button_cancel_with_reversal()
        self.assertTrue(invoice.reversal_move_id, invoice.message_ids.mapped("body"))
        self._process_documents_web_services(invoice, {"cfdi_3_3"})
        self.l10n_mx_edi_pac_test_env = True
        self._process_documents_web_services(invoice, {"cfdi_3_3"})
        self.assertEqual(invoice.edi_state, "cancelled", invoice.edi_error_message)

    def test_cancel_vendor_bill(self):
        """Try to cancel a vendor bill out of period"""
        date_mx = self.env["l10n_mx_edi.certificate"].sudo().get_mx_current_datetime()
        invoice = self.invoice.create(
            {
                "partner_id": self.invoice.partner_id.id,
                "move_type": "in_invoice",
                "invoice_date": date_mx - timedelta(days=2),
                "invoice_line_ids": [
                    Command.create(
                        {
                            "product_id": self.invoice.invoice_line_ids[0].product_id.id,
                            "account_id": (
                                self.invoice.invoice_line_ids[0]
                                .product_id.product_tmpl_id.get_product_accounts()
                                .get("income")
                                .id
                            ),
                            "quantity": 1,
                            "price_unit": 100,
                            "name": "Product Test",
                        },
                    )
                ],
            }
        )
        invoice.action_post()
        self._clear_entries()
        invoice.company_id.fiscalyear_lock_date = date_mx - timedelta(days=1)
        invoice.button_cancel_with_reversal()
        self.assertTrue(invoice.reversal_move_id, invoice.message_ids.mapped("body"))

    def _clear_entries(self):
        self.invoice.search([("state", "=", "draft")]).unlink()
        self.env["account.bank.statement.line"].search(
            [
                ("is_reconciled", "=", False),
                ("move_id.state", "in", ("draft", "posted")),
            ]
        ).unlink()
