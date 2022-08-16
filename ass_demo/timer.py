import threading

import time

#
# def A():
#     print('a')
#
#
# print('NNNN')
# timer = threading.Timer(3, A)
#
# timer.start()
# time.sleep(1)
# timer.cancel()
# print('c')


class Timer:
    def __init__(self, t, func):
        self.func = func
        self.time = t
        self.state = 'init'
        # 单位时 seconds,浮点数，
        self.init()

    def timer_threading(self):
        while True:
            if self.state == 'running':
                self.current_time = time.time()
                self.interval += self.current_time - self.last_time

                if self.interval >= self.time:
                    self.func()
                    self.state = 'stop'
                    return
                self.last_time = self.current_time
            elif self.state == 'pause':
                self.current_time = time.time()
                self.last_time = self.current_time
            elif self.state == 'stop':
                return

    def init(self):
        self.current_time = time.time()
        self.last_time = self.current_time
        self.interval = 0

    def start(self):
        self.state = 'running'
        threading.Thread(target=self.timer_threading).start()

    def pause(self):
        self.state = 'pause'

    def resume(self):
        self.state = 'running'

    def stop(self):
        self.state = 'stop'

    def reset(self, t=None):
        if t != None:
            self.time = t
        self.state = 'init'


def A():
    print("A")

print('B')
print('sssss')
timer = Timer(3,A)
timer.start()
timer.pause()
time.sleep(5)
timer.resume()

# timer.reset()
