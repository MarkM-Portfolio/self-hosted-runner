module "self_hosted_runner" {
  source   = "git@github.com:SapphireSystems/terraform-aws-ec2-instance?ref=v5.7.1"
  # source = "github.com/terraform-aws-modules/terraform-aws-ec2-instance//?ref=v5.7.1" #temporary use if local repo not yet updated to 5.7.1 

  for_each = local.self_hosted_runner

  name                   = each.key
  ami                    = each.value.ami #if config error check AMI is shared for that current region
  instance_type          = each.value.instance_type
  subnet_id              = each.value.subnet_id
  vpc_security_group_ids = each.value.vpc_security_group_ids
  iam_instance_profile   = each.value.iam_instance_profile
  root_block_device      = each.value.root_block_device
  enable_volume_tags     = true

  user_data = each.value.user_data

  tags = merge(
    each.value.tags,
    local.tags
  )
}
