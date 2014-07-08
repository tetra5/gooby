# !/usr/bin/env python
# -*- coding: utf-8 -*-


"""
:mod:`cache` --- Key-value data caching facility
================================================

    Creating a Cache object
    -----------------------

    Setting up explicitly:

        >>> from gooby.cache import SimpleCache
        >>> c = SimpleCache()

    Setting up via configuration dictionary:

        >>> from gooby.cache import from_dict
        >>> conf_dict = {
        ...     'backend': 'gooby.cache.SimpleCache',
        ...     'default_timeout': 12 * 60,
        ... }
        >>> c = from_dict(conf_dict)

    Working with Cache object
    -------------------------

        >>> from gooby.cache import SimpleCache
        >>> c = SimpleCache()
        >>> c.set('k', 'v')
        >>> c.get('k')
        'v'
        >>> c.get('some_key') is None
        True
        >>> c['derp'] = 42
        >>> 'derp' in c
        True
        >>> c
        '<SimpleCache (2 stored)>'
        >>> del c['derp']
        >>> 'derp' in c
        False

    A simple example of how to cache an expensive calculation result,
    assuming `my_cache` has been initialized and is accessible::

        def expensive_calculation(key):
            time.sleep(10)
            return '%s!' % key

        def func(k):
            value = my_cache.get(key)
            if value is not None:
                return value
            value = expensive_calculation(key)
            my_cache.set(key, value)
            return value

"""


from __future__ import unicode_literals


__docformat__ = 'restructuredtext en'

import contextlib
import importlib
import time
import sqlite3
try:
    import threading
except ImportError:
    import dummy_threading as threading
try:
    from cPickle import pickle
except ImportError:
    import pickle


class BaseCache(object):
    def __init__(self, default_timeout=600):
        self._default_timeout = default_timeout

    def _prune(self):
        raise NotImplementedError

    def get(self, key):
        raise NotImplementedError

    def set(self, key, value, timeout=None):
        raise NotImplementedError

    def add(self, key, value, timeout=None):
        raise NotImplementedError

    def delete(self, key):
        raise NotImplementedError

    def clear(self):
        raise NotImplementedError

    def __contains__(self, key):
        raise NotImplementedError

    def __len__(self):
        raise NotImplementedError

    def __setitem__(self, key, value, timeout=None):
        self.set(key, value, timeout)

    def __delitem__(self, key):
        self.delete(key)

    def __getitem__(self, key):
        return self.get(key)

    def __unicode__(self):
        return "<{0} ({1} stored)>".format(self.__class__.__name__, len(self))

    def __str__(self):
        return unicode(self).encode('utf-8')


class SimpleCache(BaseCache):
    """Simple thread-safe memory cache.
    Mostly suited for development purposes. Stores items in a regular Python
    dictionary.
    """

    def __init__(self, default_timeout=600):
        super(SimpleCache, self).__init__(default_timeout)
        self._lock = threading.Lock()
        self._cache = {}

    def _prune(self):
        now = time.time()
        with self._lock:
            for key, (expires, _) in self._cache.items():
                if 0 < expires <= now:
                    self._cache.pop(key, None)

    def get(self, key):
        now = time.time()
        expires, value = self._cache.get(key, (0, None))
        if expires >= now or expires is 0:
            try:
                value = pickle.loads(value)
            except TypeError:
                value = None
            return value

    def set(self, key, value, timeout=None):
        """Set `timeout` to `0` to disable key expiration."""

        now = time.time()
        value = pickle.dumps(value, pickle.HIGHEST_PROTOCOL)
        timeout = timeout or 0
        if timeout is 0 and self._default_timeout is 0:
            expires = 0
        else:
            expires = now + (timeout or self._default_timeout)
        self._prune()
        with self._lock:
            self._cache.update({key: (expires, value)})

    def add(self, key, value, timeout=None):
        """Set `timeout` to `0` to disable key expiration."""

        now = time.time()
        value = pickle.dumps(value, pickle.HIGHEST_PROTOCOL)
        timeout = timeout or 0
        if timeout is 0 and self._default_timeout is 0:
            expires = 0
        else:
            expires = now + (timeout or self._default_timeout)
        self._prune()
        with self._lock:
            self._cache.setdefault(key, (expires, value))

    def delete(self, key):
        with self._lock:
            self._cache.pop(key, None)

    def clear(self):
        with self._lock:
            self._cache.clear()

    def __contains__(self, key):
        return key in self._cache

    def __len__(self):
        return len(self._cache)


