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
    'depends': ['account'],

    # always loaded
    'data': [
        'views/account_bank_statement.xml',
        'views/account_move.xml',
    ],
}