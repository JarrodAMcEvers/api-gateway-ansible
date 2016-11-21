#!/usr/bin/python

# API Gateway Ansible Modules
#
# Modules in this project allow management of the AWS API Gateway service.
#
# Authors:
#  - Brian Felton <bjfelton@gmail.com>
#
# apigw_resource
#    Manage creation, update, and removal of API Gateway Method resources
#

## TODO: Add an appropriate license statement

DOCUMENTATION='''
module: apigw_method
description:
  - An Ansible module to add, update, or remove AWS API Gateway
    method resources
version_added: "2.2"
options:
  name:
    description:
      - The name of the method on which to operate
    choices: ['get', 'put', 'post', 'delete', 'patch', 'head']
    required: True
  rest_api_id:
    description:
      - The id of the parent rest api
    required: True
  resource_id:
    description:
      - The id of the resource to which the method belongs
    required: True
  state:
    description:
      - Determine whether to assert if resource should exist or not
    choices: ['present', 'absent']
    default: 'present'
    required: False

TODO: FINISH THIS

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
TODO: FINISH THIS
'''

RETURN = '''
TODO: FINISH THIS
'''

__version__ = '${version}'

import copy
try:
  import boto3
  import boto
  from botocore.exceptions import BotoCoreError, ClientError
  HAS_BOTO3 = True
except ImportError:
  HAS_BOTO3 = False

class InvalidInputError(Exception):
  def __init__(self, param, fail_message):
    """
    Exceptions raised for parameter validation errors
    :param param: The parameter with an illegal value
    :param fail_message: Message specifying why exception is being raised
    """
    Exception.__init__(self, "Error validating {0}: {1}".format(param, fail_message))

def create_patch(op, path, prefix=None, value=None):
  if re.search('/', path):
    path = re.sub('/', '~1', path)

  path = "/{}/{}".format(prefix, path) if prefix else "/{}".format(path)

  resp = {'op': op, 'path': path}
  if value is not None:
    resp['value'] = str(value)
  return resp

def patch_builder(method, params, param_map):
  ops = []
  for ans_param, boto_param in param_map.iteritems():
    if ans_param not in params and boto_param not in method:
      pass
    elif ans_param not in params and boto_param in method:
      ops.append(create_patch('remove', boto_param))
    elif ans_param in params and boto_param not in method:
      ops.append(create_patch('add', boto_param, value=params[ans_param]))
    elif str(params[ans_param]) != str(method[boto_param]):
      ops.append(create_patch('replace', boto_param, value=params[ans_param]))

  return ops

def two_way_compare_patch_builder(aws_dict, ans_dict, prefix):
  ops = []

  for k in ans_dict.keys():
    if k not in aws_dict.get(prefix, {}):
      ops.append(create_patch('add', k, prefix=prefix, value=ans_dict[k]))
    elif str(ans_dict[k]) != str(aws_dict[prefix][k]):
      ops.append(create_patch('replace', k, prefix=prefix, value=ans_dict[k]))

  for k in aws_dict.get(prefix, {}).keys():
    if k not in ans_dict:
      ops.append(create_patch('remove', k, prefix=prefix))

  return ops

def put_method(params):
  return dict(
    restApiId=params.get('rest_api_id'),
    resourceId=params.get('resource_id'),
    httpMethod=params.get('name'),
    authorizationType=params.get('authorization_type'),
    apiKeyRequired=params.get('api_key_required', False),
    requestParameters=param_transformer(params.get('request_params', []), 'request')
  )

def update_method(method, params):
  patches = {}

  param_map = {
    'authorization_type': 'authorizationType',
    'authorizer_id': 'authorizerId',
    'api_key_required': 'apiKeyRequired',
  }

  ops = patch_builder(method, params, param_map)
  ops.extend(
    two_way_compare_patch_builder(
      method,
      param_transformer(params.get('request_params', []), 'request'),
      'requestParameters'
    )
  )

  if ops:
    patches = dict(
      restApiId=params.get('rest_api_id'),
      resourceId=params.get('resource_id'),
      httpMethod=params.get('name'),
      patchOperations=ops
    )

  return patches

def put_integration(params):
  args = dict(
    restApiId=params.get('rest_api_id'),
    resourceId=params.get('resource_id'),
    httpMethod=params.get('name'),
    type=params['method_integration'].get('integration_type'),
    requestParameters=param_transformer(params['method_integration'].get('integration_params', []), 'request'),
    requestTemplates=add_templates(params['method_integration'].get('request_templates', []))
  )

  optional_map = {
    'http_method': 'integrationHttpMethod',
    'uri': 'uri',
    'passthrough_behavior': 'passthroughBehavior',
    'cache_namespace': 'cacheNamespace',
    'cache_key_parameters': 'cacheKeyParameters'
  }

  add_optional_params(params['method_integration'], args, optional_map)

  return args

