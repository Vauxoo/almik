# Copyright 2022 Vauxoo

from os.path import dirname, join, realpath


def _load_product_is_dangerous(cr, registry):
    """Import CSV data as it is faster than xml and because we can't use
    noupdate anymore with csv"""
    csv_path = join(dirname(realpath(__file__)), "data", "l10n.mx.edi.product.dangerous.csv")
    with open(csv_path) as csv_file:
        lines = csv_file.readlines()
    for line in lines:
        code, dangerous = line.replace("\n", "").split(",")
        cr.execute(
            """UPDATE product_unspsc_code
            set l10n_mx_edi_dangerous_material=%s
            WHERE code=%s""",
            (dangerous, code),
        )


def _load_product_dangerous(cr, registry):
    """Import CSV data as it is faster than xml and because we can't use
    noupdate anymore with csv"""
    csv_path = join(dirname(realpath(__file__)), "data", "l10n.mx.edi.product.dangerous.sat.code.csv")
    with open(csv_path) as csv_file:
        cr.copy_expert(
            """COPY l10n_mx_edi_product_dangerous_sat_code(code, name, class_div, active)
            FROM STDIN WITH DELIMITER '|' CSV HEADER""",
            csv_file,
        )
    # Create xml_id, to allow make reference to this data
    cr.execute(
        """INSERT INTO ir_model_data
           (name, res_id, module, model, noupdate)
           SELECT concat('prod_dangerous_code_sat_', code), id, 'l10n_mx_edi_stock_advanced',
            'l10n_mx_edi.product.dangerous.sat.code', true
           FROM l10n_mx_edi_product_dangerous_sat_code """
    )


def _load_product_packing(cr, registry):
    """Import CSV data as it is faster than xml and because we can't use
    noupdate anymore with csv"""
    csv_path = join(dirname(realpath(__file__)), "data", "l10n.mx.edi.product.packaging.sat.code.csv")
    with open(csv_path) as csv_file:
        cr.copy_expert(
            """COPY l10n_mx_edi_product_packaging_sat_code(code, name, active)
            FROM STDIN WITH DELIMITER '|' CSV HEADER""",
            csv_file,
        )
    # Create xml_id, to allow make reference to this data
    cr.execute(
        """INSERT INTO ir_model_data
           (name, res_id, module, model, noupdate)
           SELECT concat('prod_packaging_code_sat_', code), id, 'l10n_mx_edi_stock_advanced',
            'l10n_mx_edi.product.packaging.sat.code', true
           FROM l10n_mx_edi_product_packaging_sat_code """
    )


def post_init_hook(cr, registry):
    _load_product_is_dangerous(cr, registry)
    _load_product_dangerous(cr, registry)
    _load_product_packing(cr, registry)


def uninstall_hook(cr, registry):
    cr.execute("""UPDATE product_template SET l10n_mx_edi_dangerous_sat_id=NULL;""")
    cr.execute("""UPDATE product_template SET l10n_mx_edi_packaging_sat_id=NULL;""")
    cr.execute("""UPDATE product_product SET l10n_mx_edi_dangerous_sat_id=NULL;""")
    cr.execute("""UPDATE product_product SET l10n_mx_edi_packaging_sat_id=NULL;""")
    cr.execute("DELETE FROM l10n_mx_edi_product_dangerous_sat_code;")
    cr.execute("DELETE FROM l10n_mx_edi_product_packaging_sat_code;")
    cr.execute("DELETE FROM ir_model_data WHERE module='l10n_mx_edi_stock_advanced';")
