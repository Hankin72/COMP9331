import matplotlib.pyplot as plt
import numpy as np


plt.axis([0, 18000, 0, 8])
plt.grid()
plt.scatter(754, 6.767, alpha=0.6, label = 'Brisbane')
plt.scatter(6243, 4.898, alpha=0.6, label= 'Serdang')
plt.scatter(16093, 5.107, alpha=0.6, label= 'Berlin')
plt.xlabel("Distance (km)")
plt.ylabel("Computed Ratio")
plt.annotate('6.767', xy=(854, 6.86))
plt.annotate('4.898', xy=(6343, 4.48))
plt.annotate('5.107', xy=(16193, 5.12))
plt.legend()
plt.show()