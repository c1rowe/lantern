import queue
import threading
import tornado
import logging
from abc import abstractmethod, ABCMeta

from lantern import in_ipynb
from .utils import add_to_tornado, find_free_port, fqdn


_LANTERN_LIVE = None
_LANTERN_LIVE_PORT = None
_LANTERN_LIVE_THREAD = None


class LanternLive(object):
    def __init__(self, live_thread, path):
        self._thread = live_thread
        self._path = path

    def __repr__(self):
        return self._path

    def __del__(self):
        pass
        # self._thread.stop()
        # self._thread.join()


class Streaming(metaclass=ABCMeta):
    @abstractmethod
    def run(self):
        pass

    def on_data(self, data):
        getattr(self, 'callback')(data)


def run(streamer):
    global _LANTERN_LIVE
    global _LANTERN_LIVE_THREAD
    global _LANTERN_LIVE_PORT

    q = queue.Queue()

    if not _LANTERN_LIVE:
        _LANTERN_LIVE = tornado.web.Application()
        _LANTERN_LIVE_PORT = find_free_port()
        _LANTERN_LIVE.listen(_LANTERN_LIVE_PORT)
        if not in_ipynb():
            _LANTERN_LIVE_THREAD = threading.Thread(target=tornado.ioloop.IOLoop.current().start)
            _LANTERN_LIVE_THREAD.start()
        logging.basicConfig(level=logging.CRITICAL)
        logging.info('\nlistening on %s\n' % str(_LANTERN_LIVE_PORT))

    _LANTERN_LIVE._rank = 0
    add_to_tornado(_LANTERN_LIVE, q, _LANTERN_LIVE._rank)
    _LANTERN_LIVE._rank += 1

    def qput(message):
        q.put(message)

    streamer.callback = qput
    t = threading.Thread(target=streamer.run)
    t.start()

    ll = LanternLive(t, fqdn(_LANTERN_LIVE_PORT, _LANTERN_LIVE._rank-1))
    return ll
