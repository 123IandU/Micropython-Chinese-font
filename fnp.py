import gc
from micropython import const

punct={
    
176:[0x00,0x18,0x24,0x24,0x18,0x00,0x00,0x00,0x00,0x00,0x00,0x00],#°

65292:[0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x60,0x60,0x20,0x40,0x00],#，

12290:[0x00,0x00,0x00,0x00,0x00,0x00,0x30,0x48,0x48,0x30,0x00,0x00],#。

65311:[0x30,0x48,0xCC,0xCC,0x18,0x30,0x30,0x30,0x00,0x30,0x30,0x00],#？

65281:[0x00,0x78,0x78,0x78,0x78,0x30,0x30,0x30,0x00,0x30,0x30,0x00],#！

12289:[0x00,0x00,0x00,0x00,0x00,0x00,0x40,0x20,0x30,0x10,0x00,0x00],#、

65307:[0x00,0x00,0x00,0x00,0x30,0x30,0x00,0x30,0x30,0x10,0x20,0x00],#；

65306:[0x00,0x00,0x00,0x00,0x30,0x30,0x00,0x00,0x30,0x30,0x00,0x00],#：

8220:[0x00,0x00,0x24,0x48,0x6C,0x6C,0x00,0x00,0x00,0x00,0x00,0x00],#“

8221:[0x00,0x00,0x6C,0x6C,0x24,0x48,0x00,0x00,0x00,0x00,0x00,0x00],#”

65288:[0x00,0x10,0x20,0x20,0x40,0x40,0x40,0x40,0x20,0x20,0x10,0x00],#（

65289:[0x00,0x20,0x10,0x10,0x08,0x08,0x08,0x08,0x10,0x10,0x20,0x00],#）

}

UNICODE_START = const(19968)#(U+4E00~U+9FA5)
UNICODE_END = const(40869)
FONT12_PATH = "font12_uni.bin"

_font12_file = None

# 模块初始化（仅一次）
def _init_font_files():
    global _font12_file
    try:
        _font12_file = open(FONT12_PATH, "rb")
        print("12号字体文件打开成功")
    except OSError:
        print(f"警告：未找到{FONT12_PATH}")
    gc.collect()

_init_font_files()

def read_glyph(unicode_code):
    if not (UNICODE_START <= unicode_code <= UNICODE_END) or _font12_file is None:
        return None
    offset = (unicode_code - UNICODE_START) * 24
    try:
        _font12_file.seek(offset)
        glyph_data = _font12_file.read(24)
        return glyph_data if len(glyph_data) == 24 else None
    except OSError:
        return None

# ---------------------- 私有接口 ----------------------

def _draw_char12(lcd, unicode_code, x, y):
    
    glyph_data = read_glyph(unicode_code)
    if glyph_data is None:
        return
    for row in range(12):
        byte1 = glyph_data[row]
        byte2 = glyph_data[row + 12]
        # 位运算直接操作，无临时变量
        for col in range(8):
            if ((byte1 >> (7 - col)) & 1) and 0 <= (x + col) <= 128 and 0 <= (y + row) <= 128: lcd.pixel(x + col, y + row, 1)
        for col in range(4):
            if ((byte2 >> (7 - col)) & 1) and 0 <= (x + col) <= 128 and 0 <= (y + row) <= 128: lcd.pixel(x + 8 + col, y + row, 1)
    glyph_data = None  # 强制释放
    gc.collect()  # 绘制完单个字符立即回收
    
def _draw_punc(lcd, unicode_code, x, y):
    
    glyph_data = punct[unicode_code]
    if glyph_data is None:
        return
    for row in range(12):
        byte1 = glyph_data[row]
        # 位运算直接操作，无临时变量
        for col in range(8):
            if ((byte1 >> (7 - col)) & 1) and 0 <= (x + col) <= 128 and 0 <= (y + row) <= 128: lcd.pixel(x + col, y + row, 1)
    glyph_data = None  # 强制释放
    gc.collect()  # 绘制完单个字符立即回收

# ---------------------- 公开接口 ----------------------    
def show_ch(lcd, ch_str, x, y):
    ch_list = [ord(char) for char in ch_str]
    current_x = x
    for code in ch_list:
        
        if code < 127:
            lcd.text(chr(code), current_x, y+4)
            current_x += 8
            
        elif not (UNICODE_START <= code <= UNICODE_END):
            _draw_punc(lcd, code, current_x, y)
            current_x += 6
            
        else:
            _draw_char12(lcd, code, current_x, y)
            current_x += 12
        if current_x + 12 > lcd.width:
            current_x = x
            y += 12
    ch_list = None  # 强制释放
    gc.collect()  # 绘制完单个字符立即回收

def close_font_files():
    global _font12_file
    if _font12_file:
        _font12_file.close()
        _font12_file = None
    gc.collect()
    
class MessageQueue:
    def __init__(self, max_size=10):
        self.queue = []  # 存储消息的列表
        self.max_size = max_size  # 最大队列长度（避免内存溢出）
    
    def enqueue(self, msg):
        """加入消息到队列，若满则移除最旧的消息"""
        if len(self.queue) >= self.max_size:
            self.queue.pop(0)  # 移除最旧的消息
        self.queue.append(msg)  # 加入新消息
    
    def dequeue(self):
        """从队列取出最旧的消息，若无则返回None"""
        if len(self.queue) > 0:
            return self.queue.pop(0)
        return None
    
    def is_empty(self):
        return len(self.queue) == 0