## Copyright (c) 2012 Aldebaran Robotics. All rights reserved.
## Use of this source code is governed by a BSD-style license that can be
## found in the COPYING file.

""" List the name and paths of every project
"""

import os
import sys
import qibuild.log

LOGGER = qibuild.log.get_logger(__name__)

import qisrc
import qibuild


def configure_parser(parser):
    """Configure parser for this action """
    qibuild.parsers.worktree_parser(parser)

def do(args):
    """ Main method """
    qiwt = qisrc.open_worktree(args.worktree)
    print "Projects in :", qiwt.root
    print
    for project in qiwt.projects:
       print project.src
