import logging

from psycopg2.extensions import AsIs

from odoo import tools

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    rename_tables(cr)
    rename_fields(cr)
    rename_selection_options_in_serie(cr)
    rename_selection_options_in_relation(cr)


def rename_tables(cr):
    """Rename table names so they match good practices and guidelines"""
    tables_to_rename = [
        ("x_product_product_uom_uom_rel", "product_uom_rel"),
    ]
    for old_name, new_name in tables_to_rename:
        if tools.table_exists(cr, old_name):
            _logger.info("Table `%s`: renaming to `%s`", old_name, new_name)
            cr.execute(
                """
                ALTER TABLE
                    %s
                RENAME TO
                    %s
                """,
                (AsIs(old_name), AsIs(new_name)),
            )


def rename_fields(cr):
    """Rename field names so they match good practices and guidelines"""
    columns_to_rename = [
        ("account_move", "x_studio_serie", "serie"),
        ("res_partner", "x_studio_num_pedimento_mes", "customs_number_month"),
        ("product_uom_rel", "product_product_id", "product_id"),
        ("product_uom_rel", "uom_uom_id", "uom_id"),
        ("uom_uom", "x_studio_factor_conversion", "factor_conversion"),
        ("uom_uom", "x_studio_relacion", "relation"),
    ]
    for table_name, old_column, new_column in columns_to_rename:
        if tools.column_exists(cr, table_name, old_column):
            _logger.info("Table `%s`: renaming column `%s` -> `%s`", table_name, old_column, new_column)
            tools.rename_column(cr, table_name, old_column, new_column)


def rename_selection_options_in_serie(cr):
    """The options of the field serie were modified to follow guidelines and improve performance"""
    cr.execute(
        """
        UPDATE
            account_move
        SET
            serie = LOWER(
                REPLACE(
                    REPLACE(
                        serie,
                        'DOCUMENTO CANCELADO',
                        'cancelled'
                    ),
                    ' ',
                    '_'
                )
            )
        WHERE
            serie IS NOT NULL
        """
    )
    _logger.info("%s records from account_move were updated in the serie field successfully!", cr.rowcount)


def rename_selection_options_in_relation(cr):
    """The options of the field relation were modified to follow guidelines and improve performance"""
    cr.execute(
        """
        UPDATE
            uom_uom
        SET
            relation = LOWER(
                REPLACE(
                    REPLACE(
                        REPLACE(
                            REPLACE(
                                REPLACE(
                                    REPLACE(
                                        REPLACE(
                                            REPLACE(
                                                REPLACE(
                                                    relation,
                                                    'Rollo',
                                                    'roll'
                                                ),
                                                'Paquete',
                                                'pack'
                                            ),
                                            'Metro',
                                            'mt'
                                        ),
                                        'Pieza',
                                        'pcs'
                                    ),
                                    'Tonelada',
                                    'ton'
                                ),
                                'Caja',
                                'box'
                            ),
                            'Pies',
                            'ft'
                        ),
                        'Sin Conversion',
                        'no'
                    ),
                    ' / ',
                    '_'
                )
            )
        WHERE
            relation IS NOT NULL
        """
    )
    _logger.info("%s records from uom_uom were updated in the relation field successfully!", cr.rowcount)
