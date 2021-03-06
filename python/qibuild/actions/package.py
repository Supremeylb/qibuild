## Copyright (c) 2012-2016 Aldebaran Robotics. All rights reserved.
## Use of this source code is governed by a BSD-style license that can be
## found in the COPYING file.

""" Generate a binary package, ready to be added in a toolchain """

import os
import re
import sys

from qisys.qixml import etree
from qisys import ui
import qisys.archive
import qisys.sh
import qibuild.parsers

ARCHIVE_SUFFIX = ".zip"

def configure_parser(parser):
    """Configure parser for this action"""
    qibuild.parsers.cmake_configure_parser(parser)
    qibuild.parsers.cmake_build_parser(parser)
    qibuild.parsers.project_parser(parser)
    group = parser.add_argument_group("package options")
    group.add_argument("--standalone", action="store_true",
                       help="Make a standalone package (i.e, include all dependencies")
    group.add_argument("--breakpad", action="store_true",
                       help="Generate breakpad symbols. "
                            "(Force CMAKE_BUILD_TYPE=RelWithDebInfo)")
    group.add_argument("--version",
                       help="Set project version. Override settings in qiproject.xml")
    group.add_argument("--output",
                       help="Filename where the package will be stored. Must end in '{}'"
                            .format(ARCHIVE_SUFFIX))

def do(args):
    """Main entry point"""
    standalone = args.standalone
    breakpad = args.breakpad
    cmake_builder = qibuild.parsers.get_cmake_builder(args)
    if breakpad:
        cmake_builder.build_config.build_type = "RelWithDebInfo"

    projects = cmake_builder.projects
    if len(projects) != 1:
        ui.fatal("This action can only work on one project")
    project = projects[0]

    archive_name = project.name
    version = args.version
    if version:
        project.version = version
    else:
        version = project.version
        if not version:
            version = "0.1"

    if not version:
        ui.warning("Could not find project version!",
                   "Either use --version or fix qiproject.xml",
                   sep="\n")
    if version:
        archive_name += "-" + version
    archive_suffix = args.config
    if archive_suffix:
        archive_name += "-" + archive_suffix

    build_prefix = cmake_builder.build_config.build_prefix or ""
    package_dir = os.path.join(cmake_builder.build_worktree.root,
                               build_prefix,
                               "package")
    destdir = os.path.join(package_dir, archive_name)

    if args.output:
        if not args.output.endswith(ARCHIVE_SUFFIX):
            ui.fatal("The output filename should end with {}".format(ARCHIVE_SUFFIX))

        output = args.output
    else:
        output = destdir + ARCHIVE_SUFFIX

    # Clean the destdir just in case the package was already generated
    qisys.sh.rm(destdir)

    build_type = cmake_builder.build_config.build_type
    # Also build in debug on windows when building a package for a toolchain
    if sys.platform.startswith("win") and not standalone:
        _do_package(cmake_builder, destdir, build_type="Debug", standalone=False)
    _do_package(cmake_builder, destdir, build_type=build_type, standalone=standalone)

    package_xml_path = os.path.join(destdir, "package.xml")
    project.gen_package_xml(package_xml_path)

    if breakpad:
        symbols_archive_name = archive_name + "-symbols.zip"
        symbols_archive = os.path.join(package_dir, symbols_archive_name)
        with qisys.sh.TempDir() as tmp:
            pool_dir = os.path.join(tmp, "symbols")
            qibuild.breakpad.dump_symbols_from_directory(destdir, pool_dir)
            qisys.archive.compress(pool_dir, flat=True, output=symbols_archive)


    ui.info(ui.blue, "::", ui.reset, ui.bold, "Compressing package ...")
    flat = not standalone
    archive = qisys.archive.compress(destdir,
                                     algo="zip", quiet=True, flat=flat,
                                     output=output)

    # Clean up after ourselves
    qisys.sh.rm(destdir)
    ui.info(ui.green, "Package generated in", ui.reset, ui.bold, archive)

    if breakpad:
        ui.info(ui.green, "Symbols package generated in", ui.reset, ui.bold,
                symbols_archive)
        return archive, symbols_archive
    else:
        return archive


def _do_package(cmake_builder, destdir, build_type="Release", standalone=False):
    """ Helper function. On linux and mac this is only called
    once.

    On Windows this is called twice, both in debug and release
    This is because usually debug and release version of a library
    are incompatible on Windows.

    """
    cmake_builder.build_config.build_type = build_type

    cmake_builder.dep_types = ["build"]
    ui.info(ui.blue, "::", ui.reset, ui.bold, "Configuring ... (%s)" % build_type)
    cmake_builder.configure()
    ui.info(ui.blue, "::", ui.reset, ui.bold, "Building    ... (%s)" % build_type)
    cmake_builder.build()
    if standalone:
        cmake_builder.dep_types = ["runtime"]
    else:
        cmake_builder.dep_types = list()
    ui.info(ui.blue, "::", ui.reset, ui.bold, "Installing  ... (%s)" % build_type)
    if standalone:
        cmake_builder.install(destdir, components=["runtime"])
    else:
        cmake_builder.install(destdir)
