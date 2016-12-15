#!/usr/bin/python

# API Gateway Ansible Modules
#
# Modules in this project allow management of the AWS API Gateway service.
#
# Authors:
#  - Brian Felton <bjfelton@gmail.com>
#
# apigw_domain_name
#    Manage creation, update, and removal of API Gateway DomainName resources
#

## TODO: Add an appropriate license statement

DOCUMENTATION='''
module: apigw_domain_name
description: An Ansible module to add, update, or remove DomainName
  resources for AWS API Gateway.
version_added: "2.2"
options:
  name:
    description: The name of the DomainName resource on which to operate
    type: string
    required: True
    aliases: domain_name
  cert_name:
    description: Name of the associated certificate. Required when C(state) is 'present'
    type: string
    required: False
    default: None
  cert_private_key:
    description: Certificate's private key. Required when C(state) is 'present'
    type: string
    required: False
    default: None
  cert_body:
    description: Body of the server certificate. Required when C(state) is 'present'
    type: string
    required: False
    default: None
  cert_chain:
    description: Intermediate certificates and optionally the root certificate.  If root is included, it must follow the intermediate certificates. Required when C(state) is 'present'
    type: string
    required: False
    default: None
  state:
    description: Should domain_name exist or not
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
---
- hosts: localhost
  gather_facts: False
  tasks:
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

class ApiGwDomainName:
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
                 cert_name=dict(required=False),
                 cert_body=dict(required=False),
                 cert_private_key=dict(required=False),
                 cert_chain=dict(required=False),
                 state=dict(default='present', choices=['present', 'absent']),
    )

  def _retrieve_domain_name(self):
    """
    Retrieve all domain_names in the account and match them against the provided name
    :return: Result matching the provided api name or an empty hash
    """
    resp = None
    try:
      get_resp = self.client.get_domain_names(nameQuery=self.module.params['name'], includeValues=True)

      for item in get_resp.get('items', []):
        if item['name'] == self.module.params.get('name'):
          resp = item
    except BotoCoreError as e:
      self.module.fail_json(msg="Error when getting domain_names from boto3: {}".format(e))

    return resp

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
        argument_spec=ApiGwDomainName._define_module_argument_spec(),
        supports_check_mode=True
    )

    domain_name = ApiGwDomainName(module)
    domain_name.process_request()

from ansible.module_utils.basic import *  # pylint: disable=W0614
if __name__ == '__main__':
    main()
