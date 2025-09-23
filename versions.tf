terraform {
  required_version = ">= 0.15.5"
  required_providers {
    aws = {
      version = ">= 5.27"
      source  = "hashicorp/aws"
    }
    time = {
      source  = "hashicorp/time"
      version = ">= 0.7"
    }
  }
  backend "s3" {}
}

# Primary region where AFT deploys SSM Parameters is always eu-west-2. 
# Use this provider to grab SSM Parameters for data.tf
provider "aws" {
  alias  = "ssm"
  region = "eu-west-2"

  assume_role {
    role_arn = "arn:aws:iam::${ var.customer_account_id }:role/SSMInstanceProfile"
  }
}

# Home region where self-hosted runners are to be deployed
provider "aws" {
  region = var.customer_account_region
  
  assume_role {
    role_arn = "arn:aws:iam::${ var.customer_account_id }:role/AWSAFTExecution"
  }
}

provider "aws" {
  alias = "automation-account"
  region = var.customer_account_region

  assume_role {
    role_arn = "arn:aws:iam::${ var.automation_account_id }:role/AWSAFTExecution"
  }
}
