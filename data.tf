data "aws_caller_identity" "current" {}

# SSM Parameter DataSources
data "aws_ssm_parameter" "region" {
  provider = aws.ssm
  name     = "/aft/account-request/custom-fields/region"
}

data "aws_ssm_parameter" "environment" {
  provider = aws.ssm
  name     = "/aft/account-request/custom-fields/environment"
}

# VPC Data Source
data "aws_vpc" "this" {
  filter {
    name   = "tag:Name"
    values = ["vpc-${var.customer_account_region}-${local.environment}"]
  }
}

# Subnet Data Sources
data "aws_subnet" "data_a" {
  vpc_id            = data.aws_vpc.this.id
  availability_zone = "${ local.region }a"
  filter {
    name   = "tag:Name"
    values = [ "*-data-*" ]
  }
}

data "aws_subnet" "data_b" {
  vpc_id            = data.aws_vpc.this.id
  availability_zone = "${ local.region }b"
  filter {
    name   = "tag:Name"
    values = [ "*-data-*" ]
  }
}

# Security Group Data Sources
data "aws_security_group" "baseline_data" {
  vpc_id = data.aws_vpc.this.id
  filter {
    name   = "tag:Name"
    values = [ "*-baseline-data-*" ]
  }
}

data "aws_security_group" "migration" {
  vpc_id = data.aws_vpc.this.id
  filter {
    name   = "tag:Name"
    values = [ "*-migration-*" ]
  }
}

data "aws_ami" "ubuntu22-x86_64" {
  provider = aws.automation-account
  owners      = [ var.automation_account_id ]
  most_recent = true
  filter {
    name   = "tag:Name"
    values = [ "UBUNTU_2204-x86_64" ]
  }
}

data "aws_ami" "ubuntu24-arm64" {
  provider = aws.automation-account
  owners      = [ var.automation_account_id ]
  most_recent = true
  filter {
    name   = "tag:Name"
    values = [ "UBUNTU_2404-arm64" ]
  }
}
