import logging

from odoo.addons.l10n_mx_edi_stock_advanced.hooks import _load_product_is_dangerous

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    _load_product_is_dangerous(cr=cr, registry=None)
