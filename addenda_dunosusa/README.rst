Addenda Dunosusa (Del Panadero)
===============================

This addenda require to configure some additional values in the Client:

- **Internal Reference**: this is the 'Internal Reference' field found in the
  'Sales & Purchase' tag of the client's record. Here you will set the GLN of
  the client.

- **Notes**: this is the 'Notes' field found in the 'Shipping Address' of the
  client. Here you will set the GLN of the shipping address, if this field is
  not set the GLN for the shipping address in the addenda will be the same as
  the client itself.

Now, the addenda requires to fill this fields:

- **Additional Reference Code**: this is the attribute to specify the code of
  Additional references and the possible values are:

  - *AAE*: Property account
  - *CK*: Check number
  - *ACE*: Document number (Referral)
  - *ATZ*: Approval number.
  - *AWR*: Number of document that is replaced
  - *ON*: Order number (buyer)
  - *DQ*: Merchandise receipt sheet

- **Additional Reference Number**: this is to express the additional reference
  number and it is related to the selection of the previous field.

- **Date Purchase Order**: this is the date of the purchase order.

- **Order Number**: this is the number of the purchase order.

- **Lines**: these are the products from the invoice line with theirs supplier
  code. You can set the product's supplier code from here or from the Providers
  in the 'Purchase' tag in the product configuration. This is the product GLN
  code.

Technical:
==========

To install this module go to ``Apps`` search ``addenda_dunosusa`` and click
in button ``Install``.

Contributors
------------

* Luis Torres <luis_t@vauxoo.com>

Maintainer
----------

.. figure:: https://www.vauxoo.com/logo.png
   :alt: Vauxoo
   :target: https://vauxoo.com

This module is maintained by Vauxoo.

a latinamerican company that provides training, coaching,
development and implementation of enterprise management
sytems and bases its entire operation strategy in the use
of Open Source Software and its main product is odoo.

To contribute to this module, please visit http://www.vauxoo.com.
