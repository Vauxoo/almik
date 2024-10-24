# Copyright 2020 Vauxoo
# License OPL-1 (https://www.odoo.com/documentation/16.0/legal/licenses.html#odoo-apps).
{
    "name": "Addenda dunosusa",
    "summary": """
    Addenda for dunosusa
    """,
    "author": "Vauxoo",
    "website": "https://www.vauxoo.com",
    "license": "OPL-1",
    "category": "Installer",
    "version": "16.0.1.0.2",
    "depends": [
        "base_address_extended",
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
