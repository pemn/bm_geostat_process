#!python
# Create xyz coordinates for ASSAY intervals
# check manual for usage and important details
# header: collar of hole
# survey: directions of hole
# assay: (optional) intervals with lito and grades
# display: render the hole in a 3d window
# downhole: if checked positive dip values are down
# v1.0 12/2020 paulo.ernesto
'''
usage: $0 header*csv,xlsx hid:header x:header y:header z:header survey*csv,xlsx depth:survey azimuth:survey dip:survey assay*csv,xlsx from:assay to:assay output*csv,xlsx display@ downhole@
'''

import sys, os.path
import numpy as np
import pandas as pd

# import modules from a pyz (zip) file with same name as scripts
sys.path.insert(0, os.path.splitext(sys.argv[0])[0] + '.pyz')

from _gui import usage_gui, pd_load_dataframe, pd_save_dataframe, pd_synonyms, log
from db_create_from_to import pd_create_from_to
from surveyholes import Drillhole, pd_parse_hsa

def pv_plot_hole_lines(df, xyz, hid = None):
  log("display")
  try:
    import pyvista as pv
  except:
    log("pyvista not available")
    return
  p = pv.Plotter()
  p.add_axes()
  if hid is not None:
    df = df.set_index(hid)
  for row in df.index:
    df_row = df.loc[row]
    mesh = pv.Spline(df_row[xyz].to_numpy(np.float_))
    p.add_mesh(mesh)
  p.show()


def pd_desurvey_straight(dfs, vhid, vx, vy, vz, vdepth, vbrg, vdip, vfrom, vto, xyz = None, downhole = False):
  if xyz is None:
    xyz = ['mid_x','mid_y','mid_z']
    
  v_lut = {}
  v_lut['hid'] = vhid
  v_lut['x'] = vx
  v_lut['y'] = vy
  v_lut['z'] = vz
  v_lut['depth'] = vdepth
  v_lut['brg'] = vbrg
  v_lut['dip'] = vdip
  v_lut['from'] = vfrom
  v_lut['to'] = vto


  # synonyms
  if not v_lut['hid']:
    v_lut['hid'] = pd_synonyms(dfs[0], 'hid')
  if not v_lut['x']:
    v_lut['x'] = pd_synonyms(dfs[0], 'x')
  if not v_lut['y']:
    v_lut['y'] = pd_synonyms(dfs[0], 'y')
  if not v_lut['z']:
    v_lut['z'] = pd_synonyms(dfs[0], 'z')
  if not v_lut['depth']:
    v_lut['depth'] = pd_synonyms(dfs[1], 'depth')
  if not v_lut['brg']:
    v_lut['brg'] = pd_synonyms(dfs[1], 'brg')
  if not v_lut['dip']:
    v_lut['dip'] = pd_synonyms(dfs[1], 'dip')
  
  if len(dfs) == 2:
    dfs.append(pd_create_from_to(dfs[-1], vhid, vdepth))

  if not v_lut['from']:
    v_lut['from'] = pd_synonyms(dfs[2], 'from')
  if not v_lut['to']:
    v_lut['to'] = pd_synonyms(dfs[2], 'to')

  for df in dfs:
    df.set_index(v_lut['hid'], drop=True, append=False, inplace=True)
    df.set_index(pd.RangeIndex(0, len(df)), drop=False, append=True, inplace=True)

  # initialize output columns
  for c in xyz[::-1]:
    if c not in dfs[2]:
      dfs[2].insert(0, c, np.nan)

  odf = pd.DataFrame()
  lines = []
  
  for i0, row0 in dfs[0].iterrows():
    h, s, a = pd_parse_hsa(dfs, i0[0], row0[[v_lut['x'],v_lut['y'],v_lut['z']]], v_lut)
    if a is None:
      continue
    log(i0[0])
    dh = Drillhole(h.values, s.values, downhole)
    lines.append(np.delete(dh.getxyz(), 0, 1))
    df = dh.desurvey(a, v_lut['from'], v_lut['to'])
    df.insert(0, v_lut['hid'], i0[0])
    #odf = odf.append(df)
    odf = pd.concat((odf,df))

  return odf

def db_desurvey_straight(header, vhid, vx, vy, vz, survey, vdepth, vbrg, vdip, assay, vfrom, vto, output, display = False, downhole = False):
  xyz = ['mid_x','mid_y','mid_z']
  dfs = []
  dfs.append(pd_load_dataframe(header, keep_null=True))
  dfs.append(pd_load_dataframe(survey, keep_null=True))
  if assay:
    dfs.append(pd_load_dataframe(assay, keep_null=True))

  odf = pd_desurvey_straight(dfs, vhid, vx, vy, vz, vdepth, vbrg, vdip, vfrom, vto, xyz, int(downhole))

  if output:
    pd_save_dataframe(odf, output)
  else:
    print(odf.to_string())

  if int(display):
    pv_plot_hole_lines(odf, xyz, vhid)

main = db_desurvey_straight

if __name__=="__main__":
  usage_gui(__doc__)