SQL_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS container
(
    key TEXT PRIMARY KEY,
    value BLOB,
    expires FLOAT
)
"""

SQL_INSERT = "INSERT INTO container (key, value, expires) VALUES (?, ?, ?)"

SQL_DELETE = "DELETE FROM container WHERE key = ?"

SQL_SELECT = "SELECT value, expires FROM container WHERE key = ?"

SQL_REPLACE = "REPLACE INTO container (key, value, expires) VALUES (?, ?, ?)"

SQL_CLEAR = "DELETE FROM container"

SQL_CLEAR_EXPIRED = "DELETE FROM container WHERE (expires <= ? AND expires > 0)"

SQL_COUNT = "SELECT count(*) FROM container WHERE key = ?"

SQL_COUNT_ALL = "SELECT count(*) FROM container"


class SQLiteCache(BaseCache):
    """SQLite cache backend.
    Note: `:memory:` location is not directly supported, as this backend
    creates a separate connection for each query."""

    def __init__(self, location, default_timeout=600, key_prefix=None):
        super(SQLiteCache, self).__init__(default_timeout)
        self._key_prefix = key_prefix
        self._location = location

    def _make_key(self, key):
        if self._key_prefix is not None:
            return '%s_%s' % (self._key_prefix, key)
        return key

    @contextlib.contextmanager
    def _connect(self):
        kwargs = dict(database=self._location, timeout=5, isolation_level=None)
        connection = sqlite3.Connection(**kwargs)
        connection.cursor().execute(SQL_CREATE_TABLE)
        try:
            yield connection
        finally:
            connection.close()

    def _prune(self):
        now = time.time()
        with self._connect() as conn:
            conn.cursor().execute(SQL_CLEAR_EXPIRED, (now,))

    def get(self, key):
        key = self._make_key(key)
        now = time.time()
        value = None
        with self._connect() as conn:
            try:
                result = conn.cursor().execute(SQL_SELECT, (key,)).fetchone()
                expires = result[1]
                if expires >= now or expires == 0:
                    value = pickle.loads(result[0])
            except TypeError:
                pass
        return value

    def set(self, key, value, timeout=None):
        """Set `timeout` to `0` to disable key expiration."""

        key = self._make_key(key)
        now = time.time()
        timeout = timeout or 0
        if timeout is 0 and self._default_timeout is 0:
            expires = 0
        else:
            expires = now + (timeout or self._default_timeout)
        self._prune()
        with self._connect() as conn:
            value = buffer(pickle.dumps(value, pickle.HIGHEST_PROTOCOL))
            conn.cursor().execute(SQL_REPLACE, (key, value, expires,))

    def add(self, key, value, timeout=None):
        """Set `timeout` to `0` to disable key expiration."""

        key = self._make_key(key)
        now = time.time()
        timeout = timeout or 0
        if timeout is 0 and self._default_timeout is 0:
            expires = 0
        else:
            expires = now + (timeout or self._default_timeout)
        self._prune()
        with self._connect() as conn:
            value = buffer(pickle.dumps(value, pickle.HIGHEST_PROTOCOL))
            conn.cursor().execute(SQL_INSERT, (key, value, expires,))

    def delete(self, key):
        key = self._make_key(key)
        with self._connect() as conn:
            conn.cursor().execute(SQL_DELETE, (key,))

    def clear(self):
        with self._connect() as conn:
            conn.cursor().execute(SQL_CLEAR)

    def __contains__(self, key):
        key = self._make_key(key)
        with self._connect() as conn:
            result = conn.cursor().execute(SQL_COUNT, (key,)).fetchone()
            count = result[0]
            if count == 1:
                return True
        return False

    def __len__(self):
        with self._connect() as conn:
            result = conn.cursor().execute(SQL_COUNT_ALL).fetchone()
            count = result[0]
        return count


def from_dict(conf_dict):
    backend = conf_dict.pop('backend')
    mod, klass = backend.split('.', 1)
    mod = importlib.import_module(mod)
    obj = getattr(mod, klass)
    return obj(**conf_dict)
