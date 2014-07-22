# Copyright 2014 Rackspace, Andrew Melton
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import mock
import unittest

import idmapshift
from idmapshift import main


def join_side_effect(root, *args):
    path = root
    if root != '/':
        path += '/'
    path += '/'.join(args)
    return path


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
        actual_target = idmapshift.find_target_id(0, self.uid_maps,
                                                  main.NOBODY_ID, dict())
        self.assertEqual(10000, actual_target)

    def test_find_target_id_inside_range_1(self):
        actual_target = idmapshift.find_target_id(2, self.uid_maps,
                                                  main.NOBODY_ID, dict())
        self.assertEqual(10002, actual_target)

    def test_find_target_id_range_2_first(self):
        actual_target = idmapshift.find_target_id(10, self.uid_maps,
                                                  main.NOBODY_ID, dict())
        self.assertEqual(20000, actual_target)

    def test_find_target_id_inside_range_2(self):
        actual_target = idmapshift.find_target_id(100, self.uid_maps,
                                                  main.NOBODY_ID, dict())
        self.assertEqual(20090, actual_target)

    def test_find_target_id_outside_range(self):
        actual_target = idmapshift.find_target_id(10000, self.uid_maps,
                                                  main.NOBODY_ID, dict())
        self.assertEqual(main.NOBODY_ID, actual_target)

    def test_find_target_id_no_mappings(self):
        actual_target = idmapshift.find_target_id(0, [],
                                                  main.NOBODY_ID, dict())
        self.assertEqual(-1, actual_target)

    def test_find_target_id_updates_memo(self):
        memo = dict()
        idmapshift.find_target_id(0, self.uid_maps, main.NOBODY_ID, memo)
        self.assertTrue(0 in memo)
        self.assertEqual(10000, memo[0])

    def test_find_target_id_in_memo(self):
        mock_maps = mock.MagicMock()
        mock_maps.__len__.return_value = 1
        actual_target = idmapshift.find_target_id(0, mock_maps,
                                                  main.NOBODY_ID, {0: 100})
        self.assertEqual(1, len(mock_maps.mock_calls))
        mock_maps.__len__.assert_has_calls([mock.call()])
        self.assertEqual(100, actual_target)


class ShiftPathTestCase(BaseTestCase):
    @mock.patch('os.lchown')
    @mock.patch('os.lstat')
    def test_shift_path(self, mock_lstat, mock_lchown):
        mock_lstat.return_value = FakeStat(0, 0)
        idmapshift.shift_path('/test/path', self.uid_maps, self.gid_maps,
                              main.NOBODY_ID, dict(), dict())
        mock_lstat.assert_has_calls([mock.call('/test/path')])
        mock_lchown.assert_has_calls([mock.call('/test/path', 10000, 10000)])

    @mock.patch('os.lchown')
    @mock.patch('os.lstat')
    def test_shift_path_dry_run(self, mock_lstat, mock_lchown):
        mock_lstat.return_value = FakeStat(0, 0)
        idmapshift.shift_path('/test/path', self.uid_maps, self.gid_maps,
                              main.NOBODY_ID, dict(), dict(), dry_run=True)
        mock_lstat.assert_has_calls([mock.call('/test/path')])
        self.assertEqual(0, len(mock_lchown.mock_calls))

    @mock.patch('os.lchown')
    @mock.patch('idmapshift.print_chown')
    @mock.patch('os.lstat')
    def test_shift_path_verbose(self, mock_lstat, mock_print, mock_lchown):
        mock_lstat.return_value = FakeStat(0, 0)
        idmapshift.shift_path('/test/path', self.uid_maps, self.gid_maps,
                              main.NOBODY_ID, dict(), dict(), verbose=True)
        mock_lstat.assert_has_calls([mock.call('/test/path')])
        mock_print_call = mock.call('/test/path', 0, 0, 10000, 10000)
        mock_print.assert_has_calls([mock_print_call])
        mock_lchown.assert_has_calls([mock.call('/test/path', 10000, 10000)])


