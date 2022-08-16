from datetime import datetime
import time


start = datetime.now().isoformat(sep = ' ', timespec='auto')

end = datetime.now()
end =str(end)

print(start)
print(end)


a = time.localtime(time.time())
a = time.asctime(a)
print()
print(a)

import calendar

cal = calendar.month(1994,8)
print(cal)


import numpy as np
abc = []

abc = np.array(abc)

print(abc.mean())
print(abc.max())
print(abc.min())