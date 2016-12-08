#!/usr/bin/python

# API Gateway Ansible Modules
#
# Modules in this project allow management of the AWS API Gateway service.
#
# Authors:
#  - Brian Felton <bjfelton@gmail.com>
#
# apigw_base_path_mapping
#    Manage creation, update, and removal of API Gateway Base Path Mapping resources
#

## TODO: Add an appropriate license statement

DOCUMENTATION='''
module: apigw_base_path_mapping
description: An Ansible module to add, update, or remove Base Path Mapping resources for
  AWS API Gateway.
version_added: "2.2"
options:
  name:
    description: The domain name of the Base Path Mapping resource on which to operate
    required: True
    aliases: ['domain_name']
  rest_api_id:
    description: The id of the Rest API to which this BasePathMapping belongs.
      Required to create a base path mapping.
    default: None
    required: False
  base_path:
    description: The base path name that callers of the api must provide.
    default: (none)
    required: False
  stage:
    description: The name of the api's stage to which to apply this mapping.
      Required to create the base path mapping.
    default: None
    required: False
  state:
    description: Should base_path_mapping exist or not
    choices: ['present', 'absent']
    default: 'present'
    required: False
requirements:
    - python = 2.7
    - boto
    - boto3
notes:
    - This module requires that you have boto and boto3 installed and that your
      credentials are created or stored in a way that is compatible (see
      U(https://boto3.readthedocs.io/en/latest/guide/quickstart.html#configuration)).
'''

EXAMPLES = '''
TBD
'''

RETURN = '''
TBD
'''

__version__ = '${version}'

try:
  import boto3
  import boto
  from botocore.exceptions import BotoCoreError
  HAS_BOTO3 = True
except ImportError:
  HAS_BOTO3 = False

class ApiGwBasePathMapping:
  def __init__(self, module):
    """
    Constructor
    """
    self.module = module
    if (not HAS_BOTO3):
      self.module.fail_json(msg="boto and boto3 are required for this module")
    self.client = boto3.client('apigateway')

  @staticmethod
  def _define_module_argument_spec():
    """
    Defines the module's argument spec
    :return: Dictionary defining module arguments
    """
    return dict( name=dict(required=True, aliases=['domain_name']),
                 rest_api_id=dict(required=False),
                 base_path=dict(required=False, default='(none)'),
                 stage=dict(required=False),
                 state=dict(default='present', choices=['present', 'absent']),
    )

  def process_request(self):
    """
    Process the user's request -- the primary code path
    :return: Returns either fail_json or exit_json
    """
    raise NotImplementedError

def main():
    """
    Instantiates the module and calls process_request.
    :return: none
    """
    module = AnsibleModule(
        argument_spec=ApiGwBasePathMapping._define_module_argument_spec(),
        supports_check_mode=True
    )

    base_path_mapping = ApiGwBasePathMapping(module)
    base_path_mapping.process_request()

from ansible.module_utils.basic import *  # pylint: disable=W0614
if __name__ == '__main__':
    main()