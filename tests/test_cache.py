# !/usr/bin/env python
# -*- coding: utf-8 -*-


"""
:mod:`test_cache` --- Cache unit tests
======================================
"""


from __future__ import unicode_literals


__docformat__ = 'restructuredtext en'


import unittest
import time
import tempfile
import shutil
import datetime

from tests import *
from gooby import cache_new as cache


class CacheTestCase(unittest.TestCase):
    klass = cache.BaseCache
    args = tuple()
    kwargs = dict()

    def setUp(self):
        self.cache = self.klass(*self.args, **self.kwargs)

    def tearDown(self):
        del self.cache

    def test_set_and_get(self):
        self.cache.set('derp', 42)
        self.assertEqual(self.cache.get('derp'), 42)

    def test_add_and_get(self):
        self.cache.add('derp', 42)
        self.assertEqual(self.cache.get('derp'), 42)

    def test_delete(self):
        self.cache.set('derp', 42)
        self.cache.delete('derp')
        self.assertIsNone(self.cache.get('derp'))

    def test_clear(self):
        self.cache.set('derp', 42)
        self.cache.set('key', 'alksjd')
        self.cache.clear()
        self.assertEqual(len(self.cache), 0)

    def test_len(self):
        self.cache.set('derp', 42)
        self.cache.set('key', 'alksjd')
        self.assertEqual(len(self.cache), 2)

    def test_contains(self):
        self.cache.set('derp', 42)
        self.assertTrue('derp' in self.cache)
        self.assertFalse('key' in self.cache)

    def test_cache_expires_instantly_on_negative_timeout(self):
        self.cache.set('derp', 42, timeout=-1)
        self.cache.set('k', 'v', timeout=1)
        time.sleep(0.2)
        self.cache._prune()
        self.assertIsNone(self.cache.get('derp'))
        self.assertEqual(self.cache.get('k'), 'v')

    def test_cache_expiration(self):
        self.cache.set('derp', 42, timeout=0.1)
        self.cache.set('k', 'v', timeout=10)
        self.cache.set('herp', 'derp')
        time.sleep(0.2)
        self.cache._prune()
        self.assertIsNone(self.cache.get('derp'))
        self.assertEqual(self.cache.get('k'), 'v')
        self.assertEqual(self.cache.get('herp'), 'derp')
        self.cache.set('derp', 42, timeout=10)
        self.cache.set('derp', 'v', timeout=0.1)
        time.sleep(0.2)
        self.cache._prune()
        self.assertIsNone(self.cache.get('derp'))

    def test_cache_never_expires_on_zero_timeout(self):
        self.cache.set('derp', 42, timeout=0)
        self.cache.set('k', 'v', timeout=0.1)
        time.sleep(0.2)
        self.cache._prune()
        self.assertEqual(self.cache.get('derp'), 42)
        self.assertIsNone(self.cache.get('k'))
        self.cache.set('derp', 42, timeout=1)
        self.cache.set('derp', 'v', timeout=0)
        time.sleep(0.1)
        self.assertEqual(self.cache.get('derp'), 'v')

    def test_setitem(self):
        self.cache['derp'] = 42
        self.assertEqual(self.cache.get('derp'), 42)

    def test_getitem(self):
        self.cache.set('derp', 42)
        self.assertEqual(self.cache['derp'], 42)

    def test_delitem(self):
        self.cache.set('derp', 42)
        del self.cache['derp']
        self.assertIsNone(self.cache.get('derp'))

    def test_object_retrieval(self):
        dt = datetime.datetime.now()
        self.cache.set('dt', dt, timeout=1)
        time.sleep(0.2)
        self.cache._prune()
        self.assertEqual(self.cache.get('dt'), dt)


class SimpleCacheTestCase(CacheTestCase):
    klass = cache.SimpleCache


class SimpleCacheZeroDefaultTimeoutTestCase(SimpleCacheTestCase):
    kwargs = {'default_timeout': 0}


class SQLiteCacheTestCase(CacheTestCase):
    klass = cache.SQLiteCache

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.location = os.path.join(self.tmp_dir, 'test_db.sqlite')
        self.cache = self.klass(self.location, *self.args, **self.kwargs)

    def tearDown(self):
        del self.cache
        shutil.rmtree(self.tmp_dir)

    def test_key_prefix(self):
        cache_with_prefix = self.klass(self.location, key_prefix='test')
        cache_without_prefix = self.klass(self.location)
        another_cache_without_prefix = self.klass(self.location)

        cache_with_prefix.set('derp', 42)
        self.assertEqual(cache_with_prefix.get('derp'), 42)
        self.assertIsNone(cache_without_prefix.get('derp'))
        self.assertIsNone(another_cache_without_prefix.get('derp'))

        cache_without_prefix.set('k', 'v')
        self.assertIsNone(cache_with_prefix.get('k'))
        self.assertEqual(cache_without_prefix.get('k'), 'v')
        self.assertEqual(another_cache_without_prefix.get('k'), 'v')

        del cache_with_prefix
        del cache_without_prefix
        del another_cache_without_prefix


class SQLiteCacheZeroDefaultTimeoutTestCase(SQLiteCacheTestCase):
    kwargs = {'default_timeout': 0}


TEST_CASES = (SimpleCacheTestCase, SQLiteCacheTestCase,
              SimpleCacheZeroDefaultTimeoutTestCase,
              SQLiteCacheZeroDefaultTimeoutTestCase)


def load_tests(loader, tests, pattern):
    suite = unittest.TestSuite()
    for case in TEST_CASES:
        _tests = loader.loadTestsFromTestCase(case)
        suite.addTests(_tests)
    return suite


if __name__ == '__main__':
    unittest.main()
