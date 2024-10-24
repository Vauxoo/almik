# Copyright 2020 Vauxoo
# License OPL-1 (https://www.odoo.com/documentation/16.0/legal/licenses.html#odoo-apps).
{
    "name": "Addenda Envases",
    "summary": """
    Addenda for Envases Universales de México
    """,
    "author": "Vauxoo",
    "website": "https://www.vauxoo.com",
    "license": "OPL-1",
    "category": "Installer",
    "version": "16.0.1.0.3",
    "depends": [
        "l10n_mx_edi",
    ],
    "test": [],
    "data": [
        "data/addenda.xml",
        "views/account_move.xml",
        "security/ir.model.access.csv",
    ],
    "demo": [],
    "installable": True,
    "auto_install": False,
}
