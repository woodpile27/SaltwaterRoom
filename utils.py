import threading


def thread_start(target, *args):
    t = threading.Thread(target=target, args=(args))
    t.setDaemon(True)
    t.start()


def timer(fun):
    t = threading.Timer(60, timer, args=[fun])
    fun()
    t.start()


def queue_get_all(q):
    items = []
    while True:
        try:
            items.append(q.get_nowait())
        except Exception, e:
            break
    return items

