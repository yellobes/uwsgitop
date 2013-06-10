#!python

import socket
try:
    import simplejson as json
except ImportError:
    import json
import curses
import time
import atexit
import sys
import traceback

need_reset = True
screen = None

def human_size(n):
    # G
    if n >= (1024*1024*1024): 
        return "%.1fG" % (n/(1024*1024*1024))
    # M
    if n >= (1024*1024):
        return "%.1fM" % (n/(1024*1024))
    # K
    if n >= 1024:
        return "%.1fK" % (n/1024)
    return "%d" % n

def game_over():
    global need_reset
    if need_reset:
        curses.endwin()

def exc_hook(type, value, tb):
    global need_reset, screen
    need_reset = False
    if screen:
        curses.endwin()
    traceback.print_exception(type, value, tb)

sys.excepthook = exc_hook

argc = len(sys.argv)

if argc < 2:
    raise Exception("You have to specify the uWSGI stats socket")

addr = sys.argv[1]
sfamily = socket.AF_UNIX
addr_tuple = addr
if ':' in addr:
    sfamily = socket.AF_INET
    addr_parts = addr.split(':')
    addr_tuple = (addr_parts[0], int(addr_parts[1]))

freq = 3
try:
    freq = int(sys.argv[2])
except:
    pass

screen = curses.initscr()
curses.start_color()

# busy
curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
# cheap
curses.init_pair(2, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
# pause
curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)
# sig
curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)


screen.timeout(freq*1000)
atexit.register(game_over)

try:
    curses.curs_set(0)
except:
    pass
screen.clear()

def reqcount(a, b):
    if a['requests'] > b['requests']:
        return -1
    if a['requests'] < b['requests']:
        return 1
    return 0

def calc_percent(tot, req):
    if tot == 0:
        return 0.0
    return (100 *float(req))/float(tot)

while True:

    screen.clear()

    js = ''

    try:
        s = socket.socket(sfamily, socket.SOCK_STREAM)
        s.connect( addr_tuple )

        while True:
            data = s.recv(4096)
            if len(data) < 1:
                break
            js += data
    except:
        raise Exception("unable to get uWSGI statistics")

    dd = json.loads(js)


    
    uversion = ''
    if 'version' in dd:
        uversion = '-' + dd['version']

    if not 'listen_queue' in dd:
        dd['listen_queue'] = 0 

    cwd = ""
    if 'cwd' in dd:
        cwd = "- cwd: %s" % dd['cwd'] 

    uid = ""
    if 'uid' in dd:
        uid = "- uid: %d" % dd['uid'] 

    gid = ""
    if 'gid' in dd:
        gid = "- gid: %d" % dd['gid'] 

    masterpid = ""
    if 'pid' in dd:
        masterpid = "- masterpid: %d" % dd['pid'] 

    screen.addstr(1, 0, "node: %s %s %s %s %s" % (socket.gethostname(), cwd, uid, gid, masterpid))

    if 'vassals' in dd:
        screen.addstr(0, 0, "uwsgi%s - %s - emperor: %s - tyrant: %d" % (uversion, time.ctime(), dd['emperor'], dd['emperor_tyrant']))
        vassal_spaces = max([len(v['id']) for v in dd['vassals']])
        screen.addstr(2, 0, " VASSAL%s\tPID\t" % (' ' * (vassal_spaces-6)), curses.A_REVERSE)
        pos = 3
        for vassal in dd['vassals']:
            screen.addstr(pos, 0, " %s\t%d" % (vassal['id'].ljust(vassal_spaces), vassal['pid']))
            pos += 1
    
    elif 'workers' in dd:
        tot = sum( [worker['requests'] for worker in dd['workers']] )
        tx = human_size(sum( [worker['tx'] for worker in dd['workers']] ))
        screen.addstr(0, 0, "uwsgi%s - %s - req: %d - lq: %d - tx: %s" % (uversion, time.ctime(), tot, dd['listen_queue'], tx))
        screen.addstr(2, 0, " WID\t%\tPID\tREQ\tEXC\tSIG\tSTATUS\tAVG\tRSS\tVSZ\tTX\tRunT\t", curses.A_REVERSE)
        pos = 3

        dd['workers'].sort(reqcount)
        for worker in dd['workers']:
            sigs = 0
            wtx = human_size(worker['tx'])

            wrunt = worker['running_time']/1000
            if wrunt > 9999999:
                wrunt = "%sm" % str(wrunt / (1000*60))
            else:
                wrunt = str(wrunt)
                
            color = curses.color_pair(0)
            if 'signals' in worker:
                sigs = worker['signals']
            if worker['status'] == 'busy':
                color = curses.color_pair(1)
            if worker['status'] == 'cheap':
                color = curses.color_pair(2)
            if worker['status'] == 'pause':
                color = curses.color_pair(3)
            if worker['status'].startswith('sig'):
                color = curses.color_pair(4)
            try:
                screen.addstr(pos, 0, " %d\t%.1f\t%d\t%d\t%d\t%d\t%s\t%dms\t%s\t%s\t%s\t%s" % (
                    worker['id'], calc_percent(tot, worker['requests']), worker['pid'], worker['requests'], worker['exceptions'], sigs, worker['status'],
                    worker['avg_rt']/1000, human_size(worker['rss']), human_size(worker['vsz']),
                    wtx, wrunt
                ), color)
            except:
                pass
            pos += 1

    screen.refresh()

    s.close()
    if screen.getch() == ord('q'):
        game_over()
        break


