# <msg_type>	<time>	<packet_type>	<seq>	<size>	<ack>
#
import collections
import queue

import random
import time

#

window = {121: {'data': b'2222', 'Time': None},
          1213213123123123: {'data': b'2222', 'Time': None},

          111111: {'data': b'2222', 'time': None}}

for see_number in sorted(list(window.keys())):
    print(see_number)

print(window.get(121))

for key,values in window.items():

    if key+len(values['data']) >10:
        print(True)
    print(values.get('data'))