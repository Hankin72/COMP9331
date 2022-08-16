import json

segment = {'port':123, 'port':123, "se1":121, 'ack':1221}

# json_str = json.dumps(segment)
# print(json_str.encode())
#
# bytes = json_str.encode()
#
#
#
# d = json.loads(bytes.decode())
#
# print(d)
import pickle

bytes = pickle.dumps(segment)
print(bytes)

print(pickle.loads(bytes))


class A:
    def __int__(self):
        self.data = '12112'


a =A()
by = pickle.dumps(a)
print(by)