## Copyright (c) 2012-2016 Aldebaran Robotics. All rights reserved.
## Use of this source code is governed by a BSD-style license that can be
## found in the COPYING file.
cmake_minimum_required(VERSION 2.8)
project(footool)

find_package(qibuild)

qi_create_bin(footool "footool.cpp")
qi_stage_bin(footool)

qi_create_test(test_footool test_footool.cpp)
