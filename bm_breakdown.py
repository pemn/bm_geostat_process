#!python
# create data pivot tables from a database
# input: bmf (vulcan block model), isis (vulcan database) or  csv (ascii)
# condition: optional expression to filter. syntax is vulcan or python (csv,isis)
# variables: variables to generate the pivot table in the breakdown format
# output: optional files to write the result, csv and/or xlsx
# keep_null: dont exclude -99 values from calculations
# v1.1 04/2018 paulo.ernesto
# v1.0 12/2017 paulo.ernesto
'''
usage: $0 input*bmf,csv,xlsx,json,isis,dm,tif,tiff,00t,obj,vtk condition variables#variable:input#type=breakdown,count,sum,mean,min,max,var,std,sem,q1,q2,q3,p10,p90,major,list,rank,text,group,distinct#weight:input keep_null@ output*csv,xlsx
'''
'''
Copyright 2017 - 2021 Vale

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''

import sys, os.path
import numpy as np
import pandas as pd

# import modules from a pyz (zip) file with same name as scripts
sys.path.insert(0, os.path.splitext(sys.argv[0])[0] + '.pyz')

from _gui import usage_gui, pd_load_dataframe, table_field, commalist, pd_save_dataframe, log

# magic character that will be the label separator
_LABEL = '='

def bm_breakdown(input_path, condition, vl_s, keep_null = False):
  ''' 
  File entry point for the breakdown process
  Input: path to input file, condition string, variable list string
  Output: dataframe with result
  '''
  vl_a = commalist().parse(vl_s)
  log("# bm_breakdown", input_path)
  if input_path.lower().endswith('.isis'):
    idf = pd_load_dataframe(input_path, condition, table_field(vl_a[0][0], True), None, keep_null)
    vl_a = table_field(vl_a)
  else:
    vl_s = set()
    for row in vl_a:
      # extract all unique variables from the breakdown mask
      # skip the operation column
      vl_s.update([row[j].split(_LABEL)[0] for j in range(len(row)) if j != 1])

    idf = pd_load_dataframe(input_path, condition, None, vl_s, keep_null)
  log("# finished")
  return pd_breakdown(idf, vl_a)

def pd_groupby_loop_350(idf, vl_b, col_b, vl_v):
  r = []
  # workaround for the pandas behavior of excluding rows with nan classificators
  for v in vl_b:
    if(idf[v].hasnans):
      idf[v].fillna(-99, inplace=True)

  r_row = []
  if vl_b:
    for gp,df in idf.groupby(vl_b):
      if not isinstance(gp, tuple):
        gp = [gp]
      r_row.append(gp)
      r.append(pd_breakdown_fn(df, vl_v))
    if r_row:
      r_row = pd.MultiIndex.from_arrays(list(zip(*r_row)), names=col_b)
  else:
    r_row.append('')
    r.append(pd_breakdown_fn(idf, vl_v))
  return r, r_row

def pd_groupby_loop_380(idf, vl_b, col_b, vl_v):
  r = []
  r_row = []
  if vl_b:
    for gp,df in idf.groupby(vl_b, dropna=False):
      if not isinstance(gp, tuple):
        gp = [gp]
      r_row.append(gp)
      r.append(pd_breakdown_fn(df, vl_v))
    if r_row:
      r_row = pd.MultiIndex.from_arrays(list(zip(*r_row)), names=col_b)
  else:
    r_row.append('')
    r.append(pd_breakdown_fn(idf, vl_v))
  return r, r_row

def pd_breakdown(idf, vl_a):
  '''
  Main worker function for the breakdown process
  Input: dataframe with input data, 2d list of breakdown template
  Output: dataframe with result
  '''
  vl_b = []
  vl_v = []

  col_b = []
  col_v = []

  for v in vl_a:
    # create a copy of the row to avoid modifing the input
    v = list(v)
    v0 = v[0]
    name = ''

    # handle alternative column names. Ex.: volume=total_volume
    if len(v0) and v0.find(_LABEL) > 0:
      v0, name = v0.split(_LABEL)

    if len(v) == 1 or v[1] == 'breakdown' or len(v[1]) == 0:
      vl_b.append(v0)
      if name:
        col_b.append(name)
      else:
        col_b.append(v0)
    elif v[1] == 'group':
      # similar to breakdown but respecting local value domains
      g0 = np.cumsum(idf[v0] != idf[v0].shift())
      g1 = pd.Series.drop_duplicates(g0)
      g1[:] = g1.index
      g2 = g1.reindex(idf.index, method='ffill')
      #vl_b.append(['%s_%d' % _ for _ in zip(idf.loc[g2, v0].values, g0)])
      vl_b.append(idf.loc[g2, v0].values)
      vl_b.append(g0)
      if name:
        col_b.append(name)
      else:
        col_b.append(v0)
      col_b.append(v0 + '#')
    else:
      if name:
        col_v.append(name)
        vl_v.append([v0] + v[1:])
      elif v[1] == 'text':
        col_v.append(v0)
        vl_v.append(v)
      else:
        col_v.append(v0 + ' ' + v[1])
        vl_v.append(v)
  if len(vl_v) == 0 and len(vl_b) > 0:
    vl_v = [['','text',''] for _ in vl_b]
    col_v = ['' for _ in vl_b]

  if sys.hexversion < 0x3080000:
    r, r_row = pd_groupby_loop_350(idf, vl_b, col_b, vl_v)
  else:
    r, r_row = pd_groupby_loop_380(idf, vl_b, col_b, vl_v)

  return(pd.DataFrame(r, index=r_row, columns=col_v))

def weighted_quantiles(a, q=[0.25], w=None):
    """
    Calculates percentiles associated with a (possibly weighted) array

    Parameters
    ----------
    a : array-like
        The input array from which to calculate percents
    q : array-like
        The percentiles to calculate (0.0 - 100.0)
    w : array-like, optional
        The weights to assign to values of a.  Equal weighting if None
        is specified

    Returns
    -------
    values : np.array
        The values associated with the specified percentiles.  
    """
    # Standardize and sort based on values in a
    q = np.array(q)
    if w is None:
        w = np.ones(a.size)
    vn = ~(np.isnan(a) | np.isnan(w))
    # early exit for fully masked data
    if not vn.any():
      return [None]
    a = a[vn]
    w = w[vn]
    idx = np.argsort(a)
    a_sort = a[idx]
    w_sort = w[idx]

    # Get the cumulative sum of weights
    ecdf = np.cumsum(w_sort)

    # Find the percentile index positions associated with the percentiles
    p = q * (np.nansum(w) - 1)

    # Find the bounding indices (both low and high)
    idx_low = np.searchsorted(ecdf, p, side='right')
    idx_high = np.searchsorted(ecdf, p + 1, side='right')
    idx_high[idx_high > ecdf.size - 1] = ecdf.size - 1

    # Calculate the weights 
    weights_high = p - np.floor(p)
    weights_low = 1.0 - weights_high

    # Extract the low/high indexes and multiply by the corresponding weights
    x1 = np.take(a_sort, idx_low) * weights_low
    x2 = np.take(a_sort, idx_high) * weights_high

    # Return the average
    return np.add(x1, x2)

def pd_breakdown_fn(df, vl):
  '''
  Custom aggregation function to allow weighted mean, sum and quantiles
  If weight is not needed, calls standard pandas or numpy functions
  Text operation: use any text in the weight field as output
  '''
  r = []
  for a in vl:
    # early out of blank rows
    if len(a) == 0:
      continue
    name = a[0]
    mode = ""
    if len(a) > 1:
      mode = a[1]
    wt = []
    for w in a[2:]:
      if w is None or len(w) == 0:
        # trap blank values
        pass
      elif ',' in w:
        # handle the case where any weight is still comma separated
        wt.extend([_ for _ in w.split(',') if _ in df])
      elif w in df:
        wt.append(w)

    v = np.nan
    if mode == "text":
      # constant value, taken as raw text from the weight field
      if len(a) > 2:
        v = a[2]
      else:
        v = name
    elif name not in df:
      # trap special case: unknown var, will keep the default value of NaN
      pass
    elif mode == "list":
      # TODO: sort by weight when a weight was supplied
      v = ','.join(map(str, df[name].value_counts().index))
    elif mode == "rank":
      s = None
      if wt:
        s = np.prod(pd.pivot_table(df, wt, name), 0)
      else:
        s = df[name].value_counts()
      v = ','.join(map(lambda _: '%.2f' % _, s / s.sum()))
    elif wt and mode == "sum":
      # weighted sum
      # python 2.5 does not support to_numpy
      #v = np.nansum(np.prod([df[_].values.astype(np.float_) for _ in [name] + wt], 0))
      v = np.nansum(np.prod(df[[name] + wt].values.astype(np.float_), 1))
    elif wt and mode == "mean":
      # boolean indexing of non-nan values
      #bi = ~ np.isnan(df[name].values)
      bi = pd.Series.notnull(df[name])
      ws = np.array([df.loc[bi, _].values.astype(np.float_) for _ in wt])
      if len(wt) > 1:
        ws = np.prod(np.array(ws), 0)
      else:
        ws = ws.flat
      if np.nansum(ws) != 0:
        # weighted mean
        v = np.average(df.loc[bi, name].values.astype(np.float_), None, np.nan_to_num(ws))
    elif wt and mode in ["q1", "q2", "q3"]:
      q = (["q1", "q2", "q3"].index(mode) + 1) * 0.25
      v = weighted_quantiles(df[name].values, [q], np.prod([df[_].values for _ in wt], 0))[0]
    elif hasattr(pd.Series, mode):
      fn = eval('pd.Series.' + mode)
      v = fn(df[name])
      # FIX?: .astype(np.float_)
    elif mode == 'major':
      if df[name].any():
        v = df[name].value_counts().idxmax()
    elif mode == 'distinct':
      v = len(df[name].unique())
    elif mode in ["q1", "q2", "q3"]:
      q = (["q1", "q2", "q3"].index(mode) + 1) * 0.25
      v = df[name].quantile(q)
    elif mode.startswith('p') and str.isnumeric(mode[1:]):
      v = np.percentile(df[name], float(mode[1:]))

    r.append(v)
  return(r)

def main(*args):
  pd_save_dataframe(bm_breakdown(args[0], args[1], args[2], args[3]), args[4])

if __name__=="__main__" and sys.argv[0].endswith('bm_breakdown.py'):
  usage_gui(__doc__)
