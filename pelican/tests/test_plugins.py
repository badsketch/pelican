# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

import os
from contextlib import contextmanager

from pelican.plugins._utils import get_namespace_plugins, load_plugins
from pelican.tests.support import unittest


@contextmanager
def tmp_namespace_path(path):
    '''Context manager for temporarily appending namespace plugin packages

    path: path containing the `pelican` folder

    This modifies the `pelican.__path__` and lets the `pelican.plugins`
    namespace package resolve it from that.
    '''
    # This avoids calls to internal `pelican.plugins.__path__._recalculate()`
    # as it should not be necessary
    import pelican

    old_path = pelican.__path__[:]
    try:
        pelican.__path__.append(os.path.join(path, 'pelican'))
        yield
    finally:
        pelican.__path__ = old_path


class PluginTest(unittest.TestCase):
    _PLUGIN_FOLDER = os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        'dummy_plugins')
    _NS_PLUGIN_FOLDER = os.path.join(_PLUGIN_FOLDER, 'namespace_plugin')
    _NORMAL_PLUGIN_FOLDER = os.path.join(_PLUGIN_FOLDER, 'normal_plugin')

    def test_namespace_path_modification(self):
        import pelican
        import pelican.plugins
        old_path = pelican.__path__[:]

        # not existing path
        path = os.path.join(self._PLUGIN_FOLDER, 'foo')
        with tmp_namespace_path(path):
            self.assertIn(
                os.path.join(path, 'pelican'),
                pelican.__path__)
            # foo/pelican does not exist, so it won't propagate
            self.assertNotIn(
                os.path.join(path, 'pelican', 'plugins'),
                pelican.plugins.__path__)
        # verify that we restored path back
        self.assertEqual(pelican.__path__, old_path)

        # existing path
        with tmp_namespace_path(self._NS_PLUGIN_FOLDER):
            self.assertIn(
                os.path.join(self._NS_PLUGIN_FOLDER, 'pelican'),
                pelican.__path__)
            # /namespace_plugin/pelican exists, so it should be in
            self.assertIn(
                os.path.join(self._NS_PLUGIN_FOLDER, 'pelican', 'plugins'),
                pelican.plugins.__path__)
        self.assertEqual(pelican.__path__, old_path)

    def test_get_namespace_plugins(self):
        # without plugins
        ns_plugins = get_namespace_plugins()
        self.assertEqual(len(ns_plugins), 0)

        # with plugin
        with tmp_namespace_path(self._NS_PLUGIN_FOLDER):
            ns_plugins = get_namespace_plugins()
            self.assertEqual(len(ns_plugins), 1)
            self.assertIn('pelican.plugins.ns_plugin', ns_plugins)
            self.assertEqual(
                ns_plugins['pelican.plugins.ns_plugin'].NAME,
                'namespace plugin')

        # should be back to 0 outside `with`
        ns_plugins = get_namespace_plugins()
        self.assertEqual(len(ns_plugins), 0)

    def test_load_plugins(self):
        # no plugins
        plugins = load_plugins({})
        self.assertEqual(len(plugins), 0)

        with tmp_namespace_path(self._NS_PLUGIN_FOLDER):
            # with no `PLUGINS` setting, load namespace plugins
            plugins = load_plugins({})
            self.assertEqual(len(plugins), 1, plugins)
            self.assertEqual(
                {'namespace plugin'},
                set(plugin.NAME for plugin in plugins))

            # disable namespace plugins with `PLUGINS = []`
            SETTINGS = {
                'PLUGINS': []
            }
            plugins = load_plugins(SETTINGS)
            self.assertEqual(len(plugins), 0, plugins)

            # using `PLUGINS`

            # normal plugin
            SETTINGS = {
                'PLUGINS': ['normal_plugin'],
                'PLUGIN_PATHS': [self._NORMAL_PLUGIN_FOLDER]
            }
            plugins = load_plugins(SETTINGS)
            self.assertEqual(len(plugins), 1, plugins)
            self.assertEqual(
                {'normal plugin'},
                set(plugin.NAME for plugin in plugins))

            # namespace plugin short
            SETTINGS = {
                'PLUGINS': ['ns_plugin']
            }
            plugins = load_plugins(SETTINGS)
            self.assertEqual(len(plugins), 1, plugins)
            self.assertEqual(
                {'namespace plugin'},
                set(plugin.NAME for plugin in plugins))

            # namespace plugin long
            SETTINGS = {
                'PLUGINS': ['pelican.plugins.ns_plugin']
            }
            plugins = load_plugins(SETTINGS)
            self.assertEqual(len(plugins), 1, plugins)
            self.assertEqual(
                {'namespace plugin'},
                set(plugin.NAME for plugin in plugins))

            # normal and namespace plugin
            SETTINGS = {
                'PLUGINS': ['normal_plugin', 'ns_plugin'],
                'PLUGIN_PATHS': [self._NORMAL_PLUGIN_FOLDER]
            }
            plugins = load_plugins(SETTINGS)
            self.assertEqual(len(plugins), 2, plugins)
            self.assertEqual(
                {'normal plugin', 'namespace plugin'},
                set(plugin.NAME for plugin in plugins))
