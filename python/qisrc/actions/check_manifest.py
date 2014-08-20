""" Apply changes from a manifest xml path.

Useful to check everything is ok before pushing the manifest

"""

from qisys import ui
import qisrc.parsers

import sys

def configure_parser(parser):
    qisrc.parsers.worktree_parser(parser)
    parser.add_argument("xml_path")

def do(args):
    git_worktree = qisrc.parsers.get_git_worktree(args)
    ok = git_worktree.check_manifest(args.xml_path)
    if not ok:
        sys.exit(1)