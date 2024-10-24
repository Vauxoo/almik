from os.path import join

from lxml.objectify import fromstring

from odoo import tools
from odoo.tests import tagged

from odoo.addons.l10n_mx_edi_40.tests.common import TestMxEdiCommon


@tagged("sanmina", "post_install", "-at_install")
class TestAddendaSanmina(TestMxEdiCommon):
    def test_addenda_sanmina(self):
        self.certificate._check_credentials()
        invoice = self.invoice
        invoice.currency_id = self.env.ref("base.MXN")
        invoice.invoice_date = False
        invoice.invoice_line_ids.product_uom_id = invoice.invoice_line_ids.product_id.uom_id
        invoice.l10n_mx_edi_usage = "S01"

        isr = self.env["account.account.tag"].search([("name", "=", "ISR")])
        iva = self.env["account.account.tag"].search([("name", "=", "IVA")])
        invoice.invoice_line_ids.tax_ids.filtered(lambda t: t.amount <= 0).invoice_repartition_line_ids.tag_ids |= isr
        invoice.invoice_line_ids.tax_ids.filtered(lambda t: t.amount > 0).invoice_repartition_line_ids.tag_ids |= iva

        invoice.partner_id.l10n_mx_edi_addenda = self.env.ref("addenda_sanmina.sanmina")
        invoice.ref = "5644544"
        invoice.currency_id = self.env.ref("base.MXN")
        invoice.action_post()
        generated_files = self._process_documents_web_services(self.invoice, {"cfdi_3_3"})
        self.assertTrue(generated_files, invoice.edi_error_message)
        # Check addenda has been appended and it's equal to the expected one
        xml = fromstring(generated_files[0])
        self.assertTrue(hasattr(xml, "Addenda"), "There is no Addenda node")

        # Since we didn't set any addenda value, the operational organization
        # won't be set, so it needs to be set on the generated XML
        xml_path = join("addenda_sanmina", "tests", "expected.xml")
        with tools.file_open(xml_path, "rb") as xml_file:
            addenda = xml_file.read()
        addenda = addenda.replace(b"--folio--", invoice.name.encode())
        expected_addenda = fromstring(addenda)
        self.assertXmlTreeEqual(xml.Addenda, expected_addenda)
