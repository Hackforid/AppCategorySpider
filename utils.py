# -*- coding:utf-8 -*-

def retry(fn, time=10):
    def _(*args, **kwargs):
        for i in range(time):
            try:
                return fn(*args, **kwargs)
            except:
                if i == time - 1:
                    print 'fail'
                pass
    return _
