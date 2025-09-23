variable "automation_account_id" {
  description = "Automation Account ID"
  type        = string
  default     = "231639157514"
}

variable "customer_account_id" {
  description = "Customer Account ID"
  type        = string
  default     = "env.AWS_ACCT"
}

variable "customer_account_region" {
  description = "Customer Account Region"
  type        = string
  default     = "env.AWS_RGN"
}

variable "customer_account_name" {
  description = "Customer Account Name"
  type        = string
  default     = "env.AWS_ALIAS"
}

variable "ohio_shared_vpc_cidr" {
  description = "CIDR Block for the ohio vpc"
  type        = string
  default     = "172.18.0.0/22"
}

variable "runner_names" {
  description = "Self-Hosted Runner List"
  type        = list(string)
  default     = env.RUNNER_NAMES
}

variable "runner_labels" {
  description = "Self-Hosted Runner Label List"
  type        = list(string)
  default     = env.RUNNER_LABELS
}

variable "runner_arch" {
  description = "Self-Hosted Runner Arch Type"
  type        = string
  default     = "env.RUNNER_ARCH"
}
