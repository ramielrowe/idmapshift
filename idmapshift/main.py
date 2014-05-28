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
import os

NOBODY_ID = 65534

UID_MAPPINGS = dict()
GID_MAPPINGS = dict()


def find_target_id(id, mappings, nobody, memo):
    if len(mappings) == 0:
        return -1
    if id not in memo:
        for start, target, count in mappings:
            if start <= id < count:
                memo[id] = (id-start) + target
    if id not in memo:
        memo[id] = nobody
    return memo[id]


def find_target_uid(id, mappings, nobody):
    return find_target_id(id, mappings, nobody, UID_MAPPINGS)


def find_target_gid(id, mappings, nobody):
    return find_target_id(id, mappings, nobody, GID_MAPPINGS)


def print_chown(path, uid, gid, target_uid, target_gid):
    print('%s %s:%s -> %s:%s' % (path, uid, gid, target_uid, target_gid))


def shift_path(path, uid_mappings, gid_mappings, nobody,
               dry_run=False, verbose=False):
    uid = os.lstat(path).st_uid
    gid = os.lstat(path).st_gid
    target_uid = find_target_uid(uid, uid_mappings, nobody)
    target_gid = find_target_uid(gid, gid_mappings, nobody)
    if verbose:
        print_chown(path, uid, gid, target_uid, target_gid)
    if not dry_run:
        os.lchown(path, target_uid, target_gid)


def shift_dir(dir, uid_mappings, gid_mappings, nobody,
              dry_run=False, verbose=False):
    for root, dirs, files in os.walk(dir):
        for dir in dirs:
            path = os.path.join(root, dir)
            shift_path(path, uid_mappings, gid_mappings, nobody,
                       dry_run=dry_run, verbose=verbose)
        for file in files:
            path = os.path.join(root, file)
            shift_path(path, uid_mappings, gid_mappings, nobody,
                       dry_run=dry_run, verbose=verbose)


def id_map_type(val):
    maps = val.split(',')
    id_maps = []
    for map in maps:
        map_vals = map.split(':')

        if len(map_vals) != 3:
            msg = 'Invalid id map %s, correct syntax is guest-id:host-id:count.'
            raise argparse.ArgumentTypeError(msg % val)

        try:
            vals = [int(i) for i in map_vals]
        except ValueError:
            msg = 'Invalid id map %s, values must be integers' % val
            raise argparse.ArgumentTypeError(msg)

        id_maps.append((vals[0], vals[1], vals[2]))
    return id_maps


def main():
    parser = argparse.ArgumentParser('User Namespace FS Owner Shift')
    parser.add_argument('path')
    parser.add_argument('-u', '--uid', type=id_map_type, default=[])
    parser.add_argument('-g', '--gid', type=id_map_type, default=[])
    parser.add_argument('-n', '--nobody', default=NOBODY_ID, type=int)
    parser.add_argument('-d', '--dry-run', action='store_true')
    parser.add_argument('-v', '--verbose', action='store_true')
    args = parser.parse_args()

    shift_dir(args.path, args.uid, args.gid, args.nobody,
              dry_run=args.dry_run, verbose=args.verbose)
