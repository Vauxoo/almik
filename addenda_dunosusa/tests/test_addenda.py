from os.path import join

from lxml.objectify import fromstring

from odoo import tools
from odoo.fields import Command
from odoo.tests import tagged

from odoo.addons.l10n_mx_edi_40.tests.common import TestMxEdiCommon


@tagged("post_install", "-at_install")
class TestAddendaDunosusa(TestMxEdiCommon):
    def test_addenda_dunosusa(self):
        self.certificate._check_credentials()
        isr = self.env["account.account.tag"].search([("name", "=", "ISR")])
        iva = self.env["account.account.tag"].search([("name", "=", "IVA")])
        self.invoice.invoice_line_ids.tax_ids.filtered(
            lambda t: t.amount <= 0
        ).invoice_repartition_line_ids.tag_ids |= isr
        self.invoice.invoice_line_ids.tax_ids.filtered(
            lambda t: t.amount > 0
        ).invoice_repartition_line_ids.tag_ids |= iva

        self.env["base.language.install"].create(
            {"lang_ids": [Command.set([self.env.ref("base.lang_es").id])], "overwrite": 0}
        ).lang_install()
        self.today = self.env["l10n_mx_edi.certificate"].sudo().get_mx_current_datetime()
        self.partner_a.write(
            {
                "l10n_mx_edi_addenda": self.ref("addenda_dunosusa.dunosusa"),
                "ref": "7505000099632",
                "lang": "es_ES",
            }
        )

        self.product.write(
            {
                "seller_ids": [
                    Command.create({"partner_id": self.partner_a.id}),
                ]
            }
        )

        invoice = self.invoice
        invoice.invoice_date = self.today
        invoice.invoice_payment_term_id = self.env.ref("account.account_payment_term_45days")
        invoice.currency_id = self.env.ref("base.MXN").id
        invoice.line_ids.with_context(dynamic_unlink=True).unlink()
        invoice.invoice_line_ids.unlink()

        taxes = [self.tax_16.id, self.tax_10_negative.id]
        invoice.invoice_line_ids = [
            Command.create(
                {
                    "account_id": self.product.product_tmpl_id.get_product_accounts()["income"].id,
                    "product_id": self.product.id,
                    "move_id": invoice.id,
                    "quantity": 1,
                    "price_unit": 450,
                    "product_uom_id": self.product.uom_id.id,
                    "name": "[PCSC234] Computer SC234 17",
                    "x_addenda_supplier_code": "1234567890",
                    "tax_ids": [Command.set(taxes)],
                },
            )
        ]
        invoice.x_addenda_dunosusa = "DQ|2023-08-04|123456|123"
        invoice.action_post()
        generated_files = self._process_documents_web_services(invoice, {"cfdi_3_3"})
        self.assertTrue(generated_files, invoice.edi_error_message)
        self.assertEqual(invoice.edi_state, "sent", invoice.message_ids.mapped("body"))

        # Check addenda has been appended and it's equal to the expected one
        xml = fromstring(generated_files[0])
        self.assertTrue(hasattr(xml, "Addenda"), "There is no Addenda node")

        xml_path = join("addenda_dunosusa", "tests", "expected.xml")
        with tools.file_open(xml_path, "rb") as xml_file:
            addenda = xml_file.read()
        addenda = addenda.replace(b"--name--", invoice.name.replace("/", "").encode())
        expected_addenda = fromstring(addenda)

        date = xml.Addenda.xpath("//requestForPayment")[0].get("DeliveryDate")
        expected_addenda.xpath("//requestForPayment")[0].attrib["DeliveryDate"] = date
        self.assertXmlTreeEqual(xml.Addenda, expected_addenda)

        # Validate that a supplier info was created for the product
        supplier_info = invoice.invoice_line_ids.product_id.seller_ids
        self.assertTrue(supplier_info, "The product has no supplier info assigned.")
