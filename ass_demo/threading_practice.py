import threading
import time
import queue

q = queue.Queue()
q.put(1)
q.put(2)
q.put(3)
q.put(4)
print(q)


def recv():
    # for i in range(10):
    try:
        seg = q.get(block=False)
    except queue.Empty:
        return (-1, None)
    return (0, seg)


for i in range(10):
    code, seg = recv()
    if code ==0:
        print(seg)
    else:
        print(None)


for i in range(10):
    try:
        e = q.get(block=False)
    except queue.Empty:
        break
    print(e)


exit_falg = False

ret = 0
lock = threading.Lock()


def workerA():
    global ret
    while not exit_falg:
        print('AAAAAA')
        time.sleep(0.5)
        lock.acquire()
        ret += 1
        lock.release()

#
# def workerB():
#     global ret
#     while not exit_falg:
#         print('BBBBBBBB')
#         time.sleep(0.6)
#         lock.acquire()
#         ret += 1
#         lock.release()
#
#
# def recv():
#     while True:
#         print("等待 recv。。")
#         time.sleep(0.5)
#     return None
#

def workerC():
    while True:
        seg = recv()

#
def workerC_fa():
    threading_C = threading.Thread(target=workerC)
    threading_C.setDaemon(True)

    threading_C.start()
    while not exit_falg:
        pass
        # time.sleep(1)
#
#
# if __name__ == "__main__":
#     threading_A = threading.Thread(target=workerA)
#     threading_B = threading.Thread(target=workerB)
#     threading_C_fa = threading.Thread(target=workerC_fa)
#
#     threading_A.start()
#     threading_B.start()
#     threading_C_fa.start()
#     time.sleep(2)
#     exit_falg = True
#
#     print(ret)
