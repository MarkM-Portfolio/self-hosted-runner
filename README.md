# Self-Hosted Runner Workflow


* Create GitHub Personal Access Token
[GitHub URL](https://github.com/settings/tokens)


* S3 Bucket

| Name                                                               | Bucket Versioning | Access                        |
| ------------------------------------------------------------------ |-------------------|-------------------------------|
| [tf-self-hosted-runner--<ACCT_NAME>-<ACCT_ID>](https://<ACCT_RGN>.console.aws.amazon.com/s3/buckets?bucketType=general&region=<ACCT_RGN>#)                                | Disabled          | Bucket and objects not public |

* DynamoDB Table

| Name                                                            | Partition key     |
| --------------------------------------------------------------- |-------------------|
| [self-hosted-runner-tf-state-lock--<ACCT_NAME>-<ACCT_ID>](https://<ACCT_RGN>.console.aws.amazon.com/dynamodbv2/home?region=<ACCT_RGN>#tables)                               | LockID (string)   |



* Self Hosted Runners are provisioned into customer account
* AMIs (from sapphire-payer) are shared into AFT-Management account
* IAM role used is github/oidc role
* Self Hosted Runners auto provision when pull requests/merge events occur in customer-onboarding-terraform repo
* Single workflow running in parallel for provisioning servers to save time
* Infracost added to ask to calculate estimated current infrastructure cost
* Self Hosted Runners auto termination after provisioning servers for cost savings
