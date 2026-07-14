variable "infra_config" {
  description = "Complete infrastructure configuration for Dev environment"
  type = object({
    resource_groups = map(object({
      location = string
      tags     = optional(map(string), {})
    }))
    storage_accounts = map(object({
      rg_key                  = string
      account_tier            = optional(string, "Standard")
      account_replication_type = optional(string, "LRS")
      kind                    = optional(string, "StorageV2")
      tags                    = optional(map(string), {})
    }))
  })
}
