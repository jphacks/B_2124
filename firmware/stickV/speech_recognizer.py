import audio
from board import board_info
from fpioa_manager import *
import image
import lcd
from machine import I2C,UART
import Maix
from Maix import GPIO, I2S
import os
from speech_recognizer import isolated_word
import time


# BOARD_NAME == M5STICKV or M1DOCK or MAIXDUINO
BOARD_NAME = "M5STICKV"

if (BOARD_NAME == "M5STICKV"):
    from pmu import axp192
    pmu = axp192()
    pmu.enablePMICSleepMode(True)


#####################################################################
# Initial values
#####################################################################
sample_rate   = 16000

# 登録する単語の指定，増減できるが上限は未確認．フラッシュの保存領域に依存する
#words = ["Hey Maxduino", "OK Google", "OK Near", "torantotte"]
words = ["torantotte"]

# DTW: 動的時間伸縮法のパラメータ
# If the word recognition rate is low, look at the values of
# dtw_value and current_frame_len in the terminal and adjust them.
dtw_threshold = 400
frame_len_threshold = 30  # trantotteを入れる場合は短め(30)に，default: 70

if (BOARD_NAME == "M5STICKV"):
    # GPIO Settings for M5StickV.
    lcd.init(type=3)
    fm.register(board_info.MIC_DAT,fm.fpioa.I2S0_IN_D0, force=True)
    fm.register(board_info.MIC_LRCLK,fm.fpioa.I2S0_WS, force=True)
    fm.register(board_info.MIC_CLK,fm.fpioa.I2S0_SCLK, force=True)
    fm.register(34, fm.fpioa.UART2_TX, force=True)
    fm.register(35, fm.fpioa.UART2_RX, force=True)
    fm.register(board_info.BUTTON_A, fm.fpioa.GPIO1, force=True)
    button_a_label = "BtnA"
    # Speaker I2s Initialize
    fm.register(board_info.SPK_SD, fm.fpioa.GPIO0)
    spk_sd=GPIO(GPIO.GPIO0, GPIO.OUT)
    spk_sd.value(1)
    fm.register(board_info.SPK_DIN,fm.fpioa.I2S1_OUT_D1)
    fm.register(board_info.SPK_BCLK,fm.fpioa.I2S1_SCLK)
    fm.register(board_info.SPK_LRCLK,fm.fpioa.I2S1_WS)
    wav_dev = I2S(I2S.DEVICE_1)
    music_sample_rate = 96000
elif ((BOARD_NAME == "MAIXDUINO") or (BOARD_NAME == "M1DOCK")):
    # GPIO Settings for Maixduino or M1Dock.
    lcd.init()
    fm.register(board_info.MIC0_DATA, fm.fpioa.I2S0_IN_D0, force=True)
    fm.register(board_info.MIC0_WS, fm.fpioa.I2S0_WS, force=True)
    fm.register(board_info.MIC0_BCK, fm.fpioa.I2S0_SCLK, force=True)
    fm.register(21, fm.fpioa.UART2_TX, force=True)  # Maixduino PIN2
    fm.register(22, fm.fpioa.UART2_RX, force=True)  # Maixduino PIN3
    fm.register(board_info.BOOT_KEY, fm.fpioa.GPIO1, force=True)
    button_a_label = "BtnBoot"

uart_port = UART(UART.UART2, 115200, 8, None, 1, timeout=1000, read_buf_len=4096)
button_a = GPIO(GPIO.GPIO1, GPIO.IN, GPIO.PULL_UP)

# data storage "/sd/" or "/flash/"
storage = "/flash/"


#####################################################################
# Functions
#####################################################################
def print_lcd(str1=None, str2=None, str3=None, serial_out=True, bgcolor=(0, 0, 0)):
    if (str1 != None):
        img.draw_rectangle((0, 0, lcd_w, 45), fill=True, color=bgcolor)
        img.draw_string(10, 10, str1, color=(255, 0, 0), scale=2, mono_space=0)
        if (serial_out):
            print(str1)
    if (str2 != None):
        img.draw_rectangle((10, 45, lcd_w, 40), fill=True, color=bgcolor)
        img.draw_string(10, 45, str2, color=(0, 0, 255), scale=2, mono_space=0)
        if (serial_out):
            print(str2)
    if (str3 != None):
        img.draw_rectangle((10, 90, lcd_w, 40), fill=True, color=bgcolor)
        img.draw_string(10, 90, str3, color=(0, 0, 255), scale=2, mono_space=0)
        if (serial_out):
            print(str3)
    lcd.display(img)