class ShiftDirTestCase(BaseTestCase):
    @mock.patch('idmapshift.shift_path')
    @mock.patch('os.path.join')
    @mock.patch('os.walk')
    def test_shift_dir(self, mock_walk, mock_join, mock_shift_path):
        mock_walk.return_value = [('/', ['a', 'b'], ['c', 'd'])]
        mock_join.side_effect = join_side_effect

        idmapshift.shift_dir('/', self.uid_maps, self.gid_maps, main.NOBODY_ID)

        files = ['a', 'b', 'c', 'd']
        mock_walk.assert_has_calls([mock.call('/')])
        mock_join_calls = [mock.call('/', x) for x in files]
        mock_join.assert_has_calls(mock_join_calls)

        args = (self.uid_maps, self.gid_maps, main.NOBODY_ID)
        kwargs = dict(dry_run=False, verbose=False,
                      uid_memo=dict(), gid_memo=dict())
        shift_path_calls = [mock.call('/', *args, **kwargs)]
        shift_path_calls += [mock.call('/' + x, *args, **kwargs)
                             for x in files]
        mock_shift_path.assert_has_calls(shift_path_calls)

    @mock.patch('idmapshift.shift_path')
    @mock.patch('os.path.join')
    @mock.patch('os.walk')
    def test_shift_dir_dry_run(self, mock_walk, mock_join, mock_shift_path):
        mock_walk.return_value = [('/', ['a', 'b'], ['c', 'd'])]
        mock_join.side_effect = join_side_effect

        idmapshift.shift_dir('/', self.uid_maps, self.gid_maps, main.NOBODY_ID,
                             dry_run=True)

        mock_walk.assert_has_calls([mock.call('/')])

        files = ['a', 'b', 'c', 'd']
        mock_join_calls = [mock.call('/', x) for x in files]
        mock_join.assert_has_calls(mock_join_calls)

        args = (self.uid_maps, self.gid_maps, main.NOBODY_ID)
        kwargs = dict(dry_run=True, verbose=False,
                      uid_memo=dict(), gid_memo=dict())
        shift_path_calls = [mock.call('/', *args, **kwargs)]
        shift_path_calls += [mock.call('/' + x, *args, **kwargs)
                             for x in files]
        mock_shift_path.assert_has_calls(shift_path_calls)


class ConfirmPathTestCase(unittest.TestCase):
    def test_confirm_path(self):
        idmapshift.confirm_path()


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
    @mock.patch('idmapshift.shift_dir')
    @mock.patch('argparse.ArgumentParser')
    def test_main(self, mock_parser_class, mock_shift_dir):
        mock_parser = mock.MagicMock()
        mock_parser.parse_args.return_value = mock_parser
        mock_parser.confirm = False
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


class IntegrationTestCase(BaseTestCase):
    @mock.patch('os.lchown')
    @mock.patch('os.lstat')
    @mock.patch('os.path.join')
    @mock.patch('os.walk')
    def test_integrated_shift_dir(self, mock_walk, mock_join, mock_lstat,
                                  mock_lchown):
        mock_walk.return_value = [('/tmp/test', ['a', 'b', 'c'], ['d']),
                                  ('/tmp/test/d', ['1', '2'], [])]
        mock_join.side_effect = join_side_effect

        def lstat(path):
            stats = {
                't': FakeStat(0, 0),
                'a': FakeStat(0, 0),
                'b': FakeStat(0, 2),
                'c': FakeStat(30000, 30000),
                'd': FakeStat(100, 100),
                '1': FakeStat(0, 100),
                '2': FakeStat(100, 100),
            }
            return stats[path[-1]]

        mock_lstat.side_effect = lstat

        idmapshift.shift_dir('/tmp/test', self.uid_maps, self.gid_maps,
                             main.NOBODY_ID, verbose=True)

        lchown_calls = [
            mock.call('/tmp/test', 10000, 10000),
            mock.call('/tmp/test/a', 10000, 10000),
            mock.call('/tmp/test/b', 10000, 10002),
            mock.call('/tmp/test/c', main.NOBODY_ID, main.NOBODY_ID),
            mock.call('/tmp/test/d', 20090, 20090),
            mock.call('/tmp/test/d/1', 10000, 20090),
            mock.call('/tmp/test/d/2', 20090, 20090),
        ]
        mock_lchown.assert_has_calls(lchown_calls)

    @mock.patch('os.lchown')
    @mock.patch('os.lstat')
    @mock.patch('os.path.join')
    @mock.patch('os.walk')
    def test_integrated_shift_dir_dry_run(self, mock_walk, mock_join,
                                          mock_lstat, mock_lchown):
        mock_walk.return_value = [('/tmp/test', ['a', 'b', 'c'], ['d']),
                                  ('/tmp/test/d', ['1', '2'], [])]
        mock_join.side_effect = join_side_effect

        def lstat(path):
            stats = {
                't': FakeStat(0, 0),
                'a': FakeStat(0, 0),
                'b': FakeStat(0, 2),
                'c': FakeStat(30000, 30000),
                'd': FakeStat(100, 100),
                '1': FakeStat(0, 100),
                '2': FakeStat(100, 100),
            }
            return stats[path[-1]]

        mock_lstat.side_effect = lstat

        idmapshift.shift_dir('/tmp/test', self.uid_maps, self.gid_maps,
                             main.NOBODY_ID, dry_run=True, verbose=True)

        self.assertEqual(0, len(mock_lchown.mock_calls))
