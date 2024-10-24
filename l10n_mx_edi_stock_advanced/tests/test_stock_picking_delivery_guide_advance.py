import unittest

from lxml import objectify

from odoo.tests import tagged

from odoo.addons.l10n_mx_edi_stock_extended_31.tests.common import (
    TestMXDeliveryGuideCommon,
)


@tagged("post_install", "-at_install")
class TestMXDeliveryGuideAdvanced(TestMXDeliveryGuideCommon):
    def setUp(self):
        super().setUp()
        self.vehicle_pedro.write(
            {
                "environmental_insurer": "DEMO INSURER",
                "environmental_insurance_policy": "DEMO POLICY 2",
            }
        )
        self.picking = self.create_picking()
        self.picking.l10n_mx_edi_gross_vehicle_weight = 2.0

    @unittest.skip("Module deprecated")
    def test_001_generate_delivery_guide_could_dangerous(self):
        """Test the case: the product sat code is marked as could be dangerous, and it is actually dangerous"""
        # The product code 01010101. It is 01, in other words. Could be dangerous
        # with l10n_mx_edi_dangerous_sat_id it is consider as dangerous
        # The packing code should be provide
        self.productA.write(
            {
                "unspsc_code_id": self.env.ref("product_unspsc.unspsc_code_01010101").id,
                "l10n_mx_edi_dangerous_sat_id": self.env.ref(
                    "l10n_mx_edi_stock_advanced.prod_dangerous_code_sat_0004"
                ).id,
                "l10n_mx_edi_packaging_sat_id": self.env.ref(
                    "l10n_mx_edi_stock_advanced.prod_packaging_code_sat_1A2"
                ).id,
            }
        )

        self.picking.l10n_mx_edi_action_send_delivery_guide()
        self.assertEqual(self.picking.l10n_mx_edi_status, "sent", self.picking.l10n_mx_edi_error)
        # Check that the attributes are what expected
        cfdi = objectify.fromstring(self.picking.l10n_mx_edi_cfdi_file_id.raw)
        self.assertTrue(hasattr(cfdi, "Complemento"), "There is not a complement node in the cfdi")
        attribute = "//cartaporte31:CartaPorte"
        namespace = {"cartaporte31": "http://www.sat.gob.mx/cartaporte31"}
        carta_porte_node = cfdi.Complemento.xpath(attribute, namespaces=namespace)
        self.assertTrue(carta_porte_node, "There is not a cartaporte node.")
        carta_porte_node = carta_porte_node[0]
        node = carta_porte_node.Mercancias.Mercancia
        self.assertEqual(node.attrib["MaterialPeligroso"], "Sí", "This case should be marked as dangerous material")
        self.assertEqual(
            node.attrib["CveMaterialPeligroso"],
            self.productA.l10n_mx_edi_dangerous_sat_id.code,
            "This case should be marked with the dangerous type code",
        )
        self.assertEqual(
            node.attrib["Embalaje"],
            self.productA.l10n_mx_edi_packaging_sat_id.code,
            "This case should be marked with the dangerous type code",
        )

    @unittest.skip("Module deprecated")
    def test_002_generate_delivery_guide_could_dangerous_case_b(self):
        """Test the case: the product sat code is marked as could be dangerous but it is not dangerous"""
        # The product code 01010101. It is 01, in other words. Could be dangerous
        # l10n_mx_edi_dangerous_sat_id should be not set to be considered as not dangerous
        # The packing code should be provide
        self.productA.write(
            {
                "unspsc_code_id": self.env.ref("product_unspsc.unspsc_code_01010101").id,
                "l10n_mx_edi_dangerous_sat_id": False,
                "l10n_mx_edi_packaging_sat_id": False,
            }
        )
        self.picking.l10n_mx_edi_action_send_delivery_guide()
        self.assertEqual(self.picking.l10n_mx_edi_status, "sent", self.picking.l10n_mx_edi_error)

        # Check that the attributes are what expected
        cfdi = objectify.fromstring(self.picking.l10n_mx_edi_cfdi_file_id.raw)
        self.assertTrue(hasattr(cfdi, "Complemento"), "There is not a complement node in the cfdi")
        attribute = "//cartaporte31:CartaPorte"
        namespace = {"cartaporte31": "http://www.sat.gob.mx/cartaporte31"}
        carta_porte_node = cfdi.Complemento.xpath(attribute, namespaces=namespace)
        self.assertTrue(carta_porte_node, "There is not a cartaporte node.")
        carta_porte_node = carta_porte_node[0]
        node = carta_porte_node.Mercancias.Mercancia
        self.assertEqual(
            node.attrib["MaterialPeligroso"], "No", "This case should be marked as Not dangerous material"
        )
        # CveMaterialPeligroso and Embalaje must not be attributes
        self.assertFalse(
            node.get("CveMaterialPeligroso", node.get("Embalaje")),
            "Any CveMaterialPeligroso or Embalaje are present in the cfdi, in this case they should not",
        )

    @unittest.skip("Module deprecated")
    def test_003_generate_delivery_guide_dangerous(self):
        """Test the case: the product sat code is marked as dangerous"""
        # The product code 01010101. It is 1, in other words, dangerous
        # The dangerous and packing codes should be provided
        self.productA.write(
            {
                "unspsc_code_id": self.env.ref("product_unspsc.unspsc_code_10151608").id,
                "l10n_mx_edi_dangerous_sat_id": self.env.ref(
                    "l10n_mx_edi_stock_advanced.prod_dangerous_code_sat_0004"
                ).id,
                "l10n_mx_edi_packaging_sat_id": self.env.ref(
                    "l10n_mx_edi_stock_advanced.prod_packaging_code_sat_1A2"
                ).id,
            }
        )
        self.picking.l10n_mx_edi_action_send_delivery_guide()
        self.assertEqual(self.picking.l10n_mx_edi_status, "sent", self.picking.l10n_mx_edi_error)

        # Check that the attributes are what expected
        cfdi = objectify.fromstring(self.picking.l10n_mx_edi_cfdi_file_id.raw)
        self.assertTrue(hasattr(cfdi, "Complemento"), "There is not a complement node in the cfdi")
        attribute = "//cartaporte31:CartaPorte"
        namespace = {"cartaporte31": "http://www.sat.gob.mx/cartaporte31"}
        carta_porte_node = cfdi.Complemento.xpath(attribute, namespaces=namespace)
        self.assertTrue(carta_porte_node, "There is not a cartaporte node.")
        carta_porte_node = carta_porte_node[0]
        node = carta_porte_node.Mercancias.Mercancia
        self.assertEqual(node.attrib["MaterialPeligroso"], "Sí", "This case should be marked as dangerous material")
        self.assertEqual(
            node.attrib["CveMaterialPeligroso"],
            self.productA.l10n_mx_edi_dangerous_sat_id.code,
            "This case should be marked with the dangerous type code",
        )
        self.assertEqual(
            node.attrib["Embalaje"],
            self.productA.l10n_mx_edi_packaging_sat_id.code,
            "This case should be marked with the dangerous type code",
        )

    @unittest.skip("Module deprecated")
    def test_004_generate_delivery_guide_dangerous(self):
        """Test the case: the product sat code is marked as not dangerous"""
        # The product code 01010101. It is 01, in other words. Could be dangerous
        # with l10n_mx_edi_dangerous_sat_id it is consider as dangerous
        # The packing code should be provide
        self.productA.write(
            {
                "unspsc_code_id": self.env.ref("product_unspsc.unspsc_code_10101500").id,
                "l10n_mx_edi_dangerous_sat_id": self.env.ref(
                    "l10n_mx_edi_stock_advanced.prod_dangerous_code_sat_0004"
                ).id,
                "l10n_mx_edi_packaging_sat_id": self.env.ref(
                    "l10n_mx_edi_stock_advanced.prod_packaging_code_sat_1A2"
                ).id,
            }
        )
        self.picking.l10n_mx_edi_action_send_delivery_guide()
        self.assertEqual(self.picking.l10n_mx_edi_status, "sent", self.picking.l10n_mx_edi_error)

        # Check that the attributes are what expected
        cfdi = objectify.fromstring(self.picking.l10n_mx_edi_cfdi_file_id.raw)
        self.assertTrue(hasattr(cfdi, "Complemento"), "There is not a complement node in the cfdi")
        attribute = "//cartaporte31:CartaPorte"
        namespace = {"cartaporte31": "http://www.sat.gob.mx/cartaporte31"}
        carta_porte_node = cfdi.Complemento.xpath(attribute, namespaces=namespace)
        self.assertTrue(carta_porte_node, "There is not a cartaporte node.")
        carta_porte_node = carta_porte_node[0]
        node = carta_porte_node.Mercancias.Mercancia
        # MaterialPeligroso, CveMaterialPeligroso and Embalaje can not be attributes
        self.assertFalse(
            node.get("MaterialPeligroso", node.get("CveMaterialPeligroso", node.get("Embalaje"))),
            "MaterialPeligroso, CveMaterialPeligroso, Embalaje any of them are present on the cfdi, "
            "in this case any of them can not be attributes",
        )
