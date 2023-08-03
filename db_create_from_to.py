#!python
# create from and to field based on a single depth field
# keep_null_values: preserve -99 values in data
'''
usage: $0 input_path*csv,xlsx hid:input_path depth:input_path output*csv,xlsx keep_null_values@
'''

import sys, os.path
import numpy as np
import pandas as pd

# import modules from a pyz (zip) file with same name as scripts
sys.path.insert(0, os.path.splitext(sys.argv[0])[0] + '.pyz')

from _gui import usage_gui, pd_load_dataframe, pd_save_dataframe

def pd_create_from_to(df, v_hid, v_depth, inplace=False):
  v_from = 'from'
  v_to = 'to'
  if not inplace:
    df = df.copy()

  d_depth = 0
  d_hid = None
  a_from = df[v_depth].copy()
  df[v_to] = df[v_depth].copy()
  for i,row in df.iterrows():
    if row[v_hid] != d_hid:
      a_from[i] = 0
      d_hid = row[v_hid]
    else:
      a_from[i] = d_depth

    d_depth = row[v_depth]
  df[v_from] = a_from
  return df

# main
def db_create_from_to(input_path, v_hid, v_depth, output, keep_null_values):

  df = pd_load_dataframe(input_path)

  pd_create_from_to(df, v_hid, v_depth, True)

  if not int(keep_null_values):
    df.fillna(-99, inplace=True)

  if output:
    pd_save_dataframe(df, output)
  else:
    print(df.to_string(index=False))

main = db_create_from_to

if __name__=="__main__": 
  usage_gui(__doc__)
