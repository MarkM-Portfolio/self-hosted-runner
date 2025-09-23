locals {
  accountid   = data.aws_caller_identity.current.account_id
  region      = data.aws_ssm_parameter.region.value
  environment = data.aws_ssm_parameter.environment.value

  self_hosted_runner = {
    # Light Workloads:
    # 	arm64: t4g.medium (2 vCPUs, 4 GB RAM, Graviton-based)
    # 	x64: t3.medium (2 vCPUs, 4 GB RAM)
    # Medium Workloads: << medium is set now
    # 	arm64: t4g.large (2 vCPUs, 8 GB RAM)
    # 	x64: t3.large (2 vCPUs, 8 GB RAM) or m6i.large (Intel-based)
    # Heavy Workloads:
    # 	arm64: c6g.xlarge (4 vCPUs, 8 GB RAM, Graviton-based)
    # 	x64: c6i.xlarge (4 vCPUs, 8 GB RAM, compute-optimized)
    for instance_name in var.runner_names : instance_name => {
      ami                    = var.runner_arch == "arm64" ? data.aws_ami.ubuntu24-arm64.id : data.aws_ami.ubuntu22-x86_64.id
      instance_type          = var.runner_arch == "arm64" ? "t4g.large" : "t3.large"
      subnet_id              = contains(var.runner_names, instance_name) ? (index(var.runner_names, instance_name) % 2 == 0 ? data.aws_subnet.data_a.id : data.aws_subnet.data_b.id) : data.aws_subnet.data_b.id
      vpc_security_group_ids = [ data.aws_security_group.baseline_data.id, data.aws_security_group.migration.id ]
      iam_instance_profile   = "SSMInstanceProfile"

      root_block_device = [
        {
          encrypted             = true
          volume_size           = 100
          volume_type           = "gp3"
          throughput            = 125
          iops                  = 3000
          delete_on_termination = true
        }
      ]

      user_data = templatefile("${path.module}/runner_${ var.runner_arch }.tpl", {
        user  = "ubuntu"
        label = var.runner_labels[index(var.runner_names, instance_name)]
        runner_version = "2.322.0" #  "2.321.0" (previous version)
        account_name = var.customer_account_name
        region = var.customer_account_region
      })

      tags = {
        "Name"           = instance_name
        "label"          = var.runner_labels[index(var.runner_names, instance_name)]
        "Runner Version" = "2.322.0" #  "2.321.0" (previous version)
        "CustomerName"   = var.customer_account_name
        "Github Repo"    = "https://github.com/SapphireSystems/customer-onboarding-terraform"
        "Description"    = "Self Hosted Runner for customer-onboarding (Managed by Terraform)"
        "OS Release"     = "Ubuntu ${ var.runner_arch == "arm64" ? "24.04" : "22.04.1" } LTS (${ var.runner_arch })"
      }
    }
  }

  tags = {
    "Environment" = local.environment
  }
}
