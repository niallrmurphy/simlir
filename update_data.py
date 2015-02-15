#!/usr/bin/env python

import constants
import sys, urllib, os.path

def reporthook(*a): print a
for url in constants.defines._REGISTRY_DATA:
  i = url.rfind('/')
  file = os.path.join(constants.defines._DATA_DIR, url[i+1:])
  print url, "->", file
  urllib.urlretrieve(url, file, reporthook)

