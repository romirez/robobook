#!/usr/bin/env python

import RPi.GPIO as GPIO
import sys,os,random,math
import curses
import urllib2, urllib, commands, json
import shlex, subprocess, pexpect
import threading, time
from PIL import Image
from colour import Color
import logging

from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics
from time import sleep


LED_IMAGE_VIEWER_PATH = "/home/pi/led-image-viewer --led-rows=64 --led-cols=64 --led-rgb-sequence=RBG"

brightness = 60
process = None
lbt = None
binstr = ""
mode = "off"

def switchMode(nmode):
    global mode
    global process
    global lbt
    global binstr
    global LED_IMAGE_VIEWER_PATH
    global brightness

    logging.debug("Switching mode from " + mode + " to " + nmode)

    if nmode == mode:
        return

    omode = mode
    mode = ""

    #cleanup

    if (process != None):
        process.sendcontrol("c")
        process = None
        sleep(0.1)

    #establish new mode

    if nmode == "greeting":
        process = pexpect.spawn(LED_IMAGE_VIEWER_PATH
            + " --led-brightness=" + str(brightness)
            + " /home/pi/robobook/bootup.gif /home/pi/robobook/greeting.gif")
    elif nmode == "binstr_fin":
        process = pexpect.spawn(LED_IMAGE_VIEWER_PATH
            + " --led-brightness=" + str(brightness)
            + " -l1 /home/pi/robobook/message.gif")
        logging.debug("started. processalive=" + str(process.isalive()))
    elif nmode == "binstr":
        process = pexpect.spawn("python /home/pi/robobook/robobook0.py")
        logging.debug("started binstr. processalive=" + str(process.isalive()))

    mode = nmode

class monitor(threading.Thread):
    def run(self):
        global process
        global mode

        timer = time.time()
        animationcycle = 0

        while True:
            swt = GPIO.input(25)
            logging.debug("swt=" + str(swt) + " mode=" + mode)

            if (swt == 1 and mode == "off"):
                #startup
                switchMode("greeting")
                sleep(0.1)
            elif (swt == 0 and mode == "offtr"):
                switchMode("off")
                sleep(0.1)
            elif (swt == 0 and mode != "off" and mode != "explore"):
                #shutdown
                switchMode("off")
                sleep(0.1)
            elif (mode == "off"):
                sleep(0.1)
            elif mode == "greeting" and process != None:
                #gif already loaded by switchMode so just wait
                logging.debug("processalive=" + str(process.isalive()))
                if process.isalive() == False:
                    switchMode("")
                sleep(0.1)
            elif mode == "binstr_fin" and process != None:
                #gif already loaded by switchMode so just wait
                logging.debug("processalive=" + str(process.isalive()))
                if process.isalive() == False:
                    logging.debug("binstr_fin animation done")
                    files = os.listdir('/home/pi/robobook/gifs/')
                    i = hash(binstr) % len(files)
                    mode = "animation"
                    process = pexpect.spawn(LED_IMAGE_VIEWER_PATH
                        + " --led-brightness=" + str(brightness)
                        + " /home/pi/robobook/gifs/" + files[i])
                    timer = time.time()
                sleep(0.1)
            elif mode == "animation":
                #gif already loaded by switchMode so just wait
                if (time.time() - timer > 8):
                    if (animationcycle == 2):
                        animationcycle = 0
                        switchMode("offtr")
                    else:
                        process.sendcontrol("c")
                        process = None
                        sleep(0.1)
                        files = os.listdir('/home/pi/robobook/gifs/')
                        i = hash(binstr + str(animationcycle)) % len(files)
                        mode = "animation"
                        process = pexpect.spawn(LED_IMAGE_VIEWER_PATH
                            + " --led-brightness=" + str(brightness)
                            + " /home/pi/robobook/gifs/" + files[i])
                        animationcycle += 1
                        timer = time.time()

                sleep(0.1)

def draw_menu(stdscr):
    global binstr
    global lbt
    global process

    k = 0

    # Clear and refresh the screen for a blank canvas
    stdscr.clear()
    stdscr.refresh()

    # Start colors in curses
    curses.start_color()
    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_WHITE)

    lbt = monitor()
    lbt.daemon = True
    lbt.start()

    dc = 0
    ei = 0

    # Loop where k is the last character pressed
    while (k != ord('q')):

        # Initialization
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        if k == 259 or k == ord('0'):
            dc = 0
            if (mode == "greeting" or mode == "binstr"):
                if (mode != "binstr"):
                    switchMode("binstr")
                    sleep(0.5)
                # Pushed 0
                title += "\nentered: 0"
                binstr += "0"
                process.sendline("0")
            elif (mode == "explore"):
                process.sendcontrol("c")
                ei -= 1
                files = os.listdir('/home/pi/robobook/gifs/')
                if (ei < 0): ei = len(files) - 1
                process = pexpect.spawn(LED_IMAGE_VIEWER_PATH
                    + " --led-brightness=" + str(brightness)
                    + " /home/pi/robobook/gifs/" + files[ei])
        elif k == 350 or k == ord('1'):
            dc = 0
            if (mode == "greeting" or mode == "binstr"):
                if (mode != "binstr"):
                    switchMode("binstr")
                    sleep(0.5)
                # Pushed 1
                title += "\nentered: 1"
                binstr += "1"
                process.sendline("1")
            elif (mode == "explore"):
                process.sendcontrol("c")
                ei += 1
                files = os.listdir('/home/pi/robobook/gifs/')
                if (ei > len(files) - 1): ei = 0
                process = pexpect.spawn(LED_IMAGE_VIEWER_PATH
                    + " --led-brightness=" + str(brightness)
                    + " /home/pi/robobook/gifs/" + files[ei])
        elif k == 258 or k == ord('2'):
            if (mode == "binstr"):
                switchMode("binstr_fin")
            elif (mode == "off"):
                logging.debug("dc=" + str(dc))
                dc += 1
                if dc >= 3:
                    switchMode("explore")
                    dc = 0
                    files = os.listdir('/home/pi/robobook/gifs/')
                    ei = int(len(files) * random.random())
                    process = pexpect.spawn(LED_IMAGE_VIEWER_PATH
                        + " --led-brightness=" + str(brightness)
                        + " /home/pi/robobook/gifs/" + files[ei])
            elif (mode == "explore"):
                process.sendcontrol("c")
                switchMode("off")
        elif k != 0:
            title += "pushed: " + str(k)

        title = "ROBOBOOK 0.1"
        title += ("\nmode: " + mode)

        # Centering calculations
        start_x_title = int((width // 2) - (len(title) // 2) - len(title) % 2)
        start_y = int((height // 2) - 2)

        # Turning on attributes for title
        stdscr.attron(curses.color_pair(2))
        stdscr.attron(curses.A_BOLD)

        # Rendering title
        stdscr.addstr(start_y, start_x_title, title)

        # Turning off attributes for title
        stdscr.attroff(curses.color_pair(2))
        stdscr.attroff(curses.A_BOLD)


        # Refresh the screen
        stdscr.refresh()

        # Wait for next input
        k = stdscr.getch()
    GPIO.cleanup()

def main():
    # init GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(19, GPIO.OUT)
    GPIO.output(19,GPIO.HIGH)
    GPIO.setup(25, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    logging.basicConfig(filename='example.log',level=logging.DEBUG)
    logging.debug('This message should go to the log file')
    logging.info('So should this')
    logging.warning('And this, too')

    curses.wrapper(draw_menu)

if __name__ == "__main__":
    main()
