{
    "name": "Default partner values (Mexican localization)",
    "summary": """
    This module adds the Usage and Payment Way fields to the partner,
    whose values will be used by default in the invoices, payments, and bank statements.
    """,
    "version": "16.0.1.0.1",
    "author": "Vauxoo",
    "website": "http://www.vauxoo.com",
    "category": "Accounting",
    "license": "OPL-1",
    "depends": [
        "l10n_mx_edi",
    ],
    "data": [
        "views/res_partner_views.xml",
    ],
}
