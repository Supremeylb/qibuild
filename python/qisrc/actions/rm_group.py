""" Add a group to the current worktree

"""

from qisys import ui
import qisrc.parsers

import sys
import copy

def configure_parser(parser):
    qisrc.parsers.worktree_parser(parser)
    parser.add_argument("group")


def do(args):
    git_worktree = qisrc.parsers.get_git_worktree(args)
    manifest = git_worktree.manifest
    groups = copy.copy(git_worktree.manifest.groups)
    groups.remove(args.group)
    git_worktree.configure_manifest(manifest.url, groups=groups,
                                    branch=manifest.branch)
