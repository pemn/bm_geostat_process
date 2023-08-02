#!python
# evaluate code interpolating vtk array names as symbols
# v1.0 2023/08 paulo.ernesto
'''
usage: $0 input_path*vtk input_code*py output*vtk
'''

import sys, os.path, re
import numpy as np
import pandas as pd

# import modules from a pyz (zip) file with same name as scripts
sys.path.insert(0, os.path.splitext(sys.argv[0])[0] + '.pyz')

from _gui import usage_gui

import pyvista as pv

class DSLSUB(object):
  def __call__(self, code = ''):
    if code == '-':
      code = input()
    elif code.endswith('.py') and os.path.exists(code):
      code = open(code).read()

    s = re.sub(r'([a-z_]\w{1,})(\s+=\s+)?', self.sub, code)
    print(s)
    exec(s)

  def sub(self, m):
    token = m.group(1)
    if (m.group(2) is not None) or (token in self.array_names):
      token = "self.cell_data['%s']%s" % m.groups('')
    return token

class DSLUG(DSLSUB, pv.UniformGrid):
  ...

class DSLSG(DSLSUB, pv.StructuredGrid):
  ...

def DSLSUB_new(input_path):
  self = pv.read(input_path)
  if self.GetDataObjectType() == 6:
    self = DSLUG(self)
  elif self.GetDataObjectType() == 2:
    self = DSLSG(self)
  return self

# main
def vtk_evaluate_array(input_path, input_code, output = None):
  dsl = DSLSUB_new(input_path)
  dsl(input_code)
  if not output:
    output = input_path
  dsl.save(output)

main = vtk_evaluate_array

if __name__=="__main__": 
  usage_gui(__doc__)
