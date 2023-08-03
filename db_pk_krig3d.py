#!python
# 3d data krigging
# v1.0 07/2020 paulo.ernesto
'''
usage: $0 hard_data*csv,xlsx x:hard_data y:hard_data z:hard_data v:hard_data variogram_model%linear,power,gaussian,spherical,exponential,hole-effect variogram_parameters anisotropy_scaling=1,2,1*2 anisotropy_angle=0*0*0,0*0*90,0*90*0,90*0*0 soft_data*csv output*csv,xlsx plot_result@1 output_plot*png
'''
import sys, os.path, re
# import modules from a pyz (zip) file with same name as scripts
sys.path.append(os.path.splitext(sys.argv[0])[0] + '.pyz')

from _gui import usage_gui, pd_load_dataframe, pd_save_dataframe, pd_detect_xyz

import numpy as np
import pandas as pd

def pd_points_3d(data, block_size):
  from itertools import product
  gmin = np.floor(data.min(0)) - 1 
  gmax = np.ceil(data.max(0)) + 1

  print("grid min %.2f,%.2f,%.2f max %.2f,%.2f,%.2f" % (gmin[0],gmin[1],gmin[2], gmax[0],gmax[1],gmax[2]))
  
  return pd.DataFrame(product(np.arange(gmin[0], gmax[0], block_size), np.arange(gmin[1], gmax[1], block_size), np.arange(gmin[2], gmax[2], block_size)), columns=['x','y','z'])

class PK(dict):
  ''' pykrige kriging engine '''
  def __init__(self, variogram_model, variogram_parameters = None, anisotropy_scaling = None, anisotropy_angle = None):
    self['variogram_model'] = variogram_model
    
    if variogram_parameters:
      self['variogram_parameters'] = eval(variogram_parameters)

    if anisotropy_scaling:
      anisotropy_scaling = list(map(float, anisotropy_scaling.split('*')))
      if len(anisotropy_scaling) == 1:
        anisotropy_scaling = anisotropy_scaling * 2
    else:
      anisotropy_scaling = [1.0, 1.0]
    self['anisotropy_scaling'] = anisotropy_scaling
    
    if anisotropy_angle:
      anisotropy_angle = list(map(int, anisotropy_angle.split('*')))
      while len(anisotropy_angle) < 3:
        anisotropy_angle.append(anisotropy_angle[-1])
    else:
      anisotropy_angle = [0, 0, 0]

    self['anisotropy_angle'] = anisotropy_angle
    self['algorithm'] = 'ordinary'

  def __getattr__(self, name):
    return self.get(name)

  def krig3d(self, samples, points):
    # Create the 3D ordinary kriging object and solves for the three-dimension kriged
    ka = None
    k3d = []
    if self.algorithm == 'ordinary':
      from pykrige.ok3d import OrdinaryKriging3D
      # OrdinaryKriging3D(x, y, z, val, variogram_model='linear', variogram_parameters=None, variogram_function=None, nlags=6, weight=False, anisotropy_scaling_y=1.0, anisotropy_scaling_z=1.0, anisotropy_angle_x=0.0, anisotropy_angle_y=0.0, anisotropy_angle_z=0.0, 
      # verbose=False, enable_plotting=False, exact_values=True, pseudo_inv=False, pseudo_inv_type='pinv')
      ka = OrdinaryKriging3D(samples[:, 0], samples[:, 1], samples[:, 2], samples[:, 3], self.variogram_model, self.variogram_parameters, anisotropy_scaling_y=self['anisotropy_scaling'][0], anisotropy_scaling_z=self['anisotropy_scaling'][1], anisotropy_angle_x=self['anisotropy_angle'][0], anisotropy_angle_y=self['anisotropy_angle'][1], anisotropy_angle_z=self['anisotropy_angle'][2])
    if self.algorithm == 'universal':
      # UniversalKriging3D(x, y, z, val, variogram_model='linear', variogram_parameters=None, variogram_function=None, nlags=6, weight=False, anisotropy_scaling_y=1.0, anisotropy_scaling_z=1.0, anisotropy_angle_x=0.0, anisotropy_angle_y=0.0, anisotropy_angle_z=0.0,
      # drift_terms=None, specified_drift=None, functional_drift=None, 
      # verbose=False, enable_plotting=False, exact_values=True, pseudo_inv=False, pseudo_inv_type='pinv')
      from pykrige.uk3d import UniversalKriging3D
      ka = UniversalKriging3D(samples[:, 0], samples[:, 1], samples[:, 2], samples[:, 3], self.variogram_model, self.variogram_parameters, anisotropy_scaling_y=self['anisotropy_scaling'][0], anisotropy_scaling_z=self['anisotropy_scaling'][1], anisotropy_angle_x=self['anisotropy_angle'][0], anisotropy_angle_y=self['anisotropy_angle'][1], anisotropy_angle_z=self['anisotropy_angle'][2])
    
    if ka is not None:
      k3d, ss3d = ka.execute('points', *points)
      print(pd.Series(k3d).describe())
      ka.print_statistics()
    
    return k3d


def db_pk_krig3d(hard_data, x, y, z, v, variogram_model, variogram_parameters, anisotropy_scaling, anisotropy_angle, soft_data, output, plot_result, plot_output):
  #variogram_parameters, anisotropy_scaling, anisotropy_angle = sanitize_krig_parameters(variogram_parameters, anisotropy_scaling, anisotropy_angle)

  df_hard = pd_load_dataframe(hard_data)
  samples = df_hard[[x,y,z,v]].dropna().values

  if not soft_data:
    soft_data = '10'
  df_soft = None
  if re.fullmatch(r'[\d\.\-,;_~]+', soft_data):
    df_soft = pd_points_3d(samples, float(soft_data))
  else:
    df_soft = pd_load_dataframe(soft_data)

  xyz = pd_detect_xyz(df_soft)
  points = np.asfarray(df_soft[xyz].values.T)

  #print("grid %d,%d,%d" % (len(gridx), len(gridy), len(gridz)))
  #kr = pk_krig3d(samples, KP(variogram_model, variogram_parameters, anisotropy_scaling, anisotropy_angle), points)
  pk = PK(variogram_model, variogram_parameters, anisotropy_scaling, anisotropy_angle)
  kr = pk.krig3d(samples, points)
  print("krig result", kr.shape)
  df_soft[v] = kr
  if output:
    # if output.endswith('bmf'):
    #   odf.insert(3, 'xlength', block_size)
    #   odf.insert(3, 'ylength', block_size)
    #   odf.insert(3, 'zlength', block_size)
    pd_save_dataframe(df_soft, output)
    
  if int(plot_result):
    from db_voxel_view import pd_voxel_view, df2a3d
    pd_voxel_view(df2a3d(df_soft, v), samples, plot_output)

main = db_pk_krig3d

if __name__ == '__main__':
  usage_gui(__doc__)
