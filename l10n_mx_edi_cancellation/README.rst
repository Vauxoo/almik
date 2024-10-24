================
EDI Cancellation
================

**This module introduces the following features in the cancellation process:**

.. contents::
      :local:

Enabling the Selection of a Cancellation Case
=============================================

To facilitate the use of the four options provided by the SAT for the cancellation process, a new field has been added
to the invoice and payment models. This field allows users to select the appropriate cancellation case for each
cancellation process.

Invoice Cancellation in Closed Periods
======================================

This module allows the cancellation of invoices issued within a closed accounting period.

**Usage Example**
Let's say you issued an invoice in February. At the end of the month, you close your accounting period.
In March, you realize you need to cancel and re-issue the invoice. This functionality enables you to cancel the invoice
through the SAT, and generate a reversal entry in the current period without affecting the closed period.

**How does it work?**
  1. **Permissions:** A new group called `Enable cancellation with reversed entry` has been added, allowing specific users to use this option.
  2. **Requirements:** The accounting period must be closed to use this functionality.
  3. **Process within the invoice:**

     1. Select the cancellation reason you want to use.
     2. Click the `(Cancel with reversal)` button.

**What happens during cancellation?**
  1. The invoice is sent to the SAT for cancellation.
  2. A credit note (refund) is generated in the system to apply the accounting effect in the current period.

  **Note:** This credit note is not sent to the SAT, as the original invoice has already been canceled by the SAT.

Ensure that the accounting is only affected when the document is cancelled in the SAT
=====================================================================================

The cancel process in Odoo can only be executed when the SAT status is cancelled for cancellation type 02, 03 and 04.

Which is the new flow to cancel?
--------------------------------

A new button `(Request Cancelation)` was added to the invoice view, that
appears when the invoice is open and the `PAC status` is `Signed`

When the new button is pressed, the CFDI is sent to the PAC to try to cancel it
in the SAT system. And does not allow to cancel the invoice in Odoo until it has
been properly canceled by the SAT. (This is an automatic action executed by the system).


On Payments:
You can enable the new setting *Accounting / Configuration / Settings/ Cancellation settings / Enable cancellation with reversal move*

Now, in the same cancellation process, the payments are checked to determine if they are from a previous period or the current period.

If payment is from previous periods you can select the date and journal for this reversal entry
and the cancellation will remove the reconciliation with related documents (such as invoices, etc.)
and create a new reversal entry without tax lines or cash basis lines.
Also if it's required, the cancel process for the related CFDI is called.


Which are the cases supported in this module?
---------------------------------------------

**Case 1**

+----------+---------+
| System   | State   |
+==========+=========+
| Odoo     | Open    |
+----------+---------+
| PAC      | Signed  |
+----------+---------+
| SAT      | Valid   |
+----------+---------+

This case is when the invoice is properly signed in the SAT system. To
cancel is necessary to press the button `Request Cancelation`, that will
to verify that effectively the CFDI is not previously canceled in the SAT
system and will to send it to cancel in the SAT.

After of request the cancellation, could be found the next cases:

*The cancel process was succesful*

+----------+------------+
| System   | State      |
+==========+============+
| Odoo     | Open       |
+----------+------------+
| PAC      | Cancelled  |
+----------+------------+
| SAT      | Valid      |
+----------+------------+

In this case, the system will execute the next actions:

1. An action will to update the PAC status (To Canceled).

2. A method will be called and will try to cancel the invoice in Odoo.


*The cancel process cannot be completed*

+----------+------------+
| System   | State      |
+==========+============+
| Odoo     | Open       |
+----------+------------+
| PAC      | To Cancel  |
+----------+------------+
| SAT      | Valid      |
+----------+------------+

In this case, the system wait for the PAC system, and will execute the next
action:

1. A method will be called to verify if the CFDI was properly cancelled in
the SAT system, and when the SAT status is `Cancelled` will try to cancel the
invoice in Odoo.

**Case 2**

+----------+------------+
| System   | State      |
+==========+============+
| Odoo     | Open       |
+----------+------------+
| PAC      | To Cancel  |
+----------+------------+
| SAT      | Valid      |
+----------+------------+

This case is the same that in the previous case when the cancel process
cannot be completed.

If the customer does not accept the CFDI cancelation, the cancel process
must be aborted and the invoice must be returned to signed. For this, was
added an action in the invoice `Revert CFDI cancellation`, that could be
called in the `Actions` of it.


**Case 3**

+----------+------------+
| System   | State      |
+==========+============+
| Odoo     | Open       |
+----------+------------+
| PAC      | To Cancel  |
+----------+------------+
| SAT      | Cancelled  |
+----------+------------+

The system executes a scheduled action that will cancel the invoice in Odoo,
and in that process, the PAC status must be updated to `Cancelled`.


**Case 4**

+----------+------------+
| System   | State      |
+==========+============+
| Odoo     | Cancel     |
+----------+------------+
| PAC      | Signed     |
+----------+------------+
| SAT      | Valid      |
+----------+------------+

The system executes a scheduled action that will check that the SAT status
continues `Valid` and if yes, the invoice must be returned to `Open`
(Without generate a new CFDI). For this:

1. If the invoice does not has a journal entry, a new will be generated and
the invoice state must be changed to `Open`.

2. If the journal entry in the invoice has a revert, it will be cancelled
and the invoice state must be changed to `Open`.

**Case 5**

+----------+------------+
| System   | State      |
+==========+============+
| Odoo     | Cancel     |
+----------+------------+
| PAC      | To Cancel  |
+----------+------------+
| SAT      | Valid      |
+----------+------------+

This is the same case that in the previous one, but after that the
invoice is open again, the PAC status must be updated to 'Signed.'

show video: https://drive.google.com/file/d/1OmKCdoY9Xq3GHDx8Htwrwepk_O-ufaj9/view?usp=drive_link

Bug Tracker
===========

Bugs are tracked on
`GitLab Issues <https://git.vauxoo.com/Vauxoo/mexico/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and
welcomed feedback.

Credits
=======

**Contributors**

* Nhomar Hernandez <nhomar@vauxoo.com> (Designer)
* Luis Torres <luis_t@vauxoo.com> (Developer)

Maintainer
==========

.. image:: https://s3.amazonaws.com/s3.vauxoo.com/description_logo.png
   :alt: Vauxoo
   :target: https://vauxoo.com