def save_file(number, data):
    print_lcd("Data Saving...")
    lcd.display(img)
    filename0 = storage + "rec0_" + str(number) + ".sr"
    filename1 = storage + "rec1_" + str(number) + ".sr"
    t0 = data[0]
    t1 = data[1]
    print(type(t0))
    print(type(t1))
    with open(filename0, 'w') as f:
        f.write(str(t0))
    with open(filename1, 'wb') as f:
        f.write(bytearray(t1))


def load_data(number):
    print_lcd("Data Loading...")
    for i in range(number):
        print("load_data:" + str(i))
        filename0 = storage + "rec0_" + str(i) + ".sr"
        filename1 = storage + "rec1_" + str(i) + ".sr"
        with open(filename0, 'r') as f:
            data0 = f.read()
        with open(filename1, 'rb') as f:
            data1 = f.read()
        print(data0)
        print(data1)
        tupledata = [int(data0), data1]
        sr.set(i*2, tupledata)
        print(b'0x0d0x0a')


def record_voice():
    for i in range(len(words)):
        while True:
            time.sleep_ms(100)
            print(sr.state())
            if sr.Done == sr.record(i*2):
                print_lcd("get !")
                data = sr.get(i*2)
                save_file(i, data)
                print(data)
                break
            for sec in range(3, 0, -1):
                print_lcd("wait {} sec".format(sec))
                time.sleep(1)
            if sr.Speak == sr.state():
                for sec in range(2, 0, -1):
                    print_lcd("Please speak {}".format(words[i]), "remain {} sec".format(sec))
                    time.sleep(1)

        sr.set(i*2, data)
        time.sleep_ms(500)

def play_wav(fname):
    player = audio.Audio(path=fname)
    player.volume(100)
    wav_info = player.play_process(wav_dev)
    wav_dev.channel_config(wav_dev.CHANNEL_1,
        I2S.TRANSMITTER,resolution = I2S.RESOLUTION_16_BIT,
        align_mode = I2S.STANDARD_MODE)
    wav_dev.set_sample_rate(music_sample_rate)
    while True:
        ret = player.play()
        if ret == None:
            break
        elif ret==0:
            break
    player.finish()
    print("finish")


##############################################################################
# Main
##############################################################################
lcd.rotation(0)

if (BOARD_NAME == "M5STICKV"):
    # set lcd backlight for M5StickV
    i2c = I2C(I2C.I2C0, freq=400000, scl=28, sda=29)
    i2c.writeto_mem(0x34, 0x91, b'\xa0')
elif ((BOARD_NAME == "MAIXDUINO") or (BOARD_NAME == "M1DOCK")):
    lcd.set_backlight(50)

lcd_w = lcd.width()
lcd_h = lcd.height()
img = image.Image(size=(lcd_w, lcd_h))
print_lcd("MaixPy", "Isolated words Recognizer")
rx = I2S(I2S.DEVICE_0)
rx.channel_config(rx.CHANNEL_0, rx.RECEIVER, align_mode=I2S.STANDARD_MODE)
rx.set_sample_rate(sample_rate)
print(rx)

# model
sr = isolated_word(dmac=2, i2s=I2S.DEVICE_0, size=50)
print(sr.size())
print(sr)

## threshold
sr.set_threshold(0, 0, 10000)


# data set
try:
    load_data(len(words))
except Exception as e:
    record_voice()

while True:
    time.sleep_ms(200)
    # シリアル通信で"E"を受け取ったら音声認識モードに
    if uart_port.any():
        read_data = uart_port.read(1)  # 1文字読み取り
        if read_data == b'E':
            print("recv = ", read_data)

            # recognition
            print_lcd("Recognition begin")
            time.sleep_ms(1000)
            while True:
                print_lcd("Please speak word!", button_a_label + ":Record Voice", serial_out=False)
                if (button_a.value() == 0):
                    record_voice()
                if sr.Done == sr.recognize():
                    res = sr.result()
                    print("(Number,dtw_value,currnt_frame_len,matched_frame_len)=" + str(res))
                    print_lcd(str3=str(res))
                    if (res != None) and (res[1] < dtw_threshold) and (res[2] > frame_len_threshold):
                        print(str(res[0]))
                        for i in range(len(words)):
                            if res[0] == (i * 2):
                                print_lcd("Recognize",str3="Word: " + words[i], bgcolor=(0, 255, 255))
                                uart_port.write(words[i] + "\n")
                                time.sleep_ms(200)
                # シリアル通信で"D"を受け取ったら終了，Mなら音声再生
                if uart_port.any():
                    read_data = uart_port.read(1)  # 1文字読み取り
                    if read_data == b'D':
                        print("Disabled mode")
                        uart_port.write(b"W")
                        break
                    elif read_data == b'M':
                        print("Music mode")
                        uart_port.write(b"M")
                        # TODO: 音声再生処理
                        play_wav("08_motteke.wav")
