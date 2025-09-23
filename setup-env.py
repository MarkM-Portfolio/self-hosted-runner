import os, boto3, botocore, argparse
from pathlib import Path

class GenerateTemplate():

    def __init__(self):
        parser = argparse.ArgumentParser()

        parser.add_argument('--arg1', type = str, required = True)
        parser.add_argument('--arg2', type = str, required = True)
        parser.add_argument('--arg3', type = str, required = True)
        parser.add_argument('--arg4', type = int, required = True)
        parser.add_argument('--arg5', type = str, required = True)

        args = parser.parse_args()

        self.proj_dir = Path(os.path.dirname(os.path.realpath(__file__)))
        self.EXPORTED = []
        self.VARS = []
        self.AWS_RGN = args.arg1
        self.AWS_ALIAS = args.arg2
        self.AWS_ACCT = args.arg3
        self.RUNNER_COUNT = args.arg4
        self.RUNNER_ARCH = args.arg5
        self.RUNNER_NAMES = []
        self.RUNNER_LABELS = []
        self.AWS_REGNAME = None
        self.AWS_S3_BUCKET = f'tf-self-hosted-runner--{ self.AWS_ALIAS }-{ self.AWS_ACCT }'
        self.AWS_DYNAMO_DB = f'self-hosted-runner-tf-state-lock--{ self.AWS_ALIAS }-{ self.AWS_ACCT }'

        self.set_env()

    def set_runners(self, params):
        count = 0
        while count < self.RUNNER_COUNT:
            letter = chr(65 + count)

            if params == "name":
                self.RUNNER_NAMES.append(f"Self-Hosted Runner { letter } ({ self.AWS_ALIAS }--{ self.AWS_ACCT })")
            if params == "label":
                self.RUNNER_LABELS.append(f"{ self.AWS_ALIAS }--{ self.AWS_ACCT }--{ letter }")

            count += 1

        return str(self.RUNNER_NAMES if params == "name" else self.RUNNER_LABELS).replace("'", '"').replace("[", "[ ").replace("]", " ]")

    def set_env(self):
        self.EXPORTED.append("AWS_ALIAS")
        self.VARS.append(self.AWS_ALIAS)

        self.EXPORTED.append("AWS_ACCT")
        self.VARS.append(self.AWS_ACCT)
        
        self.EXPORTED.append("AWS_RGN")
        self.VARS.append(self.AWS_RGN)

        if 'eu-west-2' in self.AWS_RGN:
            self.AWS_REGNAME = "London"
        elif 'us-east-2' in self.AWS_RGN:
            self.AWS_REGNAME = 'Ohio'
        else:
            self.AWS_REGNAME = 'N/A'

        self.EXPORTED.append("AWS_REGNAME")
        self.VARS.append(self.AWS_REGNAME)

        self.EXPORTED.append("RUNNER_COUNT")
        self.VARS.append(str(self.RUNNER_COUNT))

        self.EXPORTED.append("RUNNER_ARCH")
        self.VARS.append(self.RUNNER_ARCH)

        # with open(f'{ self.proj_dir }/template/versions.tf', 'r') as vers_file:
        #     lines = vers_file.readlines()

        #     for i, line in enumerate(lines):
        #         if 'backend "s3"' in line:
        #             for j in range(i + 1, i + 5):
        #                 if 'bucket' in lines[j]:
        #                     self.AWS_S3_BUCKET = lines[j].split()[2].strip('"').replace('env.AWS_ACCT', self.AWS_ACCT)
        #                     continue
        #                 if 'dynamodb_table' in lines[j]:
        #                     self.AWS_DYNAMO_DB = lines[j].split()[2].strip('"')
        #                     break

        # # Define S3 bucket policy
        # s3_bucket_policy = {
        #     "Version": "2012-10-17",
        #     "Statement": [
        #         {
        #             "Effect": "Allow",
        #             "Principal": {
        #                 "AWS": f"arn:aws:sts::231639157514:assumed-role/github-oidc/actionsrolesession"
        #             },
        #             "Action": [
        #                 "s3:GetObject",
        #                 "s3:PutObject",
        #                 "s3:DeleteObject",
        #                 "s3:ListBucket"
        #             ],
        #             "Resource": [
        #                 f"arn:aws:s3:::{ self.AWS_S3_BUCKET }",
        #                 f"arn:aws:s3:::{ self.AWS_S3_BUCKET }/*"
        #             ]
        #         }
        #     ]
        # }

        # s3_bucket_policy_json = json.dumps(s3_bucket_policy)

        # Check if S3 Bucket exists
        try:
            boto3.client('s3', region_name=self.AWS_RGN).head_bucket(Bucket=self.AWS_S3_BUCKET)
            print(f"\nS3 Bucket { self.AWS_S3_BUCKET } already exists.")
        except botocore.exceptions.ClientError as e:
            error_code = int(e.response['Error']['Code'])
            if error_code == 404:
                print(f"\nS3 Bucket ({ self.AWS_S3_BUCKET }) does not exist. Creating...")
                boto3.client('s3').create_bucket(Bucket=self.AWS_S3_BUCKET, CreateBucketConfiguration={ 'LocationConstraint': self.AWS_RGN })
                boto3.client('s3').put_public_access_block(
                    Bucket=self.AWS_S3_BUCKET, 
                    PublicAccessBlockConfiguration={
                        'BlockPublicAcls': True,
                        'IgnorePublicAcls': True,
                        'BlockPublicPolicy': True,
                        'RestrictPublicBuckets': True
                    }
                )
                print(f"S3 Bucket ({ self.AWS_S3_BUCKET }) created!")
            else:
                print(f"Error: {e}")
                raise
        # finally:
        #     boto3.client('s3', region_name=self.AWS_RGN).put_bucket_policy(Bucket=self.AWS_S3_BUCKET, Policy=s3_bucket_policy_json)
        #     print(f"S3 Bucket policy attached.")

        self.EXPORTED.append("AWS_S3_BUCKET")
        self.VARS.append(self.AWS_S3_BUCKET)

        # Check if Dynamo DB table exists
        try:
            boto3.client('dynamodb', region_name=self.AWS_RGN).describe_table(TableName=self.AWS_DYNAMO_DB)
            print(f"\nDynamo DB table { self.AWS_DYNAMO_DB } already exists.")
        except botocore.exceptions.ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'ResourceNotFoundException':
                print(f"\nDynamo DB table ({ self.AWS_DYNAMO_DB }) does not exist. Creating...")
                boto3.client('dynamodb', region_name=self.AWS_RGN).create_table(TableName=self.AWS_DYNAMO_DB,
                    AttributeDefinitions=[{ 'AttributeName': 'LockID', 'AttributeType': 'S' }],
                    KeySchema=[{ 'AttributeName': 'LockID', 'KeyType': 'HASH' }],
                    ProvisionedThroughput={ 'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5 }
                )
                print(f"Dynamo DB table ({ self.AWS_DYNAMO_DB }) created!")
            else:
                print(f"Error: {e}")
                raise

        self.EXPORTED.append("AWS_DYNAMO_DB")
        self.VARS.append(self.AWS_DYNAMO_DB)

        print(f'\n{"-":>12}----------------------------------')
        print(f'{"-":>17} Setting up environment -')
        print(f'{"-":>12}----------------------------------\n')
        
        for item in self.EXPORTED:
            os.environ[item] = self.VARS[self.EXPORTED.index(item)]
        
        for i in range(len(self.VARS)):
            print(f"{self.EXPORTED[i]:>25}: {self.VARS[i]}")

        print(f'\n{"-":>12}----------------------------------')
        print('\nGenerating workflow & terraform files from template..')

        # terraform_files = [f for f in os.listdir(self.proj_dir) if f.endswith(('.tfvars', '.tf', '.tpl'))]
        # for file in terraform_files:
        #     os.remove(f'{ self.proj_dir }/{ file }')

        # TF_TEMPLATES = os.listdir(f'{ self.proj_dir }/template')

        # for file in TF_TEMPLATES:
        #     with open(f'{ self.proj_dir }/template/{ file }', 'r') as template_file:
        #         content = template_file.read()
        #         content = content.replace('env.AWS_ALIAS', self.AWS_ALIAS)
        #         content = content.replace('env.AWS_ACCT', self.AWS_ACCT)
        #         content = content.replace('env.AWS_RGN', self.AWS_RGN)
        #         content = content.replace('env.AWS_REGNAME', self.AWS_REGNAME)

        #     if file.endswith(('.tfvars', '.tf', '.tpl')):
        #         with open(f'{ self.proj_dir }/{ file }', 'w') as tf_file:
        #             tf_file.write(content)

        try:
            os.remove(f'{self.proj_dir}/variables.tf')
        except FileNotFoundError:
            print(f"File {self.proj_dir}/variables.tf does not exist, so it cannot be removed.")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

        with open(f'{ self.proj_dir }/variables.tpl', 'r') as vars_template:
            content = vars_template.read()
            content = content.replace('env.AWS_ALIAS', self.AWS_ALIAS)
            content = content.replace('env.AWS_ACCT', self.AWS_ACCT)
            content = content.replace('env.AWS_RGN', self.AWS_RGN)
            content = content.replace('env.AWS_REGNAME', self.AWS_REGNAME)
            content = content.replace('env.RUNNER_COUNT', str(self.RUNNER_COUNT))
            content = content.replace('env.RUNNER_ARCH', self.RUNNER_ARCH)
            content = content.replace('env.RUNNER_NAMES', self.set_runners("name"))
            content = content.replace('env.RUNNER_LABELS', self.set_runners("label"))

        with open(f'{ self.proj_dir }/variables.tf', 'w') as vars_tf:
            vars_tf.write(content)

        print("\nDONE...")


if __name__ == '__main__':
    try:
        ACCT_NAME = boto3.client('sts').get_caller_identity()['UserId'].split(':')[1]
    except Exception as e:
        print('[ERROR]: No awsumed account. Please set one now!')
        print("i.e : awsume <AWS_ACCOUNT_NAME>")
    else:
        # try:
        #     boto3.client('resourcegroupstaggingapi').get_tag_values(Key="CustomerID").get('TagValues', [])[0]
        # except Exception as e:
        #     print(f'[ERROR]: Account ({ ACCT_NAME }) has no tag CustomerID. Please set one now!')
        # else:
        GenerateTemplate()
            