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
import os


def find_target_id(id, mappings, nobody, memo):
    if len(mappings) == 0:
        return -1
    if id not in memo:
        for start, target, count in mappings:
            if start <= id < count:
                memo[id] = (id - start) + target
    if id not in memo:
        memo[id] = nobody
    return memo[id]


def find_target_uid(id, mappings, nobody, memo):
    return find_target_id(id, mappings, nobody, memo)


def find_target_gid(id, mappings, nobody, memo):
    return find_target_id(id, mappings, nobody, memo)


def print_chown(path, uid, gid, target_uid, target_gid):
    print('%s %s:%s -> %s:%s' % (path, uid, gid, target_uid, target_gid))


def shift_path(path, uid_mappings, gid_mappings, nobody, uid_memo, gid_memo,
               dry_run=False, verbose=False):
    uid = os.lstat(path).st_uid
    gid = os.lstat(path).st_gid
    target_uid = find_target_uid(uid, uid_mappings, nobody, uid_memo)
    target_gid = find_target_gid(gid, gid_mappings, nobody, gid_memo)
    if verbose:
        print_chown(path, uid, gid, target_uid, target_gid)
    if not dry_run:
        os.lchown(path, target_uid, target_gid)


def shift_dir(dir, uid_mappings, gid_mappings, nobody,
              dry_run=False, verbose=False):
    uid_memo = dict()
    gid_memo = dict()
    for root, dirs, files in os.walk(dir):
        for dir in dirs:
            path = os.path.join(root, dir)
            shift_path(path, uid_mappings, gid_mappings, nobody,
                       dry_run=dry_run, verbose=verbose,
                       uid_memo=uid_memo, gid_memo=gid_memo)
        for file in files:
            path = os.path.join(root, file)
            shift_path(path, uid_mappings, gid_mappings, nobody,
                       dry_run=dry_run, verbose=verbose,
                       uid_memo=uid_memo, gid_memo=gid_memo)
