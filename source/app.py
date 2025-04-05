#!/usr/bin/env python3
import boto3
import argparse
import json
import yaml
import sys
import re
import uuid
import hashlib

def parse_cloudformation_template(file_path):
    if file_path.endswith('.json'):
        with open(file_path, 'r') as file:
            template = json.load(file)
    elif file_path.endswith(('.yaml', '.yml')):
        with open(file_path, 'r') as file:
            template = yaml.safe_load(file)
    else:
        raise ValueError(
            "Unsupported file format. Please provide a JSON or YAML file.")

    if 'Resources' not in template:
        print("No Resources section found in the template.")
        return set()

    resources = template['Resources']
    resource_types = set()

    ignore_patterns = [
        r"^Custom::.*",
        r"^AWS::CDK::Metadata",
        r"^AWS::CloudFormation::CustomResource"
    ]

    for resource in resources.values():
        if 'Type' in resource:
            resource_type = resource['Type']
            should_ignore = False
            for pattern in ignore_patterns:
                if re.match(pattern, resource_type):
                    should_ignore = True
                    break
            if not should_ignore:
                resource_types.add(resource_type)
    return resource_types


def get_permissions(resourcetype):
    cfn_client = boto3.client('cloudformation')
    response = cfn_client.describe_type(
        Type='RESOURCE',
        TypeName=resourcetype
    )
    data = json.loads(response['Schema'])
    iam_update = set()
    iam_delete = set()
    delete_specific = set()
    if 'handlers' in data:
        if 'create' in data['handlers']:
            iam_update.update(data['handlers']['create']['permissions'])
        if 'update' in data['handlers']:
            iam_update.update(data['handlers']['update']['permissions'])
        if 'delete' in data['handlers']:
            delete_specific.update(data['handlers']['delete']['permissions'])
        if 'read' in data['handlers']:
            iam_update.update(data['handlers']['read']['permissions'])
        if 'list' in data['handlers']:
            iam_update.update(data['handlers']['list']['permissions'])

    iam_delete = delete_specific.difference(iam_update)
    return iam_update, iam_delete


def generate_random_hash():
    """Generate a short random hash for role name uniqueness"""
    random_id = str(uuid.uuid4())
    hash_object = hashlib.md5(random_id.encode())
    return hash_object.hexdigest()[:8]


def generate_policy_document(all_update_permissions, all_delete_permissions, allow_delete=False):
    """
    Generate an IAM policy document with the specified permissions.

    Args:
        all_update_permissions (set): Set of permissions to allow
        all_delete_permissions (set): Set of permissions to deny or allow based on allow_delete flag
        allow_delete (bool): If True, include delete permissions as Allow, otherwise as Deny

    Returns:
        dict: Policy document
    """
    statements = []
    if all_update_permissions:
        statements.append({
            "Effect": "Allow",
            "Action": list(sorted(all_update_permissions)),
            "Resource": "*"
        })
    if all_delete_permissions:
        statements.append({
            "Effect": "Allow" if allow_delete else "Deny",
            "Action": list(sorted(all_delete_permissions)),
            "Resource": "*"
        })

    policy_document = {
        "Version": "2012-10-17",
        "Statement": statements
    }

    return policy_document


def create_iam_role(policy_document, role_name, permissions_boundary=None):
    iam_client = boto3.client('iam')
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "cloudformation.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }

    try:
        create_role_params = {
            "RoleName": role_name,
            "AssumeRolePolicyDocument": json.dumps(trust_policy),
            "Description": "Role generated using cfn-perm"
        }
        if permissions_boundary:
            create_role_params["PermissionsBoundary"] = permissions_boundary

        response = iam_client.create_role(**create_role_params)
        role_arn = response['Role']['Arn']
        policy_name = f"{role_name}-Policy"
        iam_client.put_role_policy(
            RoleName=role_name,
            PolicyName=policy_name,
            PolicyDocument=json.dumps(policy_document)
        )
        return role_arn

    except Exception as e:
        print(f"Error creating IAM role: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Generate least IAM permissions for a CloudFormation template")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("template_file", nargs="?",
                       help="Path to the CloudFormation template file")
    group.add_argument("-t", "--template-file", dest="template_file_opt",
                       help="Path to the CloudFormation template file")
    parser.add_argument("-d", "--allow-delete", action="store_true",
                        default=False, help="Allow delete permissions instead of denying them")
    parser.add_argument("-c", "--create-role", action="store_true", default=True,
                        help="Create an IAM role with the generated permissions")
    parser.add_argument(
        "-r", "--role-name", help="Name for the IAM role (if not specified, uses 'cfn-perm-<random_hash>')")
    parser.add_argument("-p", "--permissions-boundary",
                        help="ARN of the permissions boundary to attach to the role")

    args = parser.parse_args()
    
    # Determine which template file argument to use
    template_file = args.template_file if args.template_file else args.template_file_opt

    try:
        print(f"Parsing CloudFormation template: {template_file}")
        resource_types = parse_cloudformation_template(template_file)

        if not resource_types:
            print("No resource types found in the template.")
            sys.exit(1)

        all_update_permissions = set()
        all_delete_permissions = set()

        for resource in resource_types:
            update_permissions, delete_permissions = get_permissions(resource)
            all_update_permissions.update(update_permissions)
            all_delete_permissions.update(delete_permissions)

        policy_document = generate_policy_document(
            all_update_permissions, all_delete_permissions, args.allow_delete)
        random_hash = generate_random_hash()
        file_path = f"policy-{random_hash}.json"
        with open(file_path, 'w') as json_file:
            json.dump(policy_document, json_file, indent=2)
        print(f"\nGenerated IAM Policy Document to {file_path}")

        if args.create_role:
            if not args.role_name:
                random_hash = generate_random_hash()
                role_name = f"cfn-perm-{random_hash}"
            else:
                role_name = args.role_name

            role_arn = create_iam_role(
                policy_document,
                role_name,
                args.permissions_boundary
            )
            if role_arn:
                print(f"\nSuccessfully created IAM role: {role_arn}")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
