# Copyright 2022 Vauxoo
{
    "name": """Mexico - Electronic Delivery Note Advanced""",
    "version": "16.0.1.0.1",
    "category": "Accounting/Localizations/EDI",
    "author": "Vauxoo",
    "depends": [
        "l10n_mx_edi_stock_extended_40",
    ],
    "demo": [
        "demo/vehicle.xml",
    ],
    "data": [
        "security/ir.model.access.csv",
    ],
    "post_init_hook": "post_init_hook",
    "uninstall_hook": "uninstall_hook",
    "installable": True,
    "auto_install": False,
    "application": False,
    "license": "OEEL-1",
}
