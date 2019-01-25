# nxpy.ccase package ---------------------------------------------------------

# Copyright Nicola Musatti 2008 - 2018
# Use, modification, and distribution are subject to the Boost Software
# License, Version 1.0. (See accompanying file LICENSE.txt or copy at
# http://www.boost.org/LICENSE_1_0.txt)

# See https://github.com/nmusatti/nxpy_ccase. --------------------------------

r"""
Tests for the cleartool module

"""

from __future__ import absolute_import

import os

import nxpy.ccase.cleartool
import nxpy.ccase.test.env
import nxpy.command.interpreter
import nxpy.command.option
import nxpy.core.file
import nxpy.core.temp_file
import nxpy.test.log
import nxpy.test.test


class MockRunner(object):
    def __init__(self, mr_out=True, mr_exc=None):
        self.out = mr_out
        self.exc = mr_exc

    def __call__(self, cmd, **kwargs):
        if self.exc:
            raise self.exc
        if self.out:
            if self.out == True:
                return cmd
            else:
                return self.out


class ClearToolMock(nxpy.ccase.cleartool.ClearTool):
    r"""
    ClearTool mock which intercepts destructive or exceedingly heavy operations

    """

    def _mock(self, runner, func, *args, **kwargs):
        try:
            r = self._run
            self._run = runner
            ret = func(*args, **kwargs)
        finally:
            self._run = r
        return ret

    def deliver(self, *args, **kwargs):
        kwargs['preview'] = True
        return super(ClearToolMock, self).deliver(*args, **kwargs)

    def update(self, *args, **kwargs):
        kwargs['print_report'] = True
        return super(ClearToolMock, self).update(*args, **kwargs)


class TestBase(nxpy.test.test.TestCase):
    cmd = None
    
    def __init__(self, *args, **kwargs):
        log = False
        if "log" in kwargs.keys():
            log = kwargs["log"]
            del kwargs["log"]
        nxpy.test.test.TestCase.__init__(self, *args, **kwargs)
        self._tool = None
        try:
            if not TestBase.cmd:
                TestBase.cmd = nxpy.command.interpreter.Interpreter(
                        nxpy.ccase.cleartool.command_line)
            self._tool = ClearToolMock(cmd=TestBase.cmd, log=log)
        except:
            pass
        
    @property
    def tool(self):
        if not self._tool:
            self.skipTest("cleartool command not available")
            return None
        else:
            return self._tool

    def skipIfNotTest(self):
        if not self.env.test:
            self.skipTest("Destructive test")
            
class ClearToolTestBase(TestBase):
    r"""
    Reusable base class for ClearTool test suite classes. 
    Uses ClearToolMock to avoid performing harmful operations.
    """

    def setUp(self):
        self._env = None
        self.tool.cd()

# support functions

    @property
    def env(self):
        if self._env == None:
            self._env = nxpy.ccase.test.env.get_env(self)
        return self._env

    def cd(self, d=None):
        if not d:
            d = self.env.src_view_dir
        try:
            self.tool.cd(d)
            return True
        except nxpy.ccase.cleartool.FailedCommand:
            return False

    def setActivity(self):
        try:
            self.tool.setactivity(
                self.tool.lsactivity(short=True).splitlines()[0])
            return True
        except:
            return False

    def resetActivity(self):
        try:
            self.tool.setactivity(None)
        except:
            pass

class ClearToolTest(ClearToolTestBase):

# cd

    def test_cd_pass(self):
        self.tool.cd(os.getcwd())

    def test_cd_fail(self):
        self.assertRaises(nxpy.ccase.cleartool.FailedCommand, self.tool.cd, 
                "directory/which/does/not/exist")

# checkin - performed only in a testing environment

    def test_checkin_pass(self):
        self.skipIfNotTest()
        if self.cd() and self.setActivity():
            try:
                self.tool.checkout(self.env.src_file_path)
            except:
                pass
            else:
                self.assertTrue(self.tool.checkin(self.env.src_file_path, 
                        identical=True))
            finally:
                self.resetActivity()

    def test_checkin_fail(self):
        self.skipIfNotTest()
        if self.cd() and self.setActivity():
            try:
                self.assertRaises(nxpy.ccase.cleartool.FailedCommand, self.tool.checkin, 
                        self.env.src_file_path)
            except:
                pass
            finally:
                self.resetActivity()

