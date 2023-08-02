#!python
# weighted fivenum descriptive statistics (min,mean,max,std,var)
# input: a database in a known format (csv, xls, bmf, 00t, 00g, isis, msh, dm, vtk)
# condition: optional expression to filter. syntax is vulcan (bmf) or python (csv,isis)
# lito: one or more classification variables that will break data into multiple tables (optional)
# weight: variable that will be used as the weight on averages and sums (optional)
# variables: a list of grade variables to analise
# output: (optional) file to write the result: csv or xlsx
# keep_null: dont exclude -99 values from calculations
"""
usage: $0 input*bmf,csv,xlsx,isis,00t,00g,msh,dm,vtk condition lito:input weight:input variables#variable:input output*csv,xlsx keep_null@
"""

import sys, os.path
import pandas as pd

# import modules from a pyz (zip) file with same name as scripts
sys.path.insert(0, os.path.splitext(sys.argv[0])[0] + '.pyz')

from _gui import usage_gui, table_field, commalist, pd_load_dataframe, pd_save_dataframe
from bm_breakdown import pd_breakdown
"""
def pd_save_breakdown_panel(odf, output, lito=None):
  if pd.__version__ < '0.20':
    pn = dict()
    for row in odf.index:
      df = odf.xs(row)
      df.rename(lito, inplace=True)
      pn[row] = df.to_frame().T.stack(0)

    pd.Panel(pn).to_excel(output)
  else:
    pd_save_dataframe(odf, output)
"""
def var_fivenum(df, lito, weight, v):
  # breakdown_template
  bt = [[_] for _ in lito]
  bt.append(['variable=variable','text',v])

  # hardcoded output column with sum of weights
  for w in weight:
    bt.append([w + '=' + w, 'sum'])
  for f in ['count', 'mean', 'min', 'q1', 'q2', 'q3', 'max', 'var', 'std']:
    bt.append([v + '=' + f, f] + weight)
  return pd_breakdown(df, bt)

def pd_fivenum_weight(idf, lito, vl_a, weight):
  odf = pd.DataFrame()
  # special case: no group column was selected
  if len(lito) == 0:
    lito = ["null"]
    idf.insert(0, 'null', 0)
  else:
    lito = lito.split(',')
  print("#", *vl_a)
  for v in vl_a:
    df = var_fivenum(idf, lito, weight, v)
    odf= odf.append(df)

  return odf
# calculate fivenum (min,q2,mean,q3,max) for a block model
# broken by lithology
# return a panda Panel with one DataFrame for each litho
def bm_fivenum_weight(input_path, condition, lito, weight, variables, output, keep_null = False):
  print("# bm_fivenum_weight", input_path)
  
  vl_a = variables.split(';')
  weight = weight.split(',') if weight else []

  if input_path.lower().endswith('.isis'):
    idf = pd_load_dataframe(input_path, condition, table_field(vl_a[0], True), None, keep_null)
    lito, weight, variables = table_field([lito, weight, variables])
  else:
    idf = pd_load_dataframe(input_path, condition, None, (lito.split(',') if lito else []) + weight + vl_a, keep_null)

  if len(idf) == 0:
    raise RuntimeError("Zero input data rows")

  odf = pd_fivenum_weight(idf, lito, vl_a, weight)

  if output:
    pd_save_dataframe(odf, output)
  else:
    # screen
    print(odf.to_string(na_rep = ""))

main = bm_fivenum_weight

if __name__=="__main__": 
  usage_gui(__doc__)
