import uuid
import datetime


def guid():
    ret = '%s-%s' % (datetime.datetime.now().strftime('%Y%m%d%H%M%S%f'),
                     str(uuid.uuid1()).split('-')[0])
    return str(ret)
