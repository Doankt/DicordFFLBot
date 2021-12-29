import datetime

# Converts ms to mm:ss.ms
def ms_to_mmssms(ms):
    ms = int(ms)
    s = ms // 1000
    ms = ms % 1000
    m, s = divmod(s, 60)
    return "%02d:%02d.%03d" % (m, s, ms)