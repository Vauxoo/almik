import logging

from odoo import tools

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    rename_field(cr)


def rename_field(cr):
    """Rename fiscal legend field created in odoo studio to its implementation in code"""
    columns_to_rename = [
        ("res_partner", "x_studio_leyenda_fiscal", "fiscal_legend"),
    ]
    for table_name, old_column, new_column in columns_to_rename:
        if tools.column_exists(cr, table_name, old_column):
            _logger.info("Table `%s`: renaming column `%s` -> `%s`", table_name, old_column, new_column)
            tools.rename_column(cr, table_name, old_column, new_column)
