#!python
# linear regression and classifier
# soft_db: points to be estimated
# hard_db: samples with hard data
# lito: (optional) run a distinct pass for each lito value
# engine:
# - kn: KNeighbors Regressor/Classifier
# - rn: RadiusNeighbors Regressor/Classifier
# - rn+kn: use rn first, then use kn on null cells
# mode:
# - full: replace all values with estimated
# - fill: replace nan values with estimated
# v1.0 2022/01 paulo.ernesto
'''
usage: $0 soft_db*csv,xlsx,bmf,vtk soft_condition hard_db*csv,xlsx hard_condition xyz#field:hard_db lito:hard_db variables#variable:hard_db engine%kn,rn,rn+kn kn_neighbors rn_radius mode%full,fill output*csv,xlsx,bmf,vtk display@
'''

import sys, os.path
import numpy as np
import pandas as pd
import re

# import modules from a pyz (zip) file with same name as scripts
sys.path.insert(0, os.path.splitext(sys.argv[0])[0] + '.pyz')

from _gui import usage_gui, log, commalist, pd_load_dataframe, pd_save_dataframe, pd_detect_xyz

from sklearn.neighbors import NearestNeighbors, RadiusNeighborsRegressor, RadiusNeighborsClassifier, KNeighborsClassifier, KNeighborsRegressor


def pd_linear_model_variables(df0, db0_lito, df1, df1_xyz, db1_lito, variables, engine, kn_neighbors, rn_radius, mode = None):
  li = [None]
  if db0_lito and db1_lito:
    if db0_lito in df0 and db1_lito in df1:
      li = list(set(df0[db0_lito].str.lower().unique()).intersection(df1[db1_lito].str.lower().unique()))

  if len(li) == 0:
    raise Exception("Block lito (%s) does not match any sample lito (%s)" % (db0_lito, db1_lito))

  vl = []
  for v in variables:
    if v in df1:
      vl.append(v)
      if v not in df0:
        df0[v] = pd.Series(dtype=df1[v].dtype)

  if len(vl) == 0:
    raise Exception("No valid soft data variables")

  for ri in li:
    df0r = None
    df1r = None
    if ri is None:
      df0r = df0
      df1r = df1
    elif str(ri) == 'nan':
      # nan == nan evaluates to false
      bi = np.isnan(df0[db0_lito])
      df0r = df0.loc[bi]
      bi = np.isnan(df1[db1_lito])
      df1r = df1.loc[bi]
    else:
      bi = df0[db0_lito].str.lower() == ri
      df0r = df0.loc[bi]
      bi = df1[db1_lito].str.lower() == ri
      df1r = df1.loc[bi]

    if len(df0r) == 0:
      log("no soft samples for",db0_lito,"=",ri)
      continue
    if len(df1r) == 0:
      log("no hard samples for",db1_lito,"=",ri)
      continue
    if db0_lito:
      log(db0_lito,"=",ri)

    if df0r.empty:
      continue

    for v in vl:
      m = mode == 'fill'
      for e in engine.split('+'):
        s = pd_linear_model(df0r, df1r, df1_xyz, v, m, e, rn_radius, kn_neighbors)
        df0.loc[s.index, v] = s
        # mode is always fill if we doing a second pass
        m = True

  return vl

def r_predict_workaround(r, radius, df0v, df1v):
  # workaround for sklearn 0.18.1, bundled with vulcan, crashing
  # precalculate where neighbors exist
  nn = NearestNeighbors(radius=radius)
  nn.fit(df1v)
  neigh_ind = nn.radius_neighbors(df0v, return_distance=False)
  bi = np.array([len(_) > 0 for _ in neigh_ind])
  d = np.full(len(df0v), np.nan)
  if np.any(bi):
    d[bi] = r.predict(df0v[bi])
  return d
  #return np.full(len(df0v), np.nan).put(bi, rmat)

