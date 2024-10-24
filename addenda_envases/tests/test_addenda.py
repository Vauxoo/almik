# See LICENSE file for full copyright and licensing details.

from os.path import join

from lxml.objectify import fromstring

from odoo import tools
from odoo.tests import Form, tagged

from odoo.addons.l10n_mx_edi_40.tests.common import TestMxEdiCommon


@tagged("post_install", "-at_install")
class TestAddendaEnvases(TestMxEdiCommon):
    def test_addenda_envases(self):
        self.certificate._check_credentials()
        self.namespaces = {"eu": "http://factura.envasesuniversales.com/addenda/eu"}
        invoice = self.invoice
        invoice.currency_id = self.env.ref("base.MXN")
        invoice.invoice_date = False

        isr = self.env["account.account.tag"].search([("name", "=", "ISR")])
        iva = self.env["account.account.tag"].search([("name", "=", "IVA")])
        invoice.invoice_line_ids.tax_ids.filtered(lambda t: t.amount <= 0).invoice_repartition_line_ids.tag_ids |= isr
        invoice.invoice_line_ids.tax_ids.filtered(lambda t: t.amount > 0).invoice_repartition_line_ids.tag_ids |= iva

        invoice.partner_id.l10n_mx_edi_addenda = self.env.ref("addenda_envases.envases")
        invoice.ref = "PO456"
        invoice.currency_id = self.env.ref("base.MXN")
        wizard = self.env["x_addenda.envases"].create(
            {
                "x_incoming_code": "12345",
            }
        )
        set_addenda_action = self.env.ref("addenda_envases.set_addenda_envases_values")
        context = {
            "active_id": wizard.id,
            "invoice_id": invoice.id,
        }
        set_addenda_action.with_context(**context).run()

        # without the context it would say that you cannot unlink records that
        # affect the tax report
        invoice.line_ids.with_context(dynamic_unlink=True).unlink()
        invoice.invoice_line_ids.unlink()

        move_form = Form(invoice)
        with move_form.invoice_line_ids.new() as line_form:
            line_form.name = self.product.name
            line_form.quantity = 1
            line_form.account_id = self.product.product_tmpl_id.get_product_accounts()["income"]
            line_form.product_id = self.product
            line_form.product_uom_id = self.product.uom_id

        with move_form.invoice_line_ids.edit(0) as line_form:
            line_form.price_unit = 450
            line_form.tax_ids.clear()
            line_form.tax_ids.add(self.tax_16)
            line_form.tax_ids.add(self.tax_10_negative)
        move_form.save()
        invoice.action_post()
        generated_files = self._process_documents_web_services(invoice, {"cfdi_3_3"})
        self.assertTrue(generated_files, invoice.edi_error_message)
        self.assertEqual(invoice.edi_state, "sent", invoice.message_ids.mapped("body"))

        # Check addenda has been appended and it's equal to the expected one
        xml = fromstring(generated_files[0])
        self.assertTrue(hasattr(xml, "Addenda"), "There is no Addenda node")

        xml_path = join("addenda_envases", "tests", "expected.xml")
        with tools.file_open(xml_path, "rb") as xml_file:
            addenda = xml_file.read()
        addenda = addenda.replace(b"--date--", str(invoice.invoice_date).encode()).replace(
            b"--folio--",
            self.env["account.edi.format"]._l10n_mx_edi_get_serie_and_folio(invoice)["folio_number"].encode(),
        )
        expected_addenda = fromstring(addenda)

        self.assertXmlTreeEqual(xml.Addenda, expected_addenda)
