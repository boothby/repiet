from PIL import Image
from collections import namedtuple
from operator import itemgetter

Color = namedtuple('color', ['color','abbv','hue','dark'])

class Parser:
    ##Stolen from http://www.dangermouse.net/esoteric/piet/Piet_py.txt
    #  Author- Ross Tucker
    #  Thanks to Marc Majcher for his project, Piet.pl
    #  Modified by Kelly Boothby to emit instructions instead of immediately executing them

    HEX_BLACK = '0x000000'
    HEX_WHITE = '0xffffff'

    do_arr = [["NOP", "PSH", "POP"],
              ["ADD", "SBT", "MLT"],
              ["DVD", "MOD", "NOT"],
              ["GRT", "PTR", "SWT"],
              ["DPL", "RLL", "DIN"],
              ["CIN", "DUT", "CUT"]]

    hex2tuple = {
        '0xffc0c0':Color('light red',    'lR',0, 0),                            
        '0xffffc0':Color('light yellow', 'lY',1, 0),                            
        '0xc0ffc0':Color('light green',  'lG',2, 0),                            
        '0xc0ffff':Color('light cyan',   'lC',3, 0),                            
        '0xc0c0ff':Color('light blue',   'lB',4, 0),                            
        '0xffc0ff':Color('light magenta','lM',5, 0),                            
        '0xff0000':Color('red',          ' R',0, 1),                            
        '0xffff00':Color('yellow',       ' Y',1, 1),                            
        '0x00ff00':Color('green',        ' G',2, 1),                            
        '0x00ffff':Color('cyan',         ' C',3, 1),                            
        '0x0000ff':Color('blue',         ' B',4, 1),                            
        '0xff00ff':Color('magenta',      ' M',5, 1),                            
        '0xc00000':Color('dark red',     'dR',0, 2),                            
        '0xc0c000':Color('dark yellow',  'dY',1, 2),                            
        '0x00c000':Color('dark green',   'dG',2, 2),                            
        '0x00c0c0':Color('dark cyan',    'dC',3, 2),                            
        '0x0000c0':Color('dark blue',    'dB',4, 2),                            
        '0xc000c0':Color('dark magenta', 'dM',5, 2),                            
        '0xffffff':Color('white',        'Wt',-1,-1),                            
        '0x000000':Color('black',        'Bk',-1,-1)
    }

    def __init__(self, filename):
        self.x, self.y = 0, 0
        self.dp = 0
        self.cc = -1
        self.debug = 0
        self.step_number = 1
        self.block = (0,0)
        self.filename = filename
        self._image = Image.open(self.filename).convert("RGB")
        self.cols, self.rows = self._image.size
        self.matrix = [[0 for x in range(self.cols)] \
                        for y in range(self.rows)]

        for j in range(self.rows):
            for i in range(self.cols):
                r,g,b = self._image.getpixel((i,j))
                rgb = "0x%02x%02x%02x" % (r,g,b)
                if rgb not in self.hex2tuple:
                    rgb = self.HEX_BLACK
                self.matrix[j][i] = rgb

    def _is_valid(self,x,y):        
        return 0 <= x < self.cols and 0 <= y < self.rows and \
               self.matrix[y][x] != self.HEX_BLACK
    
    def neighbors(self,x,y):
        for (dx,dy) in ((0,1),(0,-1),(1,0),(-1,0)):
            if self._is_valid(x+dx,y+dy) and \
                   (x+dx,y+dy) not in self.block and \
                   self.matrix[y][x] == self.matrix[y+dy][x+dx]:
                self.block.add((x+dx,y+dy))
                self.neighbors(x+dx,y+dy)

    def dmesg(self, mesg):
        if self.debug:
            print >>sys.stderr, mesg
            
    def get_edge(self):
        k_1 = int(not(self.dp % 2))
        r_1 = int(not(int(self.dp % 2) - int(self.cc < 0)))
        k_2 = int(self.dp % 2)
        r_2 = int(self.dp < 2)
        self.block = list(self.block)
        self.block.sort(key=itemgetter(k_1), reverse=r_1)
        self.block.sort(key=itemgetter(k_2), reverse=r_2)
        return self.block[0]
        
    def get_next_valid(self, x, y):
        if self.dp == 0:
            x += 1
        elif self.dp == 1:
            y += 1
        elif self.dp == 2:
            x -= 1
        elif self.dp == 3:
            y -= 1
        else:
            raise RuntimeError("bad direction pointer")
            sys.exit(1)
        return x,y

    def step(self):
        self.dmesg("\n-- STEP: %s" % self.step_number)
        self.block = set([(self.x, self.y)])
        self.neighbors(self.x, self.y) # modifies self.block
        self.block_value = len(self.block)
        i = 1
        seen_white = 0
        ex, ey = self.get_edge()
        while i <= 8:
            nx, ny = self.get_next_valid(ex, ey)
            if not self._is_valid(nx, ny):
                i += 1
                if i % 2:
                    self.dp = (self.dp + 1) % 4                
                else:
                    self.cc *= -1
                self.dmesg("Trying again at %s, %s. DP: %s CC: %s" % \
                           (nx, ny, self.dp, self.cc))
                if self.matrix[ey][ex] != self.HEX_WHITE:
                    self.block = set([(ex, ey)])
                    self.neighbors(ex, ey) # modifies self.block
                    self.block_value = len(self.block)
                    ex, ey = self.get_edge()
            elif self.matrix[ny][nx] == self.HEX_WHITE:
                if not seen_white:
                    seen_white = 1
                    i = 0
                    self.dmesg("Entering white; sliding thru")
                ex, ey = nx, ny
            else: # next color is a color
                self.dmesg("%s @ (%s,%s) -> %s @ (%s,%s) DP:%s CC:%s" % \
                           (self.hex2tuple[self.matrix[self.y][self.x]].color, \
                            self.x, self.y, \
                            self.hex2tuple[self.matrix[ny][nx]].color, \
                            nx, ny,\
                            self.dp, self.cc))
                if not seen_white:
                    dH = self.hex2tuple[self.matrix[ny][nx]].hue - \
                         self.hex2tuple[self.matrix[self.y][self.x]].hue
                    dD = self.hex2tuple[self.matrix[ny][nx]].dark - \
                         self.hex2tuple[self.matrix[self.y][self.x]].dark
                    retval = self.do_arr[dH][dD]
                    self.dmesg("OPER: %s" % (self.do_arr[dH][dD]))
                else:
                    retval = "NOP"


#                self.dmesg("STACK: %s" % self.stack)
                self.x, self.y = nx, ny
                self.step_number += 1
                return retval
        else:
            self.dmesg("Execution trapped, program terminates")
            return None
