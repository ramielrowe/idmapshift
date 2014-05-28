# Copyright 2014 Rackspace, Andrew Melton
#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import argparse
import mock
import unittest

from idmapshift import main


class FakeStat(object):
    def __init__(self, uid, gid):
        self.st_uid = uid
        self.st_gid = gid


class BaseTestCase(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(BaseTestCase, self).__init__(*args, **kwargs)
        self.uid_maps = [(0, 10000, 10), (10, 20000, 1000)]
        self.gid_maps = [(0, 10000, 10), (10, 20000, 1000)]


class FindTargetIDTestCase(BaseTestCase):
    def test_find_target_id_range_1_first(self):
        actual_target = main.find_target_id(0, self.uid_maps,
                                            main.NOBODY_ID, dict())
        self.assertEqual(10000, actual_target)

    def test_find_target_id_inside_range_1(self):
        actual_target = main.find_target_id(2, self.uid_maps,
                                            main.NOBODY_ID, dict())
        self.assertEqual(10002, actual_target)

    def test_find_target_id_range_2_first(self):
        actual_target = main.find_target_id(10, self.uid_maps,
                                            main.NOBODY_ID, dict())
        self.assertEqual(20000, actual_target)

    def test_find_target_id_inside_range_2(self):
        actual_target = main.find_target_id(100, self.uid_maps,
                                            main.NOBODY_ID, dict())
        self.assertEqual(20090, actual_target)

    def test_find_target_id_outside_range(self):
        actual_target = main.find_target_id(10000, self.uid_maps,
                                            main.NOBODY_ID, dict())
        self.assertEqual(main.NOBODY_ID, actual_target)

    def test_find_target_id_no_mappings(self):
        actual_target = main.find_target_id(0, [],
                                            main.NOBODY_ID, dict())
        self.assertEqual(-1, actual_target)

    def test_find_target_id_updates_memo(self):
        memo = dict()
        main.find_target_id(0, self.uid_maps, main.NOBODY_ID, memo)
        self.assertTrue(0 in memo)
        self.assertEqual(10000, memo[0])

    def test_find_target_id_in_memo(self):
        mock_maps = mock.MagicMock()
        mock_maps.__len__.return_value = 1
        actual_target = main.find_target_id(0, mock_maps,
                                            main.NOBODY_ID, {0: 100})
        self.assertEqual(1, len(mock_maps.mock_calls))
        mock_maps.__len__.assert_has_calls([mock.call()])
        self.assertEqual(100, actual_target)

    @mock.patch('idmapshift.main.find_target_id')
    def test_find_target_uid_uses_uid_memo(self, mock_ftid):
        main.find_target_uid(0, self.uid_maps, main.NOBODY_ID)
        self.assertEqual(1, len(mock_ftid.mock_calls))
        args, kwargs = mock_ftid.call_args
        self.assertIs(main.UID_MAPPINGS, args[3])

    @mock.patch('idmapshift.main.find_target_id')
    def test_find_target_gid_uses_gid_memo(self, mock_ftid):
        main.find_target_gid(0, self.gid_maps, main.NOBODY_ID)
        self.assertEqual(1, len(mock_ftid.mock_calls))
        args, kwargs = mock_ftid.call_args
        self.assertIs(main.GID_MAPPINGS, args[3])


class ShiftPathTestCase(BaseTestCase):
    @mock.patch('os.lchown')
    @mock.patch('os.lstat')
    def test_shift_path(self, mock_lstat, mock_lchown):
        mock_lstat.return_value = FakeStat(0, 0)
        main.shift_path('/test/path', self.uid_maps, self.gid_maps,
                        main.NOBODY_ID)
        mock_lstat.assert_has_calls([mock.call('/test/path')])
        mock_lchown.assert_has_calls([mock.call('/test/path', 10000, 10000)])

    @mock.patch('os.lchown')
    @mock.patch('os.lstat')
    def test_shift_path_dry_run(self, mock_lstat, mock_lchown):
        mock_lstat.return_value = FakeStat(0, 0)
        main.shift_path('/test/path', self.uid_maps, self.gid_maps,
                        main.NOBODY_ID, dry_run=True)
        mock_lstat.assert_has_calls([mock.call('/test/path')])
        self.assertEqual(0, len(mock_lchown.mock_calls))

    @mock.patch('os.lchown')
    @mock.patch('idmapshift.main.print_chown')
    @mock.patch('os.lstat')
    def test_shift_path_verbose(self, mock_lstat, mock_print, mock_lchown):
        mock_lstat.return_value = FakeStat(0, 0)
        main.shift_path('/test/path', self.uid_maps, self.gid_maps,
                        main.NOBODY_ID, verbose=True)
        mock_lstat.assert_has_calls([mock.call('/test/path')])
        mock_print_call = mock.call('/test/path', 0, 0, 10000, 10000)
        mock_print.assert_has_calls([mock_print_call])
        mock_lchown.assert_has_calls([mock.call('/test/path', 10000, 10000)])


class ShiftDirTestCase(BaseTestCase):
    @mock.patch('idmapshift.main.shift_path')
    @mock.patch('os.path.join')
    @mock.patch('os.walk')
    def test_shift_dir(self, mock_walk, mock_join, mock_shift_path):
        mock_walk.return_value = [('/', ['a', 'b'], ['c', 'd'])]
        mock_join.side_effect = lambda f, *args: f + '/'.join(args)

        main.shift_dir('/', self.uid_maps, self.gid_maps, main.NOBODY_ID)

        files = ['a', 'b', 'c', 'd']
        mock_walk.assert_has_calls([mock.call('/')])
        mock_join_calls = [mock.call('/', x) for x in files]
        mock_join.assert_has_calls(mock_join_calls)

        args = (self.uid_maps, self.gid_maps, main.NOBODY_ID)
        kwargs = dict(dry_run=False, verbose=False)
        shift_path_calls = [mock.call('/' + x, *args, **kwargs) for x in files]
        mock_shift_path.assert_has_calls(shift_path_calls)

    @mock.patch('idmapshift.main.shift_path')
    @mock.patch('os.path.join')
    @mock.patch('os.walk')
    def test_shift_dir_dry_run(self, mock_walk, mock_join, mock_shift_path):
        mock_walk.return_value = [('/', ['a', 'b'], ['c', 'd'])]
        mock_join.side_effect = lambda f, *args: f + '/'.join(args)

        main.shift_dir('/', self.uid_maps, self.gid_maps, main.NOBODY_ID,
                       dry_run=True)

        mock_walk.assert_has_calls([mock.call('/')])

        files = ['a', 'b', 'c', 'd']
        mock_join_calls = [mock.call('/', x) for x in files]
        mock_join.assert_has_calls(mock_join_calls)

        args = (self.uid_maps, self.gid_maps, main.NOBODY_ID)
        kwargs = dict(dry_run=True, verbose=False)
        shift_path_calls = [mock.call('/' + x, *args, **kwargs) for x in files]
        mock_shift_path.assert_has_calls(shift_path_calls)


class IDMapTypeTestCase(unittest.TestCase):
    def test_id_map_type(self):
        result = main.id_map_type("1:1:1,2:2:2")
        self.assertEqual([(1, 1, 1), (2, 2, 2)], result)

    def test_id_map_type_not_int(self):
        self.assertRaises(argparse.ArgumentTypeError, main.id_map_type,
                          "a:1:1")

    def test_id_map_type_not_proper_format(self):
        self.assertRaises(argparse.ArgumentTypeError, main.id_map_type,
                          "1:1")


class MainTestCase(BaseTestCase):
    @mock.patch('idmapshift.main.shift_dir')
    @mock.patch('argparse.ArgumentParser')
    def test_main(self, mock_parser_class, mock_shift_dir):
        mock_parser = mock.MagicMock()
        mock_parser.parse_args.return_value = mock_parser
        mock_parser.path = '/test/path'
        mock_parser.uid = self.uid_maps
        mock_parser.gid = self.gid_maps
        mock_parser.nobody = main.NOBODY_ID
        mock_parser.dry_run = False
        mock_parser.verbose = False
        mock_parser_class.return_value = mock_parser
        main.main()
        mock_shift_dir_call = mock.call('/test/path', self.uid_maps,
                                        self.gid_maps, main.NOBODY_ID,
                                        dry_run=False, verbose=False)
        mock_shift_dir.assert_has_calls([mock_shift_dir_call])
