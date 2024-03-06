# -*- coding: utf-8 -*-
{
    'name': "Almik Dev",

    'summary': """
        Almik Dev """,

    'description': """
        Almik Dev 
    """,

    'author': "Almik",


    # any module necessary for this one to work correctly
    'depends': ['base','account'],

    # always loaded
    'data': [        
        'data/cron_rate_exchange.xml',
        # 'data/email_template.xml',
        'views/account_bank_statement.xml',
        'views/account_move.xml',
        'views/res_currency.xml',
    ],
}
