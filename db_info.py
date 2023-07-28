#!python
# display general information about a supported data file
# v1.0 2021/01 paulo.ernesto

'''
usage: $0 input_files#files*csv,xlsx,vtk,vtm,glb,shp,tif,tiff,msh,obj,dxf,dwg,dm,bmf,00t display@
'''
import sys, os.path
import pandas as pd
import numpy as np
import re

# import modules from a pyz (zip) file with same name as scripts
sys.path.insert(0, os.path.splitext(sys.argv[0])[0] + '.pyz')

from _gui import usage_gui, commalist, pd_load_dataframe, pd_load_shape, pyd_zip_extract, table_name_selector

pyd_zip_extract()

def df_to_raster(df):
  print(df)
  nx = None
  if 'xc' in df:
    nx = int(df['xc'].max()) + 1
  else:
    nx = int(df['x'].max()) + 1
  ny = None
  if 'yc' in df:
    ny = int(df['yc'].max()) + 1
  else:
    ny = int(df['y'].max()) + 1
  nc = sum(map(str.isnumeric, df.columns))
  # agregate all channels into a single mean band
  r = None
  if nc > 1:
    r = np.mean([df[str(i)] for i in range(nc)], 0, dtype=np.float_)
  else:
    df['0'].values.astype(np.float)
  return r.reshape((nx,ny))

def pd_info(df):
  if 'layer' in df:
    layers = df['layer'].unique()
    print(len(layers), 'layers')
    print(layers)
  print(df.shape[0], 'records')
  print(df.shape[1], 'columns')
  print(*df.columns)
  print(*df.dtypes)
  print('# head')
  print(df.head().to_string(index=False))
  print('# tail')
  print(df.tail().to_string(index=False))
  if not (df.empty or df.size > 999999):
    print('# describe')
    print(df.describe().to_string())


def main(input_files, display = False):
  meshes = []
  raster = []
  for fp in commalist().parse(input_files).split():
    fp, table_name = table_name_selector(fp)
    mesh = None
    if re.search(r'vt(k|p|m)$', fp, re.IGNORECASE):
      from pd_vtk import pv_read, vtk_mesh_info
      mesh = vtk_mesh_info(pv_read(fp))
    elif re.search(r'gl(b|tf)$', fp, re.IGNORECASE):
      from pd_vtk import pv_read
      for mesh in pv_read(fp):
        meshes.append(vtk_mesh_info(mesh))
    else:
      df = pd_load_dataframe(fp)
      pd_info(df)
      if int(display):
        if re.search(r'(png|tiff?)$', fp, re.IGNORECASE):
          raster.append(df_to_raster(df))
        elif int(display):
          from pd_vtk import vtk_df_to_mesh
          mesh = vtk_df_to_mesh(df)
    if mesh is not None:
      if table_name in mesh.array_names:
        arr = mesh.get_array(table_name)
        if arr.dtype.num < 17:
          mesh.set_active_scalars(table_name)
      meshes.append(mesh)

    print('')
  if int(display):
    if len(meshes):
      from pd_vtk import vtk_plot_meshes
      vtk_plot_meshes(meshes, cmap='Paired')
    if len(raster):
      import matplotlib.pyplot as plt
      for r in raster:
        plt.figure()
        plt.imshow(r)
      plt.show()

if __name__=="__main__":
  usage_gui(__doc__)
