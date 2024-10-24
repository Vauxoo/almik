import logging

from odoo import tools

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    rename_fields(cr)


def rename_fields(cr):
    """Rename field names so they match good practices and guidelines"""
    columns_to_rename = [
        ("sale_order", "x_studio_cliente_numero", "customer_number"),
    ]
    for table_name, old_column, new_column in columns_to_rename:
        if tools.column_exists(cr, table_name, old_column):
            _logger.info("Table `%s`: renaming column `%s` -> `%s`", table_name, old_column, new_column)
            tools.rename_column(cr, table_name, old_column, new_column)
