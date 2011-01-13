##
## Author(s):
##  - Cedric GESTES <gestes@aldebaran-robotics.com>
##  - Dimitri Merejkowsky <dmerejkowsy@aldebaran-robotics.com>
##
## Copyright (C) 2010, 2011 Aldebaran Robotics
##

"""Configure a project

"""

import logging
import qibuild
import qitools

def configure_parser(parser):
    """Configure parser for this action"""
    qibuild.parsers.toc_parser(parser)
    qibuild.parsers.build_parser(parser)
    qibuild.parsers.project_parser(parser)
    group = parser.add_argument_group("cmake arguments")
    group.add_argument("--bootstrap", dest="bootstrap", action="store_true", help="only bootstrap projects, do not call cmake.")
    group.add_argument("--build-directory", dest="build_directory", action="store", help="override the default build directory used by cmake")
    group.add_argument("-D", dest="cmake_flags", action="append", help="additional cmake flags")

def do(args):
    """Main entry point"""
    if args.build_directory and not args.single:
        raise Exception("You should use --single when specifying a build directory")

    logger   = logging.getLogger(__name__)
    toc      = qibuild.toc.open(args.work_tree, args, use_env=True)

    (project_names, _, _) = qibuild.toc.resolve_deps(toc, args)

    projects = [toc.get_project(name) for name in project_names]
    if args.build_directory:
        projects[0].set_custom_build_directory(args.build_directory)

    for project_name in project_names:
        logger.info("Bootstraping [%s]", project_name)
        dep_sdk_dirs = toc.get_sdk_dirs(project_name)
        qibuild.project.bootstrap(toc.get_project(project_name), dep_sdk_dirs)

    if args.bootstrap:
        return
    for project in projects:
        logger.info("Configuring %s in %s", project.name, toc.build_folder_name)
        toc.configure_project(project)


