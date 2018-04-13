# gemato: Utility functions
# vim:fileencoding=utf-8
# (c) 2017-2018 Michał Górny
# Licensed under the terms of 2-clause BSD license

try:
    import asyncio
except ImportError:
    asyncio = None

import multiprocessing


class MultiprocessingPoolWrapper(object):
    """
    A portability wrapper for multiprocessing.Pool that supports
    context manager API (and any future hacks we might need).

    Note: the multiprocessing behavior has been temporarily removed
    due to unresolved deadlocks. It will be restored once the cause
    of the issues is found and fixed or worked around.
    """

    __slots__ = ['processes']

    def __init__(self, processes):
        self.processes = processes or 1

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_cb):
        pass

    def map(self, func, it, chunksize=None):
        if self.processes == 1 or asyncio is None:
            return map(func, it)

        def target(x, pipe):
            try:
                result = func(x)
                exception = None
            except Exception as e:
                result = None
                exception = e

            try:
                pipe.send((result, exception))
            except BrokenPipeError:
                pass

        def reader_callback(pipe, future):
            try:
                future.set_result(pipe.recv())
            finally:
                loop.remove_reader(pipe.fileno())
                pipe.close()

        readers = set()
        procs = {}
        loop = asyncio.get_event_loop()
        it = iter(it)

        try:
            while True:
                x = next(it, None)
                if x is not None:
                    pr, pw = multiprocessing.Pipe(duplex=False)
                    proc = multiprocessing.Process(target=target, args=(x, pw))
                    proc.start()
                    pw.close()
                    reader = asyncio.Future()
                    loop.add_reader(pr.fileno(), reader_callback, pr, reader)
                    readers.add(reader)
                    procs[id(reader)] = (proc, pr, reader)
                    if len(procs) < self.processes:
                        continue

                if not (x or procs):
                    break

                done, readers = loop.run_until_complete(
                    asyncio.wait(readers, return_when=asyncio.ALL_COMPLETED))
                for reader in done:
                    (proc, pr, reader) = procs.pop(id(reader))
                    proc.join()
                    result, exception = reader.result()
                    if exception is None:
                        yield result
                    else:
                        raise exception
        finally:
            while procs:
                reader_id, (proc, pr, reader) = procs.popitem()
                loop.remove_reader(pr.fileno())
                proc.terminate()
                proc.join()

    def imap_unordered(self, *args, **kwargs):
        """
        Use imap_unordered() if available and safe to use. Fall back
        to regular map() otherwise.
        """
        return self.map(*args, **kwargs)


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
