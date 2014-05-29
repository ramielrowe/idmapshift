# IDMapShift #

[![Build Status](https://travis-ci.org/ramielrowe/idmapshift.svg?branch=master)](https://travis-ci.org/ramielrowe/idmapshift)

IDMapShift is a tool that properly sets the ownership of a filesystem for use with linux user namespaces.

### Usage ###


    idmapshift -u [[guest-uid:host-uid:count],...] -g [[guest-gid:host-gid:count],...] path