def update_integration(method, params):
  patches = {}

  mi_params = params.get('method_integration', {})

  param_map = {
    'integration_type': 'type',
    'http_method': 'httpMethod',
    'uri': 'uri',
    'passthrough_behavior': 'passthroughBehavior',
    'cache_namespace': 'cacheNamespace',
    'cache_key_parameters': 'cacheKeyParameters',
  }

  ops = patch_builder(method.get('methodIntegration', {}), mi_params, param_map)
  ops.extend(
    two_way_compare_patch_builder(
      method.get('methodIntegration', {}),
      param_transformer(mi_params.get('integration_params', []), 'request'),
      'requestParameters'
    )
  )
  ops.extend(
    two_way_compare_patch_builder(
      method.get('methodIntegration', {}),
      add_templates(mi_params.get('request_templates', [])),
      'requestTemplates'
    )
  )

  if ops:
    patches = dict(
      restApiId=params.get('rest_api_id'),
      resourceId=params.get('resource_id'),
      httpMethod=params.get('name'),
      patchOperations=ops
    )

  return patches

def put_method_response(params):
  args = []

  for mr_params in params.get('method_responses', []):
    kwargs = dict(
      restApiId=params.get('rest_api_id'),
      resourceId=params.get('resource_id'),
      httpMethod=params.get('name'),
      statusCode=str(mr_params.get('status_code'))
    )
    resp_models = {}
    for model in mr_params.get('response_models', []):
      resp_models[model.get('content_type')] = model.get('model', 'Empty')
    kwargs['responseModels'] = resp_models
    args.append(kwargs)

  return args

def put_integration_response(params):
  args = []

  for ir_params in params.get('integration_responses', []):
    kwargs = dict(
      restApiId=params.get('rest_api_id'),
      resourceId=params.get('resource_id'),
      httpMethod=params.get('name'),
      statusCode=str(ir_params.get('status_code')),
      selectionPattern='' if 'is_default' in ir_params and ir_params['is_default'] else ir_params.get('pattern')
    )
    kwargs['responseParameters'] = param_transformer(ir_params.get('response_params', []), 'response')
    kwargs['responseTemplates'] = add_templates(ir_params.get('response_templates', []))
    args.append(kwargs)

  return args

def add_templates(params):
  resp = {}
  for p in params:
    resp[p.get('content_type')] = p.get('template')

  return resp

def add_optional_params(params, args_dict, optional_args):
  for arg in optional_args:
    if arg in params:
      args_dict[optional_args[arg]] = params.get(arg)

def param_transformer(params_list, type):
  params = {}

  for param in params_list:
    key = "method.{0}.{1}.{2}".format(type, param['location'], param['name'])
    if 'param_required' in param:
      params[key] = param['param_required']
    elif 'value' in param:
      params[key] = param['value']

  return params


