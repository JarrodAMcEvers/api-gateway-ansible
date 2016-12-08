#!/usr/bin/python
# TODO: License goes here

import library.apigw_base_path_mapping as apigw_base_path_mapping
from library.apigw_base_path_mapping import ApiGwBasePathMapping
import mock
from mock import patch
from mock import create_autospec
from mock import ANY
import unittest
import boto
from botocore.exceptions import BotoCoreError

class TestApiGwBasePathMapping(unittest.TestCase):

  def setUp(self):
    self.module = mock.MagicMock()
    self.module.check_mode = False
    self.module.exit_json = mock.MagicMock()
    self.module.fail_json = mock.MagicMock()
    self.bpm  = ApiGwBasePathMapping(self.module)
    self.bpm.client = mock.MagicMock()
    self.bpm.module.params = {
      'name': 'testify',
      'rest_api_id': 'rest_id',
      'stage': 'test_stage',
      'state': 'present',
    }
    reload(apigw_base_path_mapping)

  def test_boto_module_not_found(self):
    # Setup Mock Import Function
    import __builtin__ as builtins
    real_import = builtins.__import__

    def mock_import(name, *args):
      if name == 'boto': raise ImportError
      return real_import(name, *args)

    with mock.patch('__builtin__.__import__', side_effect=mock_import):
      reload(apigw_base_path_mapping)
      ApiGwBasePathMapping(self.module)

    self.module.fail_json.assert_called_with(msg='boto and boto3 are required for this module')

  def test_boto3_module_not_found(self):
    # Setup Mock Import Function
    import __builtin__ as builtins
    real_import = builtins.__import__

    def mock_import(name, *args):
      if name == 'boto3': raise ImportError
      return real_import(name, *args)

    with mock.patch('__builtin__.__import__', side_effect=mock_import):
      reload(apigw_base_path_mapping)
      ApiGwBasePathMapping(self.module)

    self.module.fail_json.assert_called_with(msg='boto and boto3 are required for this module')

  @patch.object(apigw_base_path_mapping, 'boto3')
  def test_boto3_client_properly_instantiated(self, mock_boto):
    ApiGwBasePathMapping(self.module)
    mock_boto.client.assert_called_once_with('apigateway')


  def test_define_argument_spec(self):
    result = ApiGwBasePathMapping._define_module_argument_spec()
    self.assertIsInstance(result, dict)
    self.assertEqual(result, dict(
                     name=dict(required=True, aliases=['domain_name']),
                     rest_api_id=dict(required=False),
                     stage=dict(required=False),
                     base_path=dict(required=False, default='(none)'),
                     state=dict(default='present', choices=['present', 'absent']),
    ))

  @patch.object(apigw_base_path_mapping, 'AnsibleModule')
  @patch.object(apigw_base_path_mapping, 'ApiGwBasePathMapping')
  def test_main(self, mock_ApiGwBasePathMapping, mock_AnsibleModule):
    mock_ApiGwBasePathMapping_instance      = mock.MagicMock()
    mock_AnsibleModule_instance     = mock.MagicMock()
    mock_ApiGwBasePathMapping.return_value  = mock_ApiGwBasePathMapping_instance
    mock_AnsibleModule.return_value = mock_AnsibleModule_instance

    apigw_base_path_mapping.main()

    mock_ApiGwBasePathMapping.assert_called_once_with(mock_AnsibleModule_instance)
    assert mock_ApiGwBasePathMapping_instance.process_request.call_count == 1


if __name__ == '__main__':
    unittest.main()
