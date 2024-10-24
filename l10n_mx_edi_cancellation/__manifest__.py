# Copyright 2018 Vauxoo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "EDI Cancellation for Mexican Localization (Complement)",
    "summary": """
    Allows to add new features to the EDI Cancellation process.
    """,
    "author": "Vauxoo",
    "website": "http://www.vauxoo.com",
    "license": "LGPL-3",
    "category": "Hidden",
    "version": "16.0.1.0.2",
    "depends": [
        "l10n_mx_edi",
    ],
    "data": [
        "security/res_groups.xml",
        "views/account_move_view.xml",
        "views/account_payment_view.xml",
        "views/res_config_settings_view.xml",
    ],
    "demo": [],
    "installable": True,
    "auto_install": False,
}
