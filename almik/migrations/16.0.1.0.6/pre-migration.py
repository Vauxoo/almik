import logging

from odoo import tools

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    rename_fields(cr)


def rename_fields(cr):
    """Name of the Odoo studio field is modified, it is required modifying it in the model"""
    columns_to_rename = [
        ("purchase_order", "x_studio_direccion_de_entrega", "ship_to"),
    ]
    for table_name, old_column, new_column in columns_to_rename:
        if tools.column_exists(cr, table_name, old_column):
            _logger.info("Table `%s`: renaming column `%s` -> `%s`", table_name, old_column, new_column)
            tools.rename_column(cr, table_name, old_column, new_column)
