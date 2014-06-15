#!/usr/bin/env python
# coding:utf-8
import unittest
from google.appengine.ext import ndb
from google.appengine.ext import testbed
from google.appengine.datastore import datastore_stub_util


class DemoTestCase(unittest.TestCase):

  def setUp(self):
    self.testbed = testbed.Testbed()
    self.testbed.activate()
    self.policy = datastore_stub_util.PseudoRandomHRConsistencyPolicy(probability=0)
    self.testbed.init_datastore_v3_stub(consistency_policy=self.policy)

  def tearDown(self):
    self.testbed.deactivate()

  def testEventuallyConsistentGlobalQueryResult(self):
    class TestModel(ndb.Model):
      pass

    user_key = ndb.Key.from_path('User', 'ryan')
    # Put two entities
    ndb.put([TestModel(parent=user_key), TestModel(parent=user_key)])

    # Global query doesn't see the data.
    self.assertEqual(0, TestModel.all().count(3))
    # Ancestor query does see the data.
    self.assertEqual(2, TestModel.all().ancestor(user_key).count(3))

if __name__ == '__main__':
    unittest.main()
