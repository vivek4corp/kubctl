infra_config = {
  resource_groups = {
    "rg-micro-dev" = {
      location = "East US"
      tags     = { Environment = "Dev", ManagedBy = "Terraform" }
    }
  }
  storage_accounts = {
    "stgmicrodev123" = {
      rg_key                  = "rg-micro-dev"
      account_tier            = "Standard"
      account_replication_type = "LRS"
      kind                    = "StorageV2"
      tags                    = { Environment = "Dev", ManagedBy = "Terraform" }
    }
  }
}
