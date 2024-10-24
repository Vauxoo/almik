import logging

from odoo import tools

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    rename_field(cr)


def rename_field(cr):
    """Rename field related to the plant to the new required name in the model"""
    columns_to_rename = [
        ("sale_order", "x_studio_planta", "observations"),
    ]
    for table_name, old_column, new_column in columns_to_rename:
        if tools.column_exists(cr, table_name, old_column):
            _logger.info("Table `%s`: renaming column `%s` -> `%s`", table_name, old_column, new_column)
            tools.rename_column(cr, table_name, old_column, new_column)
