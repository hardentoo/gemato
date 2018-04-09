# gemato: Utility functions
# vim:fileencoding=utf-8
# (c) 2017-2018 Michał Górny
# Licensed under the terms of 2-clause BSD license

import multiprocessing
import sys

try:
	from concurrent.futures import ProcessPoolExecutor
except ImportError:
	ProcessPoolExecutor = None


class MultiprocessingPoolWrapper(object):
    """
    A portability wrapper for multiprocessing.Pool that supports
    context manager API (and any future hacks we might need).
    """

    __slots__ = ['pool']

    def __init__(self, processes):
        # ProcessPoolExecutor.map supports chunksize in python3.5+,
        # use it as a possible workaround for imap_unordered deadlock
        # reported in https://bugs.gentoo.org/647964.
        if sys.version_info >= (3, 5):
            self.pool = ProcessPoolExecutor(max_workers=processes)
        else:
            self.pool = multiprocessing.Pool(processes=processes)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_cb):
        if hasattr(self.pool, 'shutdown'):
            self.pool.shutdown()
        else:
            if exc_type is None:
                self.pool.close()
                self.pool.join()
            self.pool.terminate()

    def map(self, *args, **kwargs):
        return self.pool.map(*args, **kwargs)

    def imap_unordered(self, *args, **kwargs):
        """
        Use imap_unordered() if available and safe to use. Fall back
        to regular map() otherwise.
        """
        return self.pool.map(*args, **kwargs)


def path_starts_with(path, prefix):
    """
    Returns True if the specified @path starts with the @prefix,
    performing component-wide comparison. Otherwise returns False.
    """
    return prefix == "" or (path + "/").startswith(prefix.rstrip("/") + "/")


def path_inside_dir(path, directory):
    """
    Returns True if the specified @path is inside @directory,
    performing component-wide comparison. Otherwise returns False.
    """
    return ((directory == "" and path != "")
            or path.rstrip("/").startswith(directory.rstrip("/") + "/"))


def throw_exception(e):
    """
    Raise the given exception. Needed for onerror= argument
    to os.walk(). Useful for other callbacks.
    """
    raise e