def pd_linear_model(df0, df1, df1_xyz, variable, fill = False, engine = None, radius = None, n_neighbors = None, weights = None):

  if not radius:
    radius = 1.0
  else:
    radius = float(radius)
  
  if not weights:
    weights = 'distance'

  if not n_neighbors:
    n_neighbors = 5
  else:
    n_neighbors = int(n_neighbors)

  if df1_xyz is None:
    df1_xyz = pd_detect_xyz(df1)

  df0_xyz = df1_xyz

  if set(df1_xyz).isdisjoint(df0.columns):
    # special case: soft xyz is not equal hard xyz
    df0_xyz = pd_detect_xyz(df0)
    while len(df0_xyz) > len(df1_xyz):
      df0_xyz.pop()

  log("soft_xyz: %s, hard_xyz: %s" % (str.join(',', df0_xyz),str.join(',',df1_xyz)))
  
  df0v = df0[df0_xyz].dropna()

  df1v = df1[df1_xyz + [variable]].dropna()

  if n_neighbors > len(df1v):
    n_neighbors = len(df1v)

  r = None
  if not engine or engine == 'kn':
    if df1[variable].dtype.num == 17:
      engine = 'knc'
    else:
      engine = 'knr'
  elif engine == 'rn':
    if df1[variable].dtype.num == 17:
      engine = 'rnc'
    else:
      engine = 'rnr'

  if engine == 'rnr':
    log("using radius neighbors regressor (%g) for %s, %s weights" % (radius, variable, weights))
    r = RadiusNeighborsRegressor(radius, weights=weights)
  if engine == 'rnc':
    log("using radius neighbors classifier (%g) for %s, %s weights" % (radius, variable, weights))
    r = RadiusNeighborsClassifier(radius, weights=weights, outlier_label='n')
  if engine == 'knr':
    log("using k neighbors regressor (%g) for %s, %s weights" % (n_neighbors, variable, weights))
    r = KNeighborsRegressor(n_neighbors, weights=weights)
  if engine == 'knc':
    log("using k neighbors classifier (%g) for %s, %s weights" % (n_neighbors, variable, weights))
    r = KNeighborsClassifier(n_neighbors, weights=weights)

  if r is None:
    raise Exception("invalid engine")

  rmat = None
  log("fit samples = %d, predict samples = %d" % (len(df1v),len(df0v)))

  if len(df1v):
    n = df1v.shape[1] - 1
    t = np.take(df1v.values, n, 1)
    if engine[-1] == 'r':
      t = np.asfarray(t)
    r.fit(df1v.iloc[:, :n].values, t)
    if weights == 'distance' and sys.hexversion < 0x3080000 and engine.startswith('rn'):
      # workaround for older sklearn
      rmat = r_predict_workaround(r, radius, df0v, df1v[df1_xyz])
    else:
      rmat = r.predict(df0v.values)

  if fill:
    d = df0.loc[df0v.index, variable]
    bi = ~ np.isnan(d)
    rmat[bi] = d[bi]

  s = pd.Series(rmat, index=df0v.index)
  log(s.describe())

  return s

def db_linear_model(db0, db0_condition, db1, db1_condition, db1_xyz, lito, variables, engine, kn_neighbors, rn_radius, mode, output, display):
  log("# db_linear_model started")
  df1 = pd_load_dataframe(db1, db1_condition)
  grid = None
  df1_xyz = None
  if db1_xyz:
    df1_xyz = commalist().parse(db1_xyz).split()

  if re.fullmatch(r'[\d\.\-,;_~]+', db0):
    from pd_vtk import vtk_mesh_to_df, vtk_df_to_mesh, vtk_meshes_bb, vtk_Voxel
    bb = vtk_meshes_bb([vtk_df_to_mesh(df1)])
    grid = vtk_Voxel.from_bb_schema(bb, db0)
    df0 = vtk_mesh_to_df(grid)
    #from voxelbase import VoxelBase
    #v = VoxelBase.from_schema(df1, db0)
    #df0 = v.to_df()
  elif db0.endswith('vtk'):
    from pd_vtk import pv_read, vtk_mesh_to_df
    grid = pv_read(db0)
    df0 = vtk_mesh_to_df(grid)
    if db0_condition:
      df0.query(db0_condition, True)
  else:
    df0 = pd_load_dataframe(db0, db0_condition)
  vl = variables.split(';')
  pd_linear_model_variables(df0, lito, df1, df1_xyz, lito, vl, engine, kn_neighbors, rn_radius, mode)

  if output.endswith('vtk'):
    if not grid:
      from pd_vtk import vtk_df_to_mesh
      grid = vtk_df_to_mesh(df0)
    for v in vl:
      grid.cell_data[v] = df0[v]
    grid.save(output)
  
  elif output:
    pd_save_dataframe(df0, output)
  
  else:
    print(df0.to_string())

  if int(display):
    from pd_vtk import vtk_df_to_mesh, vtk_plot_meshes
    mesh = vtk_df_to_mesh(df0)
    vtk_plot_meshes(mesh, scalars=vl[0])

  log("finished")

main = db_linear_model

if __name__=="__main__":
  usage_gui(__doc__)
