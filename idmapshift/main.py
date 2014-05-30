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

import idmapshift

NOBODY_ID = 65534


def id_map_type(val):
    maps = val.split(',')
    id_maps = []
    for m in maps:
        map_vals = m.split(':')

        if len(map_vals) != 3:
            msg = ('Invalid id map %s, correct syntax is '
                   'guest-id:host-id:count.')
            raise argparse.ArgumentTypeError(msg % val)

        try:
            vals = [int(i) for i in map_vals]
        except ValueError:
            msg = 'Invalid id map %s, values must be integers' % val
            raise argparse.ArgumentTypeError(msg)

        id_maps.append(tuple(vals))
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

    idmapshift.shift_dir(args.path, args.uid, args.gid, args.nobody,
                         dry_run=args.dry_run, verbose=args.verbose)
