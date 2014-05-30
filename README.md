# IDMapShift #

[![Build Status](https://travis-ci.org/ramielrowe/idmapshift.svg?branch=master)](https://travis-ci.org/ramielrowe/idmapshift)

IDMapShift is a tool that properly sets the ownership of a filesystem for use with linux user namespaces.

### Usage ###


    idmapshift -u [[guest-uid:host-uid:count],...] -g [[guest-gid:host-gid:count],...] path

### Purpose ###

When using user namespaces with linux containers, the filesystem of the container must be owned by the targeted user and group ids being applied to that container. Otherwise, processes inside the container won't be able to access the filesystem. 

For example, when using the id map string '0:10000:2000', this means that user ids inside the container between 0 and 1999 will map to user ids on the host between 10000 and 11999. Root (0) becomes 10000, user 1 becomes 10001, user 50 becomes 10050 and user 1999 becomes 11999. This means that files that are owned by root need to actually be owned by user 10000, and files owned by 50 need to be owned by 10050, and so on.


IDMapShift will take the uid and gid strings used for user namespaces and properly set up the filesystem for use by those users. Uids and gids outside of provided ranges will be mapped to nobody (max uid/gid) so that they are inaccessible inside the container.
