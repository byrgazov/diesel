from diesel import Application, Loop, sleep
import time

def l(ident):
    for x in range(2):
        print('* [{}] hi.{}: {}'.format(time.strftime('%H:%M:%S'), ident, x))
        time.sleep(1)
        sleep(5)
    a.halt()

a = Application()
a.add_loop(Loop(l, 1))
a.add_loop(Loop(l, 2))
a.run()
