#!python
# flag solid regions in a block model. export points inside solids.
# v1.1 2021/01 paulo.ernesto
# v1.0 2021/01 paulo.ernesto
'''
usage: $0 block_model*vtk,csv,xlsx regions#region*vtk,dxf,dwg,msh,obj,00t flag_var=region mode%flag3d,flag2d output*vtk display@
'''
import sys, os.path
import numpy as np
import pandas as pd
import re

# import modules from a pyz (zip) file with same name as scripts
sys.path.insert(0, os.path.splitext(sys.argv[0])[0] + '.pyz')
from _gui import usage_gui, commalist, pyd_zip_extract, pd_load_dataframe, pd_save_dataframe, df_to_nodes_faces, log

pyd_zip_extract()

from pd_vtk import pv_read, vtk_dmbm_to_ug, vtk_df_to_mesh, vtk_mesh_to_df, vtk_cells_to_flat, vtk_plot_meshes, vtk_nf_to_mesh, vtk_meshes_bb, vtk_Voxel, pv_save, Raytracer

def vtk_flag_region_2d(grid, meshes, flag_var, flag_cell = False, values = None):
  rt = Raytracer(grid, flag_cell)

  ms = []
  for n in range(len(meshes)):
    v = n + 1
    if n < len(values):
      v = values[n]
    mesh = meshes[n]
    rt.raytrace(mesh, v)

  if flag_cell:
    grid.cell_arrays[flag_var] = rt.value
  else:
    grid.point_arrays[flag_var] = rt.value

  return grid

def vtk_flag_region(grid, meshes, flag_var, flag_cell = False, values = None):
  if flag_cell:
    cv = np.full(grid.GetNumberOfCells(), '', dtype=np.object_)
  else:
    cv = np.full(grid.GetNumberOfPoints(), '', dtype=np.object_)
  
  if values is None or not isinstance(values, list):
    values = []

  for n in range(len(meshes)):
    v = n + 1
    if n < len(values):
      v = values[n]
    
    r = grid.select_enclosed_points(meshes[n], check_surface=False)
    if flag_cell:
      rc = r.ptc().get_array('SelectedPoints')
    else:
      rc = r.get_array('SelectedPoints')
    cv[rc > 0] = v
  if flag_cell:
    grid.cell_data[flag_var] = cv
  else:
    grid.point_data[flag_var] = cv

  return grid


def vtk_flag_regions(block_model, regions, flag_var, mode, output, display):
  meshes = []
  values = []
  for region in commalist().parse(regions).split():
    if not os.path.exists(region):
      log("file not found:",region)
      continue

    mesh = pv_read(region)

    values.append(os.path.splitext(os.path.basename(region))[0])
    meshes.append(mesh)

  grid = None

  if re.fullmatch(r'[\d\.\-,;_~]+', block_model):
    bb = vtk_meshes_bb(meshes)
    grid = vtk_Voxel.from_bb_schema(bb, block_model)
    grid.cells_volume('volume')
  elif re.search(r'vt.$', block_model, re.IGNORECASE):
    grid = pv_read(block_model)
  else:
    bdf = pd_load_dataframe(block_model)

    if set(['XC','YC','ZC']).issubset(bdf.columns):
      grid = vtk_dmbm_to_ug(bdf)
    else:
      grid = vtk_df_to_mesh(bdf)

  if len(grid.cell_data) == 0 and len(grid.point_data) > 0 and grid.n_points:
    grid = grid.ptc()
  flag_cell = True
  if len(meshes) and flag_var:
    if mode == 'flag2d':
      log("flag2d")
      vtk_flag_region_2d(grid, meshes, flag_var, flag_cell, values)
    else:
      log("flag3d")
      vtk_flag_region(grid, meshes, flag_var, flag_cell, values)

  if output:
    pv_save(grid, output)
  else:
    print(vtk_mesh_to_df(grid))

  if int(display):
    vtk_plot_meshes([grid] + meshes, scalars=flag_var)

main = vtk_flag_regions

if __name__=="__main__":
  usage_gui(__doc__)
