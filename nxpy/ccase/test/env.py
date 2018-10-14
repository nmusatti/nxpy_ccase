# nxpy.ccase package ---------------------------------------------------------

# Copyright Nicola Musatti 2012 - 2018
# Use, modification, and distribution are subject to the Boost Software
# License, Version 1.0. (See accompanying file LICENSE.txt or copy at
# http://www.boost.org/LICENSE_1_0.txt)

# See https://github.com/nmusatti/nxpy_ccase. --------------------------------

r"""
Clearcase test environment definition.

"""

from __future__ import absolute_import

import os.path
import platform

from six.moves import configparser

import nxpy.test.env


class ConfigurationError(Exception):
    r"""Raised when the ClearCase test environment is not properly set."""


class Env(nxpy.test.env.EnvBase):
    r"""Environment configuration information for ClearCase related tests."""
    
    src_link_name = "nxpy_test_link"
    r"""Name for a link created when testing the *ln()* method."""
    
    backup_ext = ".test"
    r"""Extension used for backup files."""

    def __init__(self):
        r"""Takes initialization information from a conventionally placed configuration file."""
        
        nxpy.test.env.EnvBase.__init__(self, "conf")
        self.parser = configparser.SafeConfigParser()
        self.parser.read(os.path.join(self.elem_dir, "ccase.ini"))
        self.section = platform.node()
        if not self.parser.has_section(self.section):
            self.section = "localhost"
            if not self.parser.has_section(self.section):
                raise ConfigurationError("ccase.ini has no section for this computer")

        self.src_view_dir = self._get("src_view_dir")
        self.src_view_tag = self._get("src_view_tag")
        self.src_stream_tag = self._get("src_stream_tag")
        self.src_stream_sel = self._get("src_stream_sel")
        self.src_proj_sel = self._get("src_proj_sel")
        self.relative_src_dir = self._get("relative_src_dir")
        self.src_file_name = self._get("src_file_name")
        self.dest_view_dir = self._get("dest_view_dir")
        self.dest_view_tag = self._get("dest_view_tag")
        self.dest_stream_sel = self._get("dest_stream_sel")
        self.proj_vob = self._get("proj_vob")
        self.lsview_tags = self._get("lsview_tags")
        self.activity = self._get("activity")
        self.test = self._getboolean("test")
        
        self.src_dir_path = os.path.join(self.src_view_dir, self.relative_src_dir)
        self.src_file_path = os.path.join(self.src_dir_path, self.src_file_name)
        self.backup_file_name = self.src_file_name + self.backup_ext
        self.src_stream_pattern = "\*" + self.src_stream_tag + "\*"

    def _get(self, option):
        return self.parser.get(self.section, option)

    def _getboolean(self, option):
        return self.parser.getboolean(self.section, option)


def get_env(test):
    r"""
    If the environment is correctly configured an instance of *Env* is returned, otherwise
    the current test is skipped. *test* is a :py:class:`unittest.TestCase` instance containing the
    test currently being executed.
    
    """
    try:
        return Env()
    except nxpy.test.env.TestEnvNotSetError:
        test.skipTest("Test environment not set")
        return None
