import boto3, argparse, json

class CrossAccount():

    def __init__(self):
        parser = argparse.ArgumentParser()

        parser.add_argument('--arg1', type = str, required = True)
        parser.add_argument('--arg2', type = str, required = True)
        parser.add_argument('--arg3', type = str, required = True)

        args = parser.parse_args()
        
        self.CUSTOMERID = args.arg1
        self.ROLE = args.arg2
        self.METHOD = args.arg3
        self.ROLES = []
        
        self.cross_account()

    def cross_account(self):
        insert_role = f"arn:aws:sts::{ self.CUSTOMERID }:assumed-role/github-oidc/actionsrolesession"

        try:
            current_policy_response = boto3.client('iam').get_role(RoleName=self.ROLE)
            current_trust_policy = current_policy_response['Role']['AssumeRolePolicyDocument']
        except Exception as e:
            print(f"Error getting role: { e }")

        if self.ROLE == 'AWSAFTExecution':
            for item in current_trust_policy['Statement']:
                self.ROLES = item.get('Principal')['AWS']
            # if data type not list >> AWS: []
            if not isinstance(self.ROLES, list):
                self.ROLES = [ self.ROLES ]

        if self.METHOD == 'insert':
            self.insert(insert_role, current_trust_policy)
        if self.METHOD == 'remove':
            self.remove(insert_role, current_trust_policy)

    def insert(self, role_name, current_trust_policy):
        if role_name not in self.ROLES and self.ROLE == 'AWSAFTExecution':
            self.ROLES.append(role_name)

        trust_policy = {
            "Effect": "Allow",
            "Principal": {
                "AWS": self.ROLES if self.ROLE == 'AWSAFTExecution' else role_name
            },
            "Action": "sts:AssumeRole"
        }

        if self.ROLE == 'SSMInstanceProfile':
            try:
                boto3.client('iam').attach_role_policy(
                    RoleName=self.ROLE,
                    PolicyArn="arn:aws:iam::aws:policy/AdministratorAccess"
                )
                print(f"Policy AdministratorAccess attached to role { self.ROLE } successfully.")
            except Exception as e:
                print(f"Error attach role policy for role: { e }")

            try:
                boto3.client('iam').update_role(
                    RoleName=self.ROLE,
                    MaxSessionDuration=14400
                )
                print(f"Role { self.ROLE } updated successfully.")
            except boto3.client('iam').exceptions.ClientError:
                print(f"Error updating the role: { self.ROLE }")

            trust_policy["Principal"]["Service"] = "ec2.amazonaws.com"

        current_trust_policy['Statement'] = trust_policy

        try:
            boto3.client('iam').update_assume_role_policy(
                RoleName=self.ROLE,
                PolicyDocument=json.dumps(current_trust_policy)
            )
            print(f"Trust policy for role { self.ROLE } added successfully.")
        except Exception as e:
            print(f"Error updating policy: { e }")

    def remove(self, role_name, current_trust_policy):
        if role_name in self.ROLES and self.ROLE == 'AWSAFTExecution':
            self.ROLES.remove(role_name)

        trust_policy = {
            "Effect": "Allow",
            "Principal": {
                "AWS": self.ROLES if self.ROLE == 'AWSAFTExecution' else role_name,
                "Service": "ec2.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }

        try:
            boto3.client('iam').update_role(
                RoleName=self.ROLE,
                MaxSessionDuration=3600
            )
            print(f"Role { self.ROLE } updated successfully.")
        except boto3.client('iam').exceptions.ClientError:
            print(f"Error updating the role: { self.ROLE }")

        if self.ROLE == 'SSMInstanceProfile':
            try:
                boto3.client('iam').detach_role_policy(
                    RoleName=self.ROLE,
                    PolicyArn="arn:aws:iam::aws:policy/AdministratorAccess"
                )
                print(f"Policy AdministratorAccess detached from role { self.ROLE } successfully.")
            except Exception as e:
                print(f"Error detaching role policy for role: { e }")

            del trust_policy["Principal"]["AWS"]

        if self.ROLE == 'AWSAFTExecution':
            del trust_policy["Principal"]["Service"]

        current_trust_policy['Statement'] = trust_policy

        try:
            boto3.client('iam').update_assume_role_policy(
                RoleName=self.ROLE,
                PolicyDocument=json.dumps(current_trust_policy)
            )
            print(f"Trust policy for role { self.ROLE } removed successfully.")
        except Exception as e:
            print(f"Error updating policy: { e }")


if __name__ == '__main__':
    CrossAccount()
    