# checkout - performed only in a testing environment

    def test_checkout_pass(self):
        self.skipIfNotTest()
        if self.cd() and self.setActivity():
            try:
                out = self.tool.checkout(self.env.src_file_path)
                self.tool.uncheckout(self.env.src_file_path)
            finally:
                self.resetActivity()
            self.assertTrue(out)

    def test_checkout_fail(self):
        self.skipIfNotTest()
        try:
            self.tool.cd()
            self.resetActivity()
        except:
            pass
        else:
            self.assertRaises(nxpy.ccase.cleartool.FailedCommand, self.tool.checkout, 
                    self.env.src_file_path)

# deliver

    def test_deliver_preview_pass(self):
        if self.cd():
            self.assertTrue(self.tool.deliver(activities=( self.env.activity, ),
                    preview=True, stream=self.env.src_stream_sel, 
                    target=self.env.dest_stream_sel, 
                    to=self.env.dest_view_tag))
        
# describe

    def test_describe_fail(self):
        self.assertRaises(nxpy.ccase.cleartool.FailedCommand, self.tool.describe, 
                "file/which/does/not/exist")

    def test_describe_file_pass(self):
        self.assertTrue(self.tool.describe(self.env.src_file_path))

    def test_describe_activity_pass(self):
        if self.cd():
            self.assertTrue(self.tool.describe(self.tool.lsactivity(me=True, 
                    fmt=r"%Xn\n").splitlines()[0]))

# get

    def test_get_pass(self):
        v = self.tool.ls(self.env.src_file_path, nxn=False)
        v = v.strip()
        with nxpy.core.temp_file.TempDir() as d:
            dest_file = os.path.join(d.name, self.env.src_file_name)
            self.tool.get(dest_file, v)
            self.assertTrue(nxpy.core.file.compare(dest_file, self.env.src_file_path))

# ln - performed only in a testing environment

    def test_ln_pass(self):
        self.skipIfNotTest()
        if self.cd(self.env.src_dir_path):
            self.assertTrue(self.tool.ln(self.env.src_link_name, 
                    self.env.src_file_name, checkout=False))
            self.tool.rmname(self.env.src_link_name, checkout=False)

    def test_ln_fail(self):
        self.skipIfNotTest()
        if self.cd(self.env.src_dir_path):
            self.assertRaises(nxpy.ccase.cleartool.FailedCommand, self.tool.ln, 
                    self.env.src_file_name, self.env.src_link_name, checkout=False)

# ls

    def test_ls_pass(self):
        if self.cd(self.env.src_dir_path):
            self.assertTrue(self.tool.ls())

    def test_ls_fail(self):
        self.tool.cd("C:\\")
        self.assertRaises(nxpy.ccase.cleartool.FailedCommand, self.tool.ls) 


# lsactivity

    def test_lsactivity_pass(self):
        if self.cd():
            self.assertTrue(self.tool.lsactivity())

    def test_lsactivity_fail(self):
        self.assertRaises(nxpy.ccase.cleartool.FailedCommand, self.tool.lsactivity)

    def test_lsactivity_stream_pass(self):
        if self.cd():
            self.assertTrue(self.tool.lsactivity(in_stream=self.env.src_stream_sel))

# lshistory

    def test_lshistory_pass(self):
        self.assertTrue(self.tool.lshistory(self.env.src_file_path, all=True))
    
    def test_lshistory_fail(self):
        self.assertRaises(nxpy.ccase.cleartool.FailedCommand, self.tool.lshistory,
                "/file/which/does/not/exist")

# lsproject

    def test_lsproject_cview_pass(self):
        if self.cd():
            self.assertTrue(self.tool.lsproject(cview=True))

    def test_lsproject_fail(self):
        self.assertRaises(nxpy.command.option.InvalidOptionError, self.tool.lsproject)

    def test_lsproject_cview_view_fail(self):
        self.assertRaises(nxpy.command.option.InvalidOptionError, 
                self.tool.lsproject,cview=True, view=self.env.src_view_tag)

    def test_lsproject_view_pass(self):
        self.assertTrue(self.tool.lsproject(view=self.env.src_view_tag))

    def test_lsproject_invob_pass(self):
        self.assertTrue(self.tool.lsproject(invob=self.env.proj_vob))

# lsstream

    def test_lsstream_pass(self):
        if self.cd():
            self.assertTrue(self.tool.lsstream())

    def test_lsstream_fail(self):
        self.assertRaises(nxpy.ccase.cleartool.FailedCommand, self.tool.lsstream)

    def test_lsstream_view_proj_fail(self):
        self.assertRaises(nxpy.command.option.InvalidOptionError, self.tool.lsstream, 
                view=self.env.src_view_tag, proj=self.env.src_proj_sel)

    def test_lsstream_view_pass(self):
        self.assertTrue(self.tool.lsstream(view=self.env.src_view_tag))

    def test_lsstream_proj_pass(self):
        self.assertTrue(self.tool.lsstream(proj=self.env.src_proj_sel))

    def test_lsstream_invob_pass(self):
        self.assertTrue(self.tool.lsstream(invob=self.env.proj_vob))

# lsview

    def test_lsview_pass(self):
        self.assertTrue(self.tool.lsview())

    def test_lsview_cview_pass(self):
        if self.cd():
            self.assertTrue(self.tool.lsview(cview=True))

    def test_lsview_cview_fail(self):
        self.assertRaises(nxpy.ccase.cleartool.FailedCommand, self.tool.lsview, cview=True) 

    def test_lsview_cview_tags_fail(self):
        self.assertRaises(nxpy.command.option.InvalidOptionError, self.tool.lsview, 
                self.env.src_stream_pattern, cview=True) 

    def test_lsview_tags_pass(self):
        self.assertTrue(self.tool.lsview(self.env.lsview_tags))

# lsvob

    def test_lsvob_pass(self):
        self.assertTrue(self.tool.lsvob())

# mv - performed only in a testing environment

    def test_mv_pass(self):
        self.skipIfNotTest()
        self.skip("Test not implemented!")

# pwd

    def test_pwd_pass(self):
        if self.cd(self.env.src_view_dir):
            self.assertEqual(self.tool.pwd(), self.env.src_view_dir)

# rmname - performed only in a testing environment

    def test_rmname_pass(self):
        self.skipIfNotTest()
        if self.cd(self.env.src_dir_path):
            try:
                self.tool.ln(self.env.src_link_name, 
                        self.env.src_file_name, checkout=False)
            except:
                pass
            else:
                self.assertTrue(self.tool.rmname(self.env.src_link_name, 
                        checkout=False))

    def test_rmname_fail(self):
        self.skipIfNotTest()
        if self.cd(self.env.src_dir_path):
            self.assertRaises(nxpy.ccase.cleartool.FailedCommand, self.tool.rmname, 
                    self.env.src_link_name, checkout=False)

# setactivity

    def test_setactivity_pass(self):
        if self.cd():
            activity = self.tool.lsactivity(short=True).splitlines()[0]
            if activity:
                self.assertTrue(self.tool.setactivity(activity))

    def test_setactivity_none_pass(self):
        if self.cd():
            self.assertTrue(self.tool.setactivity(None))

# uncheckout - performed only in a testing environment

    def test_uncheckout_pass(self):
        self.skipIfNotTest()
        if self.cd() and self.setActivity():
            try:
                self.tool.checkout(self.env.src_file_path)
                self.assertTrue(self.tool.uncheckout(self.env.src_file_path))
            finally:
                self.resetActivity()

    def test_uncheckout_fail(self):
        self.skipIfNotTest()
        if self.cd() and self.setActivity():
            try:
                self.assertRaises(nxpy.ccase.cleartool.FailedCommand, self.tool.uncheckout, 
                        self.env.src_file_path)
            finally:
                self.resetActivity()

# update

    def test_update_pass(self):
        if self.cd():
            self.assertTrue(self.tool.update())

    def test_update_fail(self):
        self.assertFalse(self.tool.update())
