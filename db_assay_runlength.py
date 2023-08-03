#!python
# limit assay intervals by a maximum length. usefull for desurvey/compositing.
# v1.0 2022/10 paulo.ernesto
'''
usage: $0 assay*csv,xlsx from:assay to:assay length:assay runlength=1,5,10,15 output*csv,xlsx
'''

import sys, os.path
import numpy as np
import pandas as pd

# import modules from a pyz (zip) file with same name as scripts
sys.path.insert(0, os.path.splitext(sys.argv[0])[0] + '.pyz')

from _gui import usage_gui, pd_load_dataframe, pd_save_dataframe, log, pd_synonyms

def db_assay_runlength(assay, vfrom, vto, vlength, runlength, output):
  idf = pd_load_dataframe(assay, keep_null=True)
  if runlength:
    runlength = float(runlength)
  else:
    runlength = 1

  if not vfrom:
    vfrom = pd_synonyms(idf, 'from')
  if not vto:
    vto = pd_synonyms(idf, 'to')
  if not vlength:
    vlength = pd_synonyms(idf, 'length')


  odf = pd.DataFrame(columns=idf.columns)
  for ri,rd in idf.iterrows():
    t0 = rd[vfrom]
    t1 = rd[vto]
    while (t1 - t0) > runlength:
      rd[vfrom] = t0
      rd[vto] = t0 + runlength
      if vlength:
        rd[vlength] = runlength
      t0 += runlength
      #odf = odf.append(rd, ignore_index=True)
      odf = pd.concat((odf, rd.to_frame().T), ignore_index=True, copy=False)

    rd[vfrom] = t0
    rd[vto] = t1
    if vlength:
      rd[vlength] = t1 - t0
    #odf = odf.append(rd, ignore_index=True)
    odf = pd.concat((odf, rd.to_frame().T), ignore_index=True, copy=False)

  if output:
    pd_save_dataframe(odf, output)
  else:
    print(odf.to_string())


main = db_assay_runlength

if __name__=="__main__":
  usage_gui(__doc__)
