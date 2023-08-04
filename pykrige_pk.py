#python

import numpy as np
import pandas as pd

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

