## Copyright (C) 2011 Aldebaran Robotics

import os
import shlex
import logging

import qibuild.sh

LOGGER = logging.getLogger("qibuild.toc.project")

class Project:
    """ Store information about a project:
         - name
         - source directory
         - build directory
         - build configuration
         - dependencies
    """
    def __init__(self, name, directory):
        self.name            = name
        self.directory       = directory
        self.depends         = list()
        self.rdepends        = list()

        #build related flags
        self.cmake_flags     = list()
        self.build_directory = None
        self.sdk_directory   = None
        self._custom_sdk_dir = False

    def get_sdk_dir(self):
        """ Return the SDK dir of the project.
        To use the project build results, from an other project,
        you just have to add this directory to CMAKE_PREFIX_PATH

        """
        return os.path.join(self.build_directory, "sdk")

    def update_depends(self, toc):
        """ Update project dependency list """
        deps  = toc.configstore.get("project", self.name, "depends", default="").split()
        rdeps = toc.configstore.get("project", self.name, "rdepends", default="").split()
        self.depends.extend(deps)
        self.rdepends.extend(rdeps)

    def update_build_config(self, toc, build_directory_name):
        """ Update cmake_flags
           - add flags from the build_config (read in toc's configstore)
           - add flags from the project config (read in toc's configstore project section)
           - add flags from the command line (stored in toc.cmake_flags when toc is built)
        """

        #handle custom global build directory containing all projects
        singlebdir = toc.configstore.get("general", "build", "build_dir", default=None)
        if singlebdir:
            if not os.path.isabs(singlebdir):
                singlebdir = os.path.join(toc.work_tree, singlebdir)
            bname = os.path.join("build-%s" % (build_directory_name), self.name)
            self.build_directory = os.path.normpath(os.path.join(singlebdir, bname))
        else:
            bname = "build-%s" % (build_directory_name)
            self.build_directory = os.path.join(self.directory, bname)

        build_config_flags = toc.configstore.get("general", "build", "cmake", "flags",
            default=None)
        if build_config_flags:
            self.cmake_flags.extend(shlex.split(build_config_flags))

        project_flags = toc.configstore.get("project", self.name, "cmake", "flags",
            default=None)
        if project_flags:
            self.cmake_flags.extend(shlex.split(project_flags))

        if toc.build_type:
            self.cmake_flags.append("CMAKE_BUILD_TYPE=%s" % (toc.build_type.upper()))

        if toc.cmake_flags:
            self.cmake_flags.extend(toc.cmake_flags)

        #handle single sdk dir
        sdk_dir = toc.configstore.get("general", "build", "sdk_dir", default=None)
        if sdk_dir:
            if os.path.isabs(sdk_dir):
                self.sdk_directory = sdk_dir
            else:
                self.sdk_directory = os.path.join(toc.work_tree, sdk_dir)
            bname = "sdk-%s" % (build_directory_name)
            self.sdk_directory = os.path.normpath(os.path.join(self.sdk_directory, bname))
            self._custom_sdk_dir = True
            self.cmake_flags.append("QI_SDK_DIR=%s" % (self.sdk_directory))
        else:
            #normal sdk dir in buildtree
            self.sdk_directory   = os.path.join(self.build_directory, "sdk")

    def set_custom_build_directory(self, build_dir):
        """ could be used to override the default build_directory
        """
        old = self.build_directory
        self.build_directory = build_dir

        #detect single sdk directory for multiple projects
        if self._custom_sdk_dir == False:
            self.sdk_directory = os.path.join(self.build_directory, "sdk")

    def __str__(self):
        res = ""
        res += "Project: %s\n" % (self.name)
        res += "  directory       = %s\n" % self.directory
        res += "  depends         = %s\n" % self.depends
        res += "  rdepends        = %s\n" % self.rdepends
        res += "  cmake_flags     = %s\n" % self.cmake_flags
        res += "  build_directory = %s" % self.build_directory
        return res


def get_qibuild_cmake_framework_path():
    """ return the path to the qiBuild Cmake framework """
    path = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "cmake"))
    return qibuild.sh.to_posix_path(path)

def bootstrap(project, dep_sdk_dirs):
    """Generate the find_deps.cmake for the given project
    """
    build_dir = project.build_directory
    qibuild.sh.mkdir(build_dir, recursive=True)

    to_write  = "#############################################\n"
    to_write += "#QIBUILD AUTOGENERATED FILE. DO NOT EDIT.\n"
    to_write += "#############################################\n"
    to_write += "\n"
    to_write += "#QIBUILD CMAKE FRAMEWORK PATH:\n"
    to_write += "list(APPEND CMAKE_MODULE_PATH \"%s\")\n" % get_qibuild_cmake_framework_path()
    to_write += "\n"
    to_write += "#DEPENDENCIES:\n"
    for dep_sdk_dir in dep_sdk_dirs:
        to_write += "list(APPEND CMAKE_PREFIX_PATH \"%s\")\n" % qibuild.sh.to_posix_path(dep_sdk_dir)
    to_write += "set(CMAKE_MODULE_PATH \"${CMAKE_MODULE_PATH}\" CACHE INTERNAL \"\" FORCE)\n"
    to_write += "set(CMAKE_PREFIX_PATH \"${CMAKE_PREFIX_PATH}\" CACHE INTERNAL \"\" FORCE)\n"

    output_path = os.path.join(build_dir, "dependencies.cmake")
    with open(output_path, "w") as output_file:
        output_file.write(to_write)
    LOGGER.debug("Wrote %s", output_path)
