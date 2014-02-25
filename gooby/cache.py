#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
:mod:`cache` --- Data caching facility
======================================
"""


__docformat__ = "restructuredtext en"


import sys
import sqlite3
import importlib
from time import time

try:
    import cPickle as pickle
except ImportError:
    import pickle


# FIXME: This code is not thread-safe.
# This decision isn't optimal to say at the very least. The solution works
# for this case as Skype4Py threads are queued but it will eventually be
# the cause of concurrent SQLite access troubles.


# Hard-coded SQL queries are only being used in simple default built-in SQLite
# caching system.
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

SQL_CLEAR_EXPIRED = "DELETE FROM container WHERE expires <= ? AND expires != 0"

SQL_COUNT = "SELECT count(*) FROM container WHERE key = ?"

SQL_COUNT_ALL = "SELECT count(*) FROM container"


class BaseCache(object):
    """
    Base cache class.
    """

    def __init__(self, default_timeout=600):
        self._default_timeout = default_timeout

    def get(self, key):
        """
        Get method should always return NoneType if a requested cache key
        is expired.
        """

        raise NotImplementedError

    def add(self, key, value, timeout=None):
        raise NotImplementedError

    def set(self, key, value, timeout=None):
        raise NotImplementedError

    def delete(self, key):
        raise NotImplementedError

    def clear(self):
        raise NotImplementedError

    def _prune(self):
        """
        Clear expired cache entries. It's probably better not to call this
        method directly rather than incorporate the call into other methods
        which are modifying cache data (:meth:`BaseCache.add()`,
        :meth:`BaseCache.set()`, etc) if necessary.
        """

        raise NotImplementedError

    def get_cached(self, key, timeout=None):
        """
        Caching decorator.
        Stores return value of a cached function or method.

        .. seealso::
            :class:`SimpleCache` for basic usage.
        """

        self._timeout = timeout

        def decorated(cached_function):
            def wrapper(*args, **kwargs):
                cached = self.get(key)
                if cached is None:
                    cached = cached_function(*args, **kwargs)
                    timeout = self._timeout
                    if timeout is None:
                        expires = self._default_timeout
                    else:
                        expires = timeout
                    if expires >= 0:
                        self.set(key, cached, expires)
                return cached
            return wrapper
        return decorated

    def __setitem__(self, key, value, timeout=None):
        self.set(key, value, timeout)

    def __delitem__(self, key):
        self.delete(key)

    def __getitem__(self, key):
        return self.get(key)

    def __contains__(self, key):
        raise NotImplementedError

    def __len__(self):
        raise NotImplementedError

    def __unicode__(self):
        return "<{0} ({1} stored)>".format(self.__class__.__name__, len(self))

    def __str__(self):
        return unicode(self).encode("utf-8")


class SimpleCache(BaseCache):
    """
    Simple memory cache suited mostly for development purposes.
    Stores items in a regular Python dictionary.

    Basic usage:

    >>> cache = SimpleCache()

    >>> cache.add("mykey", 42, timeout=3600)
    >>> assert cache.get("mykey") is 42

    >>> cache.set("mykey", "derp", timeout=3600)
    >>> assert cache.get("mykey") == "derp"

    >>> cache.delete("mykey")
    >>> assert cache.get("mykey") is None

    >>> cache.set("mykey", 42, timeout=3600)
    >>> cache.clear()
    >>> assert cache.get("mykey") is None

    >>> cache.set("mykey", 42, timeout=-1)
    >>> # Cache is expired.
    >>> assert cache.get("mykey") is None

    Decorator API usage:

    >>> cache = SimpleCache()
    >>> cache.set("mykey", 42, timeout=0)
    >>> @cache.get_cached("mykey")
    ... def do_something():
    ...     return "derp"
    ...
    >>> # Outputs 42 as its output is cached for unlimited time.
    >>> assert do_something() is 42

    >>> cache.set("mykey", 42, timeout=-1)
    >>> # Outputs "derp" as the cached value is expired.
    >>> assert do_something() == "derp"

    >>> # Caching decorator applies to class methods.
    >>> cache = cache  # IDE code hinting fix.
    >>> cache["mykey"] = 42
    >>> class MyClass:
    ...     @cache.get_cached("mykey")
    ...     def do_something(self):
    ...         return "derp"
    ...
    >>> assert MyClass().do_something() is 42

    Dictionary-like behaviour:

    >>> cache = SimpleCache()
    >>> cache["mykey"] = 42

    >>> assert cache["mykey"] == cache.get("mykey")

    >>> assert "mykey" in cache

    >>> del cache["mykey"]
    >>> assert "mykey" not in cache

    >>> cache["a"] = "herp"
    >>> cache["b"] = "derp"
    >>> assert len(cache) is 2
    """

    # FIXME: Not thread-safe.

    def __init__(self, default_timeout=600):
        """
        :param default_timeout: default cache TTL in seconds. Timeout set to 0
            means cache never expires.
        :type default_timeout: `integer`
        """

        super(SimpleCache, self).__init__(default_timeout)
        self._cache = {}

    def get(self, key):
        expires, value = self._cache.get(key, (0, None))
        if expires > time() or expires == 0:
            try:
                value = pickle.loads(value)
            except TypeError:
                value = None
            return value

    def set(self, key, value, timeout=None):
        self._prune()
        timeout = timeout or self._default_timeout or 0
        expires = time() + timeout if timeout > 0 else timeout
        value = pickle.dumps(value, pickle.HIGHEST_PROTOCOL)
        self._cache.update({key: (expires, value)})

    def add(self, key, value, timeout=None):
        self._prune()
        timeout = timeout or self._default_timeout or 0
        expires = time() + timeout if timeout > 0 else timeout
        value = pickle.dumps(value, pickle.HIGHEST_PROTOCOL)
        self._cache.setdefault(key, (expires, value))

    def delete(self, key):
        self._cache.pop(key, None)

    def clear(self):
        self._cache.clear()

    def _prune(self):
        for key, (expires, _) in self._cache.items():
            if expires <= time() and expires != 0:
                self._cache.pop(key, None)

    def __contains__(self, key):
        return key in self._cache

    def __len__(self):
        return len(self._cache)


class SQLiteCache(BaseCache):
    """
    Simple SQLite-driven caching backend. Uses hardcoded SQL queries.

    Basic usage:

    >>> cache = SQLiteCache()

    >>> cache.add("herp_ [mykey]--_ DERP", 42, timeout=3600)
    >>> assert cache.get("herp_ [mykey]--_ DERP") is 42

    >>> cache.set("mykey", "derp", timeout=3600)
    >>> assert cache.get("mykey") == "derp"

    >>> cache.delete("mykey")
    >>> assert cache.get("mykey") is None

    >>> cache.set("mykey", 42, timeout=3600)
    >>> cache.clear()
    >>> assert cache.get("mykey") is None

    >>> cache.set("mykey", 42, timeout=-1)
    >>> # Cache is expired.
    >>> assert cache.get("mykey") is None

    Decorator API usage:

    >>> cache = SQLiteCache()
    >>> cache.set("mykey", 42, timeout=0)
    >>> @cache.get_cached("mykey")
    ... def do_something():
    ...     return "derp"
    ...
    >>> # Outputs 42 as its output is cached for unlimited time.
    >>> assert do_something() == 42

    >>> cache.set("mykey", 42, timeout=-1)
    >>> # Outputs "derp" as the cached value is expired.
    >>> assert do_something() == "derp"

    >>> # Caching decorator applies to class methods.
    >>> cache = cache  # IDE code hinting fix.
    >>> cache["mykey"] = 42
    >>> class MyClass:
    ...     @cache.get_cached("mykey")
    ...     def do_something(self):
    ...         return "derp"
    ...
    >>> assert MyClass().do_something() is 42

    Dictionary-like behaviour:

    >>> cache = SQLiteCache()
    >>> cache["mykey"] = 42

    >>> assert cache["mykey"] == cache.get("mykey")

    >>> assert "mykey" in cache

    >>> del cache["mykey"]
    >>> assert "mykey" not in cache

    >>> cache["a"] = "herp"
    >>> cache["b"] = "derp"
    >>> assert len(cache) is 2
    """

    def __init__(self, location="", default_timeout=600, autocommit=True):
        """
        :param location: database file path for filesystem storage. Empty
            string or ":memory:" for in-memory storage
        :type location: `str`

        :param default_timeout: default cache TTL in seconds
        :type default_timeout: `float`

        :param autocommit: decides whether database changes should be committed
            automatically
        :type autocommit: `boolean`
        """

        super(SQLiteCache, self).__init__(default_timeout)

        assert isinstance(location, basestring)

        if not location:
            self._location = ":memory:"
        else:
            self._location = location
        self._connection = None
        self._autocommit = autocommit

    def _get_connection(self):
        if self._connection is None:
            kwargs = dict(database=self._location, timeout=30)
            if self._autocommit:
                kwargs.update(dict(isolation_level=None))

            # FIXME: Potentially dangerous garbage.
            # Not thread-safe.
            # See this module's docstring for more information.
            kwargs.update(dict(check_same_thread=False))

            self._connection = sqlite3.Connection(**kwargs)
            self._connection.cursor().execute(SQL_CREATE_TABLE)
        return self._connection

    def commit(self):
        with self._get_connection() as connection:
            connection.commit()

    def get(self, key):
        value = None
        with self._get_connection() as connection:
            try:
                result = connection.cursor().execute(SQL_SELECT,
                                                     (key,)).fetchone()
                expires = result[1]
                if expires >= time() or expires == 0:
                    value = pickle.loads(str(result[0]))
            except TypeError:
                pass
        return value

    def set(self, key, value, timeout=None):
        self._prune()
        timeout = timeout or self._default_timeout or 0
        expires = time() + timeout if timeout > 0 else timeout
        # if timeout is None:
        #     expires = 0
        # elif self._default_timeout == 0:
        #     expires = 0
        # elif timeout == 0:
        #     expires = 0
        # else:
        #     expires = time() + timeout
        with self._get_connection() as connection:
            value = buffer(pickle.dumps(value, pickle.HIGHEST_PROTOCOL))
            connection.cursor().execute(SQL_REPLACE, (key, value, expires,))

    def add(self, key, value, timeout=None):
        self._prune()
        timeout = timeout or self._default_timeout or 0
        expires = time() + timeout if timeout > 0 else timeout
        # if timeout is None:
        #     expires = 0
        # elif self._default_timeout == 0:
        #     expires = 0
        # else:
        #     expires = time() + timeout
        with self._get_connection() as connection:
            value = buffer(pickle.dumps(value, pickle.HIGHEST_PROTOCOL))
            connection.cursor().execute(SQL_INSERT, (key, value, expires,))

    def delete(self, key):
        with self._get_connection() as connection:
            connection.cursor().execute(SQL_DELETE, (key,))

    def clear(self):
        with self._get_connection() as connection:
            connection.cursor().execute(SQL_CLEAR)

    def _prune(self):
        """
        >>> from time import sleep

        >>> cache = SQLiteCache()
        >>> cache.add("mykey", 42, timeout=0.01)
        >>> sleep(0.1)
        >>> cache._prune()
        >>> assert cache.get("mykey") is None
        """

        with self._get_connection() as connection:
            connection.cursor().execute(SQL_CLEAR_EXPIRED, (time(),))

    def __contains__(self, key):
        retval = False
        with self._get_connection() as connection:
            result = connection.cursor().execute(SQL_COUNT, (key,)).fetchone()
            count = result[0]
            if count == 1:
                retval = True
            elif count > 1:
                raise Exception("Cache contains multiple values with same key")
        return retval

    def __len__(self):
        with self._get_connection() as connection:
            result = connection.cursor().execute(SQL_COUNT_ALL).fetchone()
            count = result[0]
        return count

    def __del__(self):
        with self._get_connection() as connection:
            connection.commit()
            connection.cursor().close()
        self._connection.close()


class CacheManager(object):
    """
    Registry which keeps track of every instantiated cache object.

    >>> cm = CacheManager()

    >>> cache = cm.get_cache("simple_cache")
    >>> same_cache = cm.get_cache("simple_cache")
    >>> assert cache is same_cache
    """

    _default_backend = SimpleCache

    def __init__(self):
        self._caches = {}

    def get_cache(self, key):
        return self._caches.setdefault(key, self._default_backend())

    def add_cache(self, key, cacheobj):
        assert isinstance(cacheobj, BaseCache)
        self._caches.setdefault(key, cacheobj)

    def delete_cache(self, key):
        self._caches.pop(key, None)


cache_manager = CacheManager()

get_cache = cache_manager.get_cache

add_cache = cache_manager.add_cache

delete_cache = cache_manager.delete_cache


class BaseCacheConfigurator(object):
    """
    Base cache configurator class which defines some useful defaults and
    methods.
    """

    _defaults = {
        "backend": "cache.SimpleCache",

        # Depending on cache backend, location could be "host:port" pair,
        # file path, etc. Defaults to empty string which is ":memory:" for
        # cache.SQLiteCache backend.
        "location": "",

        # Cache time-to-live in seconds, with "0" means no expiration.
        "timeout": 0,
    }

    def __init__(self, config, cache_manager=cache_manager):
        self._config = config
        self._cache_manager = cache_manager

        # self._importer = __import__
        self._importer = importlib.import_module

    def _resolve(self, s):
        """
        Resolve strings to objects using standard import and attribute syntax.
        """

        chunks = s.split(".")
        used = chunks.pop(0)
        try:
            found = self._importer(used)
            for chunk in chunks:
                used += "." + chunk
                try:
                    found = getattr(found, chunk)
                except AttributeError:
                    self._importer(used)
                    found = getattr(found, chunk)
            return found
        except ImportError:
            error, traceback = sys.exc_info()[1:]
            exception = ValueError('Cannot resolve %r: %s' % (s, error))
            exception.__cause__, exception.__traceback__ = error, traceback
            raise exception


class DictCacheConfigurator(BaseCacheConfigurator):
    """
    Configure caching using a dictionary-like object to describe the
    configuration.

    Example usage:

    >>> config = dict(mycache=dict(backend="cache.SQLiteCache"))
    >>> dict_config(config)

    >>> assert isinstance(get_cache("mycache"), SQLiteCache)

    >>> cache = get_cache("other_cache")
    >>> assert isinstance(cache, SimpleCache)

    >>> cache.set("a", 42)
    >>> assert cache.get("a") is 42
    """

    def configure(self):
        for key, opts in self._config.iteritems():
            if not key:
                continue
            d = self._defaults
            backend = self._resolve(str(opts.pop("backend", d.get("backend"))))
            timeout = float(opts.pop("timeout", d.get("timeout")))
            location = str(opts.pop("location", d.get("location")))
            assert not opts, "Unknown options: %s" % ", ".join(opts.keys())
            cacheobj = backend(default_timeout=timeout, location=location)
            self._cache_manager.add_cache(key, cacheobj)


def dict_config(config):
    DictCacheConfigurator(config).configure()


if __name__ == "__main__":
    import doctest
    doctest.testmod()
