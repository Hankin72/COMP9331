import collections


q = collections.deque()

q.append(1)
q.append(2)
q.append(3)

print(q)

q.appendleft(1)
q.appendleft(2)
q.appendleft(3)
print(q)

print(q.popleft())
print(q.pop())
print(q)

MMS =400

buffer_unacked = collections.deque(maxlen= int(MMS/2))

print(buffer_unacked)
buffer_unsent = collections.deque()

# segment = send_buffer.get()
#
# if size1+size2 < MWS:
#     buffer_unsent.append()
#
#     seq2 =buffer_unsent.pop()
#     send()
#
#     buffer_unacked.append(seq2)
#
#
#


