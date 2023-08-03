#!python

import numpy as np
import pandas as pd

def desurvey_hole(depth, phi, theta, matrix = False, downhole = False):
  # get lengths of the separate segments 
  lengths = np.array(depth)
  #np.subtract(depth[1:], depth[:-1])
  lengths[1:] -= depth[:-1]
  # convert to radians
  phi = np.deg2rad(phi)
  # downhole have unsigned dip values which are shorthand for negative
  if downhole:
    theta *= -1

  # in spherical coordinates theta is measured from zenith down 
  # you are measuring it from horizontal plane up 
  theta = np.deg2rad(90. - theta)

  # get x, y, z from known formulae
  x = lengths*np.sin(phi)*np.sin(theta)
  y = lengths*np.cos(phi)*np.sin(theta)
  z = lengths*np.cos(theta)

  if matrix:
    return np.column_stack((depth, x, y, z))
  else:
    # np.cumsum is employed to gradually sum resultant vectors 
    return np.column_stack((depth, np.cumsum(x), np.cumsum(y), np.cumsum(z)))

def pd_parse_hsa(dfs, hid, h, v_lut):
  s = a = None
  if hid not in dfs[0].index.levels[0]:
    print(hid, "not found in HEADER, skipped")
  else:
    if hid in dfs[1].index.levels[0]:
      s = dfs[1].loc[hid, [v_lut['depth'], v_lut['brg'], v_lut['dip']]]
    else:
      print(hid, "not found in SURVEY, using default 90°")
      s = pd.DataFrame([[0, 0, -90]], columns=[v_lut['depth'], v_lut['brg'], v_lut['dip']])

    if hid not in dfs[2].index.levels[0]:
      print(hid, "not found in ASSAY, skipped")
      # TODO: use survey intervals
    else:
      a = dfs[2].loc[hid]

      # special case: assay intervals overshoots survey intervals
      if a.iloc[-1].loc[v_lut['to']] > s.iloc[-1].loc[v_lut['depth']]:
        row = s.iloc[-1].copy()
        row[v_lut['depth']] = a.iloc[-1].loc[v_lut['to']]
        s = pd.concat((s, row))
  return h, s, a

def desurvey_line3d(dfs, v_lut):
  odf = pd.DataFrame()
  for df in dfs:
    df.set_index(v_lut['hid'], True, False, True)
    df.set_index(pd.RangeIndex(0, len(df)), False, True, True)
  for i0, row0 in dfs[0].iterrows():
    h, s, a = pd_parse_hsa(dfs, i0[0], row0, v_lut)
    if a is None:
      continue
    dh = Drillhole(h.values, s.values)
    for ri,rd in a.iterrows():
      #midxyz = dh.getxyz((rd[v_lut['from']] + rd[v_lut['to']]) / 2)
      for v in ['from','to']:
        d = dh.getxyz(rd[v_lut[v]])
        odf = odf.append(pd.Series(d, name=i0))
    #df.insert(0, v_lut['hid'], i0[0])

  return odf

class Drillhole(object):
  _collar = None
  _survey = None
  _assay = None
  _xyz = None
  def __init__(self, collar = None, survey = None, downhole = True):
    super().__init__()
    if collar is None:
      collar = np.zeros(3)

    self._collar = np.array(collar)

    if survey is not None:
      self._survey = np.array(survey)
      self._xyz = np.add(desurvey_hole(self._survey[:,0],self._survey[:,1],self._survey[:,2], downhole=downhole), [0] + self._collar.tolist())

  def getxyz(self, along = None):
    if along is None:
      return self._xyz
    v1 = np.searchsorted(self._xyz[:, 0], along)
    v0 = v1 - 1
    xyz0 = None
    xyz1 = None

    # overshoot special case
    if v1 >= self._xyz.shape[0]:
      v1 = self._xyz.shape[0] - 1

    if v0 >= v1:
      v0 = v1 - 1

    if v0 < 0:
      xyz0 = [0] + self._collar.tolist()
    else:
      xyz0 = self._xyz[v0]

    xyz1 = self._xyz[v1]
    xyz = xyz0
    d01 = None
    t01 = None
    if v0 != v1:
      d01 = np.subtract(xyz1, xyz0)
      if np.all(~np.isnan(d01)):
        if d01[0] > 0:
          t01 = (along - xyz0[0]) / d01[0]
          xyz = np.add(xyz0, np.multiply(d01, t01))

    return xyz
    
  def desurvey(self, table, vfrom = 'from', vto = 'to'):
    df = pd.DataFrame(table)
    df['mid_x'] = np.nan
    df['mid_y'] = np.nan
    df['mid_z'] = np.nan
    for i,row in df.iterrows():
      midxyz = self.getxyz((row[vfrom] + row[vto]) / 2)
      df.loc[i, ['mid_x','mid_y','mid_z']] = midxyz[1:]
    return df

def pd_plot_hole(df_header, df_survey, df_assay, output_img = None):
  import matplotlib.pyplot as plt
  from mpl_toolkits.mplot3d import Axes3D
  ds = pd.DataFrame(desurvey_hole(df_survey['DEPTH'], df_survey['AZIMUTH'], df_survey['DIP']), columns=['DEPTH','X','Y','Z'])
  dh = df_header.copy()

  dxyz = dict()
  for row in dh.index:
    hid = dh.loc[row, 'HID']
    dxyz[hid] = [[0] + dh.loc[row, ['X','Y','Z']].tolist()]
    dxyz[hid] = np.vstack((dxyz[hid], [dh.loc[row, 'DEPTH'], dh.loc[row, 'X'] + ds.loc[row, 'X'], dh.loc[row, 'Y'] + ds.loc[row, 'Y'], dh.loc[row, 'Z'] + ds.loc[row, 'Z']]))

  fig = plt.figure()

  ax = plt.subplot(131, projection='3d', azim=30, elev=15)
  for k,v in dxyz.items():
    ax.plot(v.T[1], v.T[2], v.T[3], label=k)

  plt.legend()

  ax = plt.subplot(132, projection='3d', azim=120, elev=15)
  for k,v in dxyz.items():
    ax.plot(v.T[1], v.T[2], v.T[3], label=k)

  plt.legend()

  ax = plt.subplot(133, projection='3d', azim=0, elev=0)
  for k,v in dxyz.items():
    ax.plot(v.T[1], v.T[2], v.T[3], label=k)

  plt.legend()

  plt.show()

def fill_desurvey_lut(hid = None, x = None, y = None, z = None, depth = None, brg = None, dip = None, t0 = None, t1 = None):
  v_lut = {}
  v_lut['hid'] = hid or 'BHID'
  v_lut['x'] = x or 'X'
  v_lut['y'] = y or 'Y'
  v_lut['z'] = z or 'Z'
  v_lut['depth'] = depth or 'DEPTH'
  v_lut['brg'] = brg  or 'AZIMUTH'
  v_lut['dip'] = dip or 'DIP'
  v_lut['from'] = t0 or 'FROM'
  v_lut['to'] = t1 or 'TO'
  return v_lut

if __name__=="__main__":
  dfs = []
  import sys
  for i in range(1, len(sys.argv)):
    dfs.append(pd.read_csv(sys.argv[i]))

  df = desurvey_line3d(dfs, desurvey_lut())
  print(df.to_string())
  