class ApiGwMethod:
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
    return dict(
        name=dict(
          required=True,
          choices=['GET', 'PUT', 'POST', 'DELETE', 'PATCH', 'HEAD', 'ANY', 'OPTIONS'],
          aliases=['method']
        ),
        rest_api_id=dict(required=True),
        resource_id=dict(required=True),
        authorization_type=dict(required=False, default='NONE'),
        authorizer_id=dict(required=False),
        api_key_required=dict(required=False, type='bool', default=False),
        request_params=dict(
          type='list',
          required=False,
          default=[],
          name=dict(required=True),
          location=dict(required=True, choices=['querystring', 'path', 'header']),
          param_required=dict(type='bool')
        ),
        method_integration=dict(
          type='dict',
          default={},
          integration_type=dict(
            required=False,
            default='AWS',
            choices=['AWS', 'MOCK', 'HTTP', 'HTTP_PROXY', 'AWS_PROXY']
          ),
          http_method=dict(required=False, default='POST', choices=['POST', 'GET', 'PUT']),
          uri=dict(required=False),
          passthrough_behavior=dict(
            required=False,
            default='when_no_templates',
            choices=['when_no_templates', 'when_no_match', 'never']
          ),
          request_templates=dict(
            required=False,
            type='list',
            default=[],
            content_type=dict(required=True),
            template=dict(required=True)
          ),
          cache_namespace=dict(required=False, default=''),
          cache_key_parameters=dict(required=False, type='list', default=[]),
          integration_params=dict(
            type='list',
            required=False,
            default=[],
            name=dict(required=True),
            location=dict(required=True, choices=['querystring', 'path', 'header']),
            value=dict(required=True)
          )
        ),
        method_responses=dict(
          type='list',
          default=[],
          status_code=dict(required=True),
          response_models=dict(
            type='list',
            required=False,
            default=[],
            content_type=dict(required=True),
            model=dict(required=False, default='Empty', choices=['Empty', 'Error'])
          )
        ),
        integration_responses=dict(
          type='list',
          default=[],
          status_code=dict(required=True),
          is_default=dict(required=False, default=False, type='bool'),
          pattern=dict(required=False),
          response_params=dict(
            type='list',
            required=False,
            default=[],
            name=dict(required=True),
            location=dict(required=True, choices=['body', 'header']),
            value=dict(required=True)
          ),
          response_templates=dict(
            required=False,
            type='list',
            default=[],
            content_type=dict(required=True),
            template=dict(required=True)
          ),
        ),
        state=dict(default='present', choices=['present', 'absent'])
    )

  def validate_params(self):
    """
    Validate the module's argument spec for illegal combinations of arguments
    Throws InvalidInputError for any issues
    :return: Returns nothing
    """
    p = self.module.params
    if p['state'] == 'present':
      for param in ['method_integration', 'method_responses', 'integration_responses']:
        if param not in p:
          raise InvalidInputError(param, "'{}' must be provided when 'state' is present".format(param))

    if p['authorization_type'] == 'CUSTOM' and 'authorizer_id' not in p:
      raise InvalidInputError('authorizer_id', "authorizer_id must be provided when authorization_type is 'CUSTOM'")

    if p['method_integration']['integration_type'] in ['AWS', 'HTTP']:
      if 'http_method' not in p['method_integration']:
        raise InvalidInputError('method_integration', "http_method must be provided when integration_type is 'AWS' or 'HTTP'")
      elif 'uri' not in p['method_integration']:
        raise InvalidInputError('method_integration', "uri must be provided when integration_type is 'AWS' or 'HTTP'")

    for ir in p['integration_responses']:
      if 'is_default' in ir and ir['is_default'] and 'pattern' in ir:
        raise InvalidInputError('integration_responses', "'pattern' must not be provided when 'is_default' is True")
      elif 'pattern' not in ir and ('is_default' not in ir or not ir['is_default']):
        raise InvalidInputError('integration_responses', "'pattern' must be provided when 'is_default' is False")


  def _find_method(self):
    """
    Execute a find to determine if the method exists
    :return: Returns result of find or exits with fail_json
    """
    p = self.module.params

    try:
      response = self.client.get_method(
          restApiId=p.get('rest_api_id'),
          resourceId=p.get('resource_id'),
          httpMethod=p.get('name')
      )
      return response
    except ClientError as e:
      if 'NotFoundException' in e.message:
        return None
      else:
        self.module.fail_json(msg='Error calling boto3 get_method: {}'.format(e))
    except BotoCoreError as e:
      self.module.fail_json(msg='Error calling boto3 get_method: {}'.format(e))

  def _delete_method(self):
    """
    Delete the method
    :return: nothing
    """
    if not self.module.check_mode:
      try:
        self.client.delete_method(
          restApiId=self.module.params.get('rest_api_id'),
          resourceId=self.module.params.get('resource_id'),
          httpMethod=self.module.params.get('name')
        )
      except BotoCoreError as e:
        self.module.fail_json(msg="Error calling boto3 delete_method: {}".format(e))

  def _create_method(self):
    """
    Create or update the method
    :return: nothing
    """
    response = None
    changed = True
    if not self.module.check_mode:
      try:
        self.client.put_method(**put_method(self.module.params))
        self.client.put_integration(**put_integration(self.module.params))
        for args in put_method_response(self.module.params):
          self.client.put_method_response(**args)
        for args in put_integration_response(self.module.params):
          self.client.put_integration_response(**args)
        response = self._find_method()
      except BotoCoreError as e:
        self.module.fail_json(msg="Error while creating method via boto3: {}".format(e))

    return changed, response

  def _update_method(self):
    response = None
    changed = False

    try:
        um_args = update_method(self.method, self.module.params)
        if um_args:
          changed = True
          if not self.module.check_mode:
            self.client.update_method(**um_args)

        if 'methodIntegration' not in self.method:
          self.client.put_integration(**put_integration(self.module.params))
        else:
          ui_args = update_integration(self.method, self.module.params)
          self.client.update_integration(**ui_args)
    except BotoCoreError as e:
      self.module.fail_json(msg="Error while updating method via boto3: {}".format(e))

    return changed, response

  def process_request(self):
    """
    Process the user's request -- the primary code path
    :return: Returns either fail_json or exit_json
    """
    self.method = self._find_method()

    changed = False
    response = None

    if self.method is not None and self.module.params.get('state') == 'absent':
      self._delete_method()
      changed = True
    elif self.module.params.get('state') == 'present' and self.method is None:
      (changed, response) = self._create_method()
    elif self.module.params.get('state') == 'present':
      (changed, response) = self._update_method()

    self.module.exit_json(changed=changed, method=response)

def main():
    """
    Instantiates the module and calls process_request.
    :return: none
    """
    module = AnsibleModule(
        argument_spec=ApiGwMethod._define_module_argument_spec(),
        supports_check_mode=True
    )

    rest_api = ApiGwMethod(module)
    rest_api.process_request()

from ansible.module_utils.basic import *  # pylint: disable=W0614
if __name__ == '__main__':
    main()
