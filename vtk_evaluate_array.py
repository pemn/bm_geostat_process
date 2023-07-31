#!python
# evaluate code interpolating vtk array names as symbols
# v1.0 2023/08 paulo.ernesto
'''
usage: $0 input_path*vtk input_code*py output*vtk
'''

import sys, os.path, re
import numpy as np
import pandas as pd
# import code

# import modules from a pyz (zip) file with same name as scripts
sys.path.insert(0, os.path.splitext(sys.argv[0])[0] + '.pyz')

from _gui import usage_gui

from pd_vtk import vtk_mesh_info

class VTKDSL(str):
  _d = None
  _s = r'([a-z_]\w{1,})(\s+=\s+)?'
  def __new__(cls, s = ''):
    if s.endswith('.py') and os.path.exists(s):
      s = open(s).read()

    return super().__new__(cls, s)

  def set(self, data = None):
    self._d = data

  def sub(self, m):
    token = m.group(1)
    if (m.group(2) is not None) or (token in self._d.array_names):
      token = "self._d.cell_data['%s']%s" % m.groups('')
    return token

  def __call__(self):
    s = re.sub(self._s, self.sub, self)
    print(s)
    exec(s)

# main
def vtk_evaluate_array(input_path, input_code, output):
  import pyvista as pv
  grid = pv.read(input_path)
  dsl = VTKDSL(input_code)
  dsl.set(grid)
  dsl()
  
  vtk_mesh_info(grid)

  grid.save(output)

main = vtk_evaluate_array

if __name__=="__main__": 
  usage_gui(__doc__)
