# CloudFormation Permissions Generator (cfn-perm)

A tool to automatically generate IAM permissions from CloudFormation templates.

## Overview

This tool analyzes CloudFormation templates to identify all resource types used, then queries the CloudFormation registry to determine the required IAM permissions for each resource type. It can generate IAM policy documents or create IAM roles with the appropriate permissions.

## Features

- Parse CloudFormation templates in JSON or YAML format
- Extract resource types and determine required permissions
- Generate IAM policy documents with appropriate permissions
- Create IAM roles with the generated permissions
- Option to allow or deny delete permissions
- Support for permissions boundaries

## Prerequisites

- Python 3.9+
- AWS CLI configured with [CloudFormation DescribeType](https://docs.aws.amazon.com/AWSCloudFormation/latest/APIReference/API_DescribeType.html) permission
- Required Python packages: boto3, pyyaml

## Installation

```bash
git clone https://github.com/yourusername/cfn-perm.git
cd cfn-perm
pip install -r requirements.txt
```

## Usage

```bash
python source/app.py <template_file> [options]
# or using shorthand options
python source/app.py -t <template_file> [options]
```

### Arguments

- `template_file` or `-t, --template-file`: Path to the CloudFormation template file (JSON or YAML)

### Options

- `-d, --allow-delete`: Allow delete permissions instead of denying them
- `-c, --create-role`: Create an IAM role with the generated permissions (default: True)
- `-r, --role-name`: Name for the IAM role (if not specified, uses 'cfn-perm-<random_hash>')
- `-p, --permissions-boundary`: ARN of the permissions boundary to attach to the role

### Examples

Generate a policy document from a template:
```bash
python source/app.py path/to/template.yaml
# or
python source/app.py -t path/to/template.yaml
```

Create an IAM role with delete permissions denied (default behavior):
```bash
python source/app.py path/to/template.yaml
```

Create an IAM role with delete permissions allowed:
```bash
python source/app.py path/to/template.yaml -d
```

Create an IAM role with a custom name:
```bash
python source/app.py path/to/template.yaml -r MyCustomRole
```

Create an IAM role with a permissions boundary:
```bash
python source/app.py path/to/template.yaml -p arn:aws:iam::123456789012:policy/boundary
```

## How It Works

1. The tool parses the CloudFormation template to extract all resource types
2. For each resource type, it queries the CloudFormation registry to get the required permissions
3. It categorizes permissions into "update" (create/update/read) and "delete-specific" permissions
4. It generates a policy document with appropriate Allow and Deny statements
5. It saves the policy document to a file with a unique name
6. If requested (default), it creates an IAM role with the generated policy