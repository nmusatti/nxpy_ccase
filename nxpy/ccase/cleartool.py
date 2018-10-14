# nxpy.ccase package ---------------------------------------------------------

# Copyright Nicola Musatti 2008 - 2018
# Use, modification, and distribution are subject to the Boost Software
# License, Version 1.0. (See accompanying file LICENSE.txt or copy at
# http://www.boost.org/LICENSE_1_0.txt)

# See https://github.com/nmusatti/nxpy_ccase. --------------------------------

"""
Programming interface to the ClearCase configuration management tool.
Implemented by driving interactively the cleartool program.

"""

from __future__ import absolute_import

import re
import sys

import nxpy.command.interpreter
import nxpy.command.option


class ClearToolError(Exception):
    r"""Raised when cleartool returns an unexpected reply."""


class InvalidArgument(ClearToolError):
    r"""Raised on an invalid argument combination."""


class FailedCommand(nxpy.command.interpreter.BadCommand, ClearToolError):
    r"""Raised when a command returns an error code."""

    def __init__(self, cmd, err_code=0, err=""):
        message = []
        if err:
            message.append(err)
        if err_code != 0:
            message.append("Error: " + err_code)
        super(FailedCommand, self).__init__(cmd, "\n".join(message))


_config = nxpy.command.option.Config(

    prefix="-",

    # boolean options, which appear on the command line without arguments.
    bool_opts=("cact", "cview", "force", "identical", "keep", "long", "me",
            "none", "nxn", "preview", "print_report", "short", "slink",
            "visible", "vob_only"),

    # Options with an associated value
    value_opts=("activity", "comment", "in_stream", "invob", "log", "proj",
            "stream", "target", "to", "user", "view"),

    # Options with multiple arguments, separated by commas.
    iterable_opts=("activities", ),

    # Options whose argument is copied by means of the '%' operator.
    format_opts={"fmt": "\"%s\""},

    # Options whose name must be translated, e.g. because it is not a valid identifier.
    mapped_opts={"in_stream": "-in", "nolog": "-log NUL", "print_report": "-print", "proj": "-in"},

    # Boolean options that are expressed by the lack of an opposite command line option
    opposite_opts={"activity": "-none", "checkout": "-nco -force", "comment": "-nc", "keep": "-rm",
            "log": "-log NUL"}

    )


command_line = "cleartool -status"


class ClearTool(object):
    r"""
    Allows manipulation of ClearCase UCM projects by driving the  cleartool utility in a
    subprocess.
    
    Each sub-command is implemented in its own method. In general cleartool's standard output is 
    returned, except when standard error contains useful information, in which case both are 
    returned.
    
    """
    _result_re = re.compile(r"Command \d+ returned status (\d)\r\n")

    def __init__(self, cmd=None, log=False):
        r"""
        Create a *cleartool* interpreter.
        
        *cmd* is an optional :py:class:`.command.interpreter.Interpreter` instance, used mainly to
        supply an alternative implementation for tests; *log* is an optional logging destination.
        
        """
        if cmd is not None:
            self.cmd = cmd
        else:
            self.cmd = nxpy.command.interpreter.Interpreter(command_line)
        self.cmd.setLog(log)

    def _run(self, parser, **kwargs):
        if isinstance(parser, nxpy.command.option.Parser):
            cmd = parser.getCommandLine()
        else:
            cmd = parser
        raise_on_failure = False
        try:
            raise_on_failure = kwargs["raise_on_failure"]
            del kwargs["raise_on_failure"]
        except KeyError:
            pass
        try:
            kwargs["cond"] = nxpy.command.interpreter.RegexpWaiter(self._result_re,
                    nxpy.command.interpreter.EXP_OUT)
            out, err = self.cmd.run(cmd, **kwargs)
            if raise_on_failure:
                err_code = ClearTool._result_re.search(out).group(1)
                if err_code > 0:
                    raise FailedCommand(cmd, err_code=err_code)
            return ClearTool._result_re.sub("", out), err, cmd
        except nxpy.command.interpreter.BadCommand:
            e = sys.exc_info()[1]
            raise FailedCommand(e.command, err=e.stderr)

# The cleartool sub-commands

    def cd(self, dir_=""):
        self._run("cd " + dir_)

    def checkin(self, *elements, **options):
        if not elements:
            raise InvalidArgument("At least one element must be specified")
        op = nxpy.command.option.Parser(_config, "checkin", elements, options, comment="", 
                identical=False)
        return self._run(op)[0]

    def checkout(self, *elements, **options):
        if not elements:
            raise InvalidArgument(
                    "At least one element must be specified")
        op = nxpy.command.option.Parser(_config, "checkout -nq", elements, options, comment="")
        return self._run(op)[0]

    def deliver(self, **options):
        op = nxpy.command.option.Parser(_config, "deliver", (), options, activities=(), cact=False,
                long=False, preview=False, short=False, stream="", target="",
                to="")
        op.checkExclusiveOptions("activities", "cact")
        op.checkExclusiveOptions("long", "short")
        return self._run(op, raise_on_error=False)

    def describe(self, *args, **options):
        op = nxpy.command.option.Parser(_config, "describe", args, options, fmt="", short=False)
        op.checkExclusiveOptions("fmt", "short")
        return self._run(op)[0]

    def ln(self, dest, *src, **options):
        r"""Note: Arguments are inverted with respect to the original command, beware!"""
        args = src + (dest, )
        op = nxpy.command.option.Parser(_config, "ln", args, options, checkout=True, comment=False, 
                slink=True)
        return self._run(op)[0]

    def ls(self, *files, **options):
        op = nxpy.command.option.Parser(_config, "ls", files, options, nxn=True, short=True, 
                visible=False, vob_only=False)
        return self._run(op)[0]
    
    def lsactivity(self, *activities, **options):
        r"""
        Note: *fmt=r"%[versions]p\n"* causes a race condition with activities that have a large
        number of contribuents.

        """
        op = nxpy.command.option.Parser(_config, "lsactivity", activities, options, cact=False, 
                fmt="", long=False, me=False, short=False, in_stream="", 
                user="", view="")
        op.checkExclusiveOptions("in_stream", "cact", "user", "me")
        op.checkExclusiveOptions("fmt", "long", "short")
        return self._run(op, interval=0.1)[0]
    
    def lshistory(self, obj, **options):
        op = nxpy.command.option.Parser(_config, "lshistory", ( obj, ), options, fmt="")
        return self._run(op)[0]

    def lsproject(self, **options):
        op = nxpy.command.option.Parser(_config, "lsproject", (), options, cview=False, view="", 
                invob="", fmt="")
        op.checkExactlyOneOption("cview", "view", "invob")
        return self._run(op)[0]

    def lsstream(self, **options):
        op = nxpy.command.option.Parser(_config, "lsstream", (), options, view="", proj="", 
                invob="", fmt="")
        op.checkExclusiveOptions("view", "proj", "invob")
        return self._run(op)[0]

    def lsview(self, *tags, **options):
        op = nxpy.command.option.Parser(_config, "lsview", [ "\'%s\'" % (t) for t in tags ],
                options, cview=False, short=False)
        op.checkNotBothOptsAndArgs("cview")
        return self._run(op)[0]

    def lsvob(self):
        op = nxpy.command.option.Parser(_config, "lsvob", (), {})
        return self._run(op)[0]

    def mv(self, dest, *src, **options):
        r"""Note: Arguments are inverted with respect to the original command, beware!"""
        args = src + (dest, )
        op = nxpy.command.option.Parser(_config, "mv", args, options, comment="")
        return self._run(op)[0]

    def pwd(self):
        return self._run("pwd")[0].strip()

    def rmname(self, *args, **options):
        op = nxpy.command.option.Parser(_config, "rmname", args, options, checkout=True, comment="")
        return self._run(op)[0]
        
    def setactivity(self, activity, **options):
        if activity:
            args = ( activity, )
        else:
            args = ()
            options["none"] = True
        op = nxpy.command.option.Parser(_config, "setactivity", args, options, none=False, view="")
        op.checkOneBetweenOptsAndArgs("none")
        return self._run(op)[0]

    def uncheckout(self, *elements, **options):
        op = nxpy.command.option.Parser(_config, "uncheckout", elements, options, keep=False)
        return self._run(op)[0]

    def update(self, **options):
        op = nxpy.command.option.Parser(_config, "update", (), options, print_report=False,
                force=False, nolog=False, log="")
        op.checkExclusiveOptions("log", "nolog")
        return self._run(op, raise_on_error=False, timeout=300, interval=0.5, quantum=0.5)[0]
