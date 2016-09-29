import matplotlib.pyplot as plt
import numpy as np
import sys

plt.rcParams.update({'legend.fontsize': 18,
                     'xtick.labelsize': 14,
                     'ytick.labelsize': 14,
                     'axes.labelsize': 16
                    })
if len(sys.argv) > 2:
    n = int(sys.argv[2])
else:
    n = 1
y = np.loadtxt(sys.argv[1])[::n]
x = np.arange(0, len(y))
s = np.cumsum(y)/np.arange(1,len(y)+1)
#plt.xlabel('time (T)')
plt.xlabel('iteration')
plt.ylabel('objective')
#plt.semilogy(x, y, label='instantaneous objective')
plt.plot(x, y, label='instantaneous objective')
plt.plot(x, s, label='cumulative averaged objective')
#plt.legend(loc='lower right')
plt.show()


