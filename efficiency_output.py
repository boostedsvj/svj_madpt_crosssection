import os, os.path as osp, glob, re

import matplotlib.pyplot as plt
import numpy as np


#log_file ='/data/users/snabili/svj_qcd/xsec_mgraph/svj_madpt_crosssection/output.txt'
log_file = 'output.txt'
textfile = open(log_file, 'r')
filetext = textfile.read()
textfile.close()

madpt0_text   = 'Successfully opened file file:/mnt/hadoop/cms/store/user/snabili/SIG/xsec_from_lxplus/madpt0/miniaod/madpt0_mz'
madpt300_text = 'Successfully opened file file:/mnt/hadoop/cms/store/user/snabili/SIG/xsec_from_lxplus/madpt300/miniaod/madpt300_mz'

mz_madpt300 = re.findall(r'Successfully opened file file:/mnt/hadoop/cms/store/user/snabili/SIG/xsec_from_lxplus/madpt300/miniaod/madpt300_mz(\d+)', filetext)
mz_madpt0 = re.findall(r'Successfully opened file file:/mnt/hadoop/cms/store/user/snabili/SIG/xsec_from_lxplus/madpt0/miniaod/madpt0_mz(\d+)', filetext)
madpt=re.findall(r'Successfully opened file file:/mnt/hadoop/cms/store/user/snabili/SIG/xsec_from_lxplus/madpt0/miniaod/madpt0(\d+)', filetext)

length_file = len(mz_madpt0) + len(mz_madpt300)
matches=re.findall(r'After matching: total cross section = ([\d\.e\+\-]+) \+\- ([\d\.e\+\-]+) pb', filetext)
xs = np.array([float(matches[i][0]) for  i in range(length_file)])
xs_err = np.array([float(matches[i][1]) for  i in range(length_file)])

print('Dumping fit result to fit.txt')
with open('xsec.txt', 'w') as f:
        f.write(repr(list(xs)))

print('*'*50)
print('madpt0:')
print([['   mz = ', mz_madpt0[i], ' xs = ', xs[i]*.25**2] for i in range(8)])
print('madpt300:')
print([['   mz = ', mz_madpt300[i], ' xs = ', xs[i+8]*.25**2] for i in range(8)])
print('*'*50)
print(xs[:8])
print(xs[8:])
#set_matplotlib_fontsizes()
fig, (ax0, ax1) = plt.subplots(2, 1, gridspec_kw={'height_ratios': [1, 0.35]}, sharex=True, figsize=(8,12))
fig.subplots_adjust(hspace=0)
ax0.errorbar(mz_madpt0, xs[:8]*0.25**2, fmt='.', yerr=xs_err[:8]*0.25, label='madpt>0')
ax0.errorbar(mz_madpt300, xs[8:]*0.25**2, fmt='.', yerr=xs_err[8:]*0.25, label='madpt>300')
ax0.set_ylabel(r'$\sigma$ after matching (pb)')
ax0.legend()
ax0.set_yscale('log')
ax1.plot(mz_madpt300, xs[8:]/xs[:8], 'o')
ax1.set_xlabel(r'$m_{Z\prime}$ (GeV)')
ax1.set_ylabel(r'$\frac{\sigma_{no madpt}}{\sigma_{madpt>300}}$', fontsize=17)
fig.savefig('png/effect_madptcut.png')
plt.close()
plt.plot(mz_madpt300, xs[8:]*0.25**2, 'o', label='madpt>300')
plt.ylabel(r'$\sigma$ after matching (pb)')
plt.xlabel(r'$m_{Z\prime}$ (GeV)')
plt.legend()
plt.savefig('png/madpt300.png')
plt.close()
xs_old = np.array([5894.0, 2958.0, 1671.0, 966.8, 578.3, 383.6, 268.0, 193.6])
plt.plot(mz_madpt0, xs[:8]*0.25**2, 'o', label='new raw samples with $g_{q}$=0.25')
plt.plot(mz_madpt0, xs_old, 'o', label='old raw samples ($g_q=?$)')
plt.ylabel(r'$\sigma$ after matching (pb)')
plt.xlabel(r'$m_{Z\prime}$ (GeV)')
plt.legend()
#plt.show()
plt.savefig('png/rawxsec.png')
