import boto3, argparse, json

class CreateSecret():

    def __init__(self):
        parser = argparse.ArgumentParser()

        parser.add_argument('--arg1', type = str, required = True)
        parser.add_argument('--arg2', type = str, required = True)

        args = parser.parse_args()
        
        self.SECRET_NAME = args.arg1
        self.SECRET_VALUE = { self.SECRET_NAME: args.arg2 }

        self.create_secret()

    def create_secret(self):
        # Check if the secret exists and is scheduled for deletion
        try:
            boto3.client('secretsmanager').describe_secret(SecretId=self.SECRET_NAME)
            print(f"Secret { self.SECRET_NAME } exists.")
        except boto3.client('secretsmanager').exceptions.ResourceNotFoundException:
            print(f"Secret { self.SECRET_NAME } does not exist. It can be created.")
        else:
            try:
                boto3.client('secretsmanager').restore_secret(SecretId=self.SECRET_NAME)
                print(f"Canceled deletion of secret { self.SECRET_NAME }.")
            except boto3.client('secretsmanager').exceptions.InvalidRequestException as e:
                print(f"Secret { self.SECRET_NAME } is not scheduled for deletion or cannot be canceled: { e }")

        try:
            boto3.client('secretsmanager').create_secret(
                Name=self.SECRET_NAME,
                SecretString=json.dumps(self.SECRET_VALUE)
            )
            print(f"Secret { self.SECRET_NAME } created successfully.")
        except boto3.client('secretsmanager').exceptions.ResourceExistsException:
            print(f"Secret { self.SECRET_NAME } already exists.")
        except Exception as e:
            print(f"Error creating secret: { e }")


if __name__ == '__main__':
    CreateSecret()
