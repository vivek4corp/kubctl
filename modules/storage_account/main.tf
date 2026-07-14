resource "azurerm_storage_account" "this" {
  for_each = var.storage_accounts

  name                     = each.key
  resource_group_name      = each.value.resource_group_name
  location                 = each.value.location
  account_tier             = each.value.account_tier
  account_replication_type = each.value.account_replication_type

  tags = each.value.tags
}

output "storage_account_names" {
  value = { for k, v in azurerm_storage_account.this : k => v.name }
}
