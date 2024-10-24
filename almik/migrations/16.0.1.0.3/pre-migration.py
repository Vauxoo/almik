import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    update_external_ids(cr)


def update_external_ids(cr):
    ids_to_update = {
        "__export__.res_groups_111_de6def0b": "almik.group_delete_initiatives_opportunity",
        "__export__.res_groups_120_90867a0a": "almik.group_allows_internal_transfer",
        "__export__.res_groups_121_cb511b27": "almik.group_view_inventory_adjustment",
        "__export__.res_groups_61_c1859343": "almik.group_salesperson_sales_report",
        "__export__.res_groups_62_958aadd5": "almik.group_inventory_readonly",
        "__export__.res_groups_63_a0e5fa58": "almik.group_users_sales_report",
        "__export__.res_groups_64_1f6e0d68": "almik.group_purchase_purchase_coordinator",
        "__export__.res_groups_65_b2481d1e": "almik.group_purchase_readonly",
        "__export__.res_groups_66_67b5aee8": "almik.group_invoicing",
        "__export__.res_groups_67_fbbcf4b8": "almik.group_sales_invoice",
        "__export__.res_groups_68_ce2e1477": "almik.group_sales_user",
        "__export__.res_groups_69_e097991d": "almik.group_manufacturing_coordinator",
        "__export__.res_groups_70_50ed07e9": "almik.group_manufacturing_user",
        "__export__.res_groups_71_ef1039ef": "almik.group_inventory_coordinator",
        "__export__.res_groups_72_12b9bc18": "almik.group_inventory_purchase_coordinator",
        "__export__.res_groups_73_9592f33b": "almik.group_inventory_qro_user",
        "__export__.res_groups_74_5d7752fa": "almik.group_inventory_manager",
        "__export__.res_groups_75_1c2a78ec": "almik.group_inventory_user",
        "__export__.res_groups_76_adc51198": "almik.group_inventory_branch_user",
        "__export__.res_groups_77_15aa4027": "almik.group_inventory_supervisor",
        "__export__.res_groups_78_4f3b7d5a": "almik.group_sales_supervisor",
        "__export__.res_groups_81_5e6dd9ec": "almik.group_inventory_adjustment",
        "__export__.res_groups_82_0c924161": "almik.group_contact_creation",
        "__export__.res_groups_83_b108df00": "almik.group_sales_supervisor_purchases_assistant",
        "__export__.res_groups_84_7fb29c17": "almik.group_delivery_administrator",
        "__export__.res_groups_86_2204bc30": "almik.group_invoice_to_draft",
        "__export__.res_groups_89_d3598800": "almik.group_delivery_guide_user",
    }
    update_query = """
        UPDATE
            ir_model_data
        SET
            module = %s,
            name = %s,
            write_date = NOW() at time zone 'UTC'
        WHERE
            module = %s
            AND name = %s;
    """
    for old_id, new_id in ids_to_update.items():
        _logger.info("Updating record's external ID: %s -> %s", old_id, new_id)
        old_module, old_name = old_id.split(".")
        new_module, new_name = new_id.split(".")
        cr.execute(update_query, (new_module, new_name, old_module, old_name))
        if cr.rowcount:
            _logger.info("Record's external ID was updated: %s -> %s", old_id, new_id)
