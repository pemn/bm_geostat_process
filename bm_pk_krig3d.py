#!python
# data krigging using pykrige
# v1.0 2022/02 paulo.ernesto
'''
usage: $0 soft_data*bmf,vtk soft_condition soft_lito:soft_data hard_data*csv hard_condition hard_lito:hard_data x:hard_data y:hard_data z:hard_data variables#variable:hard_data variogram_model%linear,power,gaussian,spherical,exponential,hole-effect variogram_parameters anisotropy_scaling=1,2,1*2 anisotropy_angle=0*0*0,0*0*90,0*90*0,90*0*0
'''
import sys, os.path, re
# import modules from a pyz (zip) file with same name as scripts
sys.path.append(os.path.splitext(sys.argv[0])[0] + '.pyz')

from _gui import usage_gui, commalist, log, bm_sanitize_condition, pd_load_dataframe, pd_save_dataframe, pd_detect_xyz

import numpy as np
import pandas as pd

from pykrige_pk import PK

def vulcan_pk_krig3d(soft_data, soft_condition, soft_lito, df_hard, hard_lito, x, y, z, variables, pk):
  import vulcan
  xyz_soft = ['xworld', 'yworld', 'zworld']

  bm = vulcan.block_model(soft_data)
  bs = bm.get_matches(bm_sanitize_condition(soft_condition))
  print(len(bs),"blocks")
  
  df_soft = pd.DataFrame(np.empty((len(bs), len(xyz_soft))), columns=xyz_soft)
  for i in range(len(xyz_soft)):
    df_soft[xyz_soft[i]] = bm.get_data(xyz_soft[i], bs)

  if hard_lito and soft_lito:
    df_soft[soft_lito] = bm.get_data(soft_lito, bs)

  vl = pk_vl(df_soft, soft_lito, df_hard, hard_lito, x, y, z, variables, pk)

  for v in vl:
    if not bm.is_field(v):
      print("creating variable", v)
      bm.add_variable(v, 'float', '-99', '')

    bm.put_data_double(v, df_soft[v].astype(np.float_), bs)

def vtk_grid_to_df(mesh):
  df0 = pd.DataFrame(mesh.cell_centers().points, columns=['x','y','z'])
  df1 = pd.DataFrame(np.transpose(mesh.cell_arrays.values()), columns=mesh.cell_arrays)
  return pd.concat([df0, df1], 1)

def vtk_pk_krig3d(soft_data, soft_condition, soft_lito, df_hard, hard_lito, x, y, z, variables, pk):
  import pyvista as pv
  mesh = pv.read(soft_data)
  df_soft = vtk_grid_to_df(mesh)
  if soft_condition:
    df_soft.query(soft_condition, True)

  vl = pk_vl(df_soft, soft_lito, df_hard, hard_lito, x, y, z, variables, pk)
  
  for v in vl:
    mesh.cell_arrays.set_array(df_soft[v], v)
  
  mesh.save(soft_data)

def pk_vl(df_soft, soft_lito, df_hard, hard_lito, x, y, z, variables, pk):
  vl = []
  for v in variables:
    if v in df_hard:
      vl.append(v)
      if v in df_soft:
        df_soft[v] = np.nan
      else:
        df_soft[v] = pd.Series(dtype=df_hard[v].dtype)

  if len(vl) == 0:
    raise Exception("No valid soft data variables")

  li = [None]
  if hard_lito and soft_lito:
    li = list(set(df_soft[soft_lito].unique()).intersection(df_hard[hard_lito].unique()))
  
  print('lito =',*li)

  for ri in li:
    df_soft_lito = None
    df_hard_lito = None
    if ri is None:
      df_soft_lito = df_soft
      df_hard_lito = df_hard
    elif str(ri) == 'nan':
      # nan == nan evaluates to false
      bi = np.isnan(df_soft[soft_lito])
      df_soft_lito = df_soft.loc[bi]
      bi = np.isnan(df_hard[hard_lito])
      df_hard_lito = df_hard.loc[bi]
    else:
      bi = df_soft[soft_lito] == ri
      df_soft_lito = df_soft.loc[bi]
      bi = df_hard[hard_lito] == ri
      df_hard_lito = df_hard.loc[bi]

    for v in vl:
      samples = df_hard_lito[[x, y, z, v]].dropna().values

      if len(samples) == 0:
        print("no soft points for %s = %s, %s" % (hard_lito,ri,v))
        continue
      
      points = np.asfarray(df_soft_lito[df_soft_lito.columns[:3]].values)
      
      if len(points) == 0:
        print("no hard samples for %s = %s, %s" % (soft_lito,ri,v))
        continue
      
      log(soft_lito,"=",ri,",",v,"; hard samples =",len(samples),"; soft points =",len(points))

      k3d = pk.krig3d(samples, points.T)
      df_soft.loc[df_soft_lito.index, v] = k3d
  
  return vl

def bm_pk_krig3d(soft_data, soft_condition, soft_lito, hard_data, hard_condition, hard_lito, x, y, z, variables, variogram_model, variogram_parameters, anisotropy_scaling, anisotropy_angle):
  pk = PK(variogram_model, variogram_parameters, anisotropy_scaling, anisotropy_angle)
  variables = commalist().parse(variables).split()

  log("# bm_pk_krig3d started")
  df_hard = pd_load_dataframe(hard_data, hard_condition)

  if soft_data.lower().endswith('bmf'):
    vulcan_pk_krig3d(soft_data, soft_condition, soft_lito, df_hard, hard_lito, x, y, z, variables, pk)
  
  if soft_data.lower().endswith('vtk'):
    vtk_pk_krig3d(soft_data, soft_condition, soft_lito, df_hard, hard_lito, x, y, z, variables, pk)


main = bm_pk_krig3d

if __name__ == '__main__':
  usage_gui(__doc__)
