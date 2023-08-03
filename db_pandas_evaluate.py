#!python
# evaluate code in a dataframe, and then either filter the rows or store the result in a column
# also can be used to convert between different files formats
# input_path: a file in any supported format
# expressions: (optional) pairs of code, name to evaluate. check manual for details.
# - code: (optional) a python expression or a column name
# - name: (optional) a column name
# output: path to save result in any supported format
# fill_null_values: replace NaN (null values) with -99. Useful in Vulcan data files.
# v2.0 2021/04 paulo.ernesto
'''
usage: $0 input_path*csv,xls,xlsx,xlsm,bmf,00t,isis,arch_d,dm,dxf,tif,tiff,jsdb,shp,obj,msh,vtk expressions#code#name:input_path output_path*csv,xlsx,00t,tif,tiff,jsdb,shp,obj,msh fill_null_values@
'''

import sys, os.path
import numpy as np
import pandas as pd
import re

# import modules from a pyz (zip) file with same name as scripts
sys.path.insert(0, os.path.splitext(sys.argv[0])[0] + '.pyz')

from _gui import usage_gui, pd_load_dataframe, pd_save_dataframe, commalist

def pd_evaluate(df, code, name = None):
  # column rename mode
  if name and code in df:
    if name in df:
      df[name] = df[code]
    else:
      df.rename(columns=dict(((code, name),)), inplace=True)
  # NaN replace mode
  elif ' || ' in code:
    t = code.split(' || ')
    if set(t).issubset(df.columns):
      if not name:
        name = t[0]
      elif name not in df:
        df[name] = df[t[0]]
      # Python 3.5 pandas does not support pd.notna
      df[name] = df[t[0]].where(~np.isnan(df[t[0]]), df[t[1]])

  # text replace mode
  elif code.startswith('s/'):
    t = code.split('/')
    is_regex = True
    if len(t) >= 4 and t[3] == 'n':
      is_regex = False
      t[1] = float(t[1])
      t[2] = float(t[2])

    if not name:
      df.replace(t[1], t[2], True, None, is_regex)
    elif name in df:
      df[name].replace(t[1], t[2], True, None, is_regex)
  # text evaluate mode
  elif name and code:
    df[name] = df.eval(code, engine='python')
  # text filter mode
  elif code:
    if ' = ' in code:
      df.eval(code, engine='python', inplace=True)
    else:
      df.query(code, engine='python', inplace=True)
  elif name:
    # ensure columns exist
    if name not in df:
      df[name] = np.nan

# main
def db_pandas_evaluate(input_path, expressions, output_path = None, fill_null_values = False):
  df = None

  for row in commalist().parse(expressions):
    code = ''
    name = ''
    if len(row) > 1:
      code, name = row
    elif len(row) > 0:
      code = row[0]
    if df is None:
      # special case: first expression is a filter
      # apply on the database load to leverage existing performace hacks
      if code and not (name or code.startswith('s/')):
        df = pd_load_dataframe(input_path, code)
        continue
      else:
        df = pd_load_dataframe(input_path)

    pd_evaluate(df, code, name)

  if int(fill_null_values):
    df.fillna(-99, inplace=True)

  if output_path:
    pd_save_dataframe(df, output_path)
  else:
    print(df.to_string(index=False))

main = db_pandas_evaluate

if __name__=="__main__": 
  usage_gui(__doc__)
