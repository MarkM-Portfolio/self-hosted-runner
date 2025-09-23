output "self_hosted_runner" {
  description = "The private IP address assigned to the instance."
  value = {
    for k, v in module.self_hosted_runner : k => v.private_ip
  }
}
