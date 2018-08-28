#!/usr/bin/env python

import RPi.GPIO as GPIO
import sys,os,random,math
import curses
import urllib2, urllib, commands, json
import shlex, subprocess, pexpect
import threading
from PIL import Image
from colour import Color
import logging

from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics
from time import sleep


LED_IMAGE_VIEWER_PATH = "/home/pi/led-image-viewer"

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

    #cleanup

    if mode == "binstr":
        binstr = ""
        lbt.matrix.Clear()
        #del lbt.matrix
        sleep(0.1)
    elif mode == "gif" or mode == "greeting":
        if (process != None):
            process.sendcontrol("c")
            process = None
            sleep(0.1)

    #establish new mode

    if nmode == "greeting":
        process = pexpect.spawn(LED_IMAGE_VIEWER_PATH
            + " --led-rows=64 --led-cols=64 --led-brightness=" + str(brightness)
            + " /home/pi/robobook/bootup.gif greeting.gif")
    elif nmode == "binstr_fin":
        process = pexpect.spawn(LED_IMAGE_VIEWER_PATH
            + " --led-rows=64 --led-cols=64 --led-brightness=" + str(brightness)
            + " /home/pi/robobook/message.gif")

    mode = nmode

class LEDBin(threading.Thread):
    matrix = None
    particles = []
    lbinstr = ""

    def run(self):
        options = RGBMatrixOptions()
        options.rows = 64
        options.cols = 64
        options.brightness = brightness

        global process
        global mode
        global binstr

        partmode = 1
        refreshrate = 0.02
        cycletime = 0

        while True:
            swt = GPIO.input(25)
            logging.debug("swt=" + str(swt) + " mode=" + mode)

            if (swt == 1 and mode == "off"):
                #startup
                switchMode("greeting")
                sleep(1)
            elif (swt == 0 and mode != "off"):
                #shutdown
                switchMode("off")
                sleep(1)
            elif (mode == "off"):
                sleep(1)
            elif mode == "greeting":
                #gif already loaded by switchMode so just wait
                logging.debug("processalive=" + str(process.isalive()))
                if process.isalive() == False:
                    switchMode("")
                sleep(1)
            elif mode == "binstr":
                if (self.matrix == None):
                    self.matrix = RGBMatrix(options = options)
                    logging.debug("new matrix")

                if (len(binstr) < len(self.lbinstr)):
                    self.particles = []
                    self.lbinstr = ""

                # add new particles
                while (len(self.lbinstr) < len(binstr)):
                    r = random.randint(10,30)
                    pos = random.random()
                    self.particles.append({'r': r, 'pos': pos,'x': random.randint(0,63), 'y': random.randint(53,63) if binstr[len(self.lbinstr)] == '0' else random.randint(0,10),
                        'dir': 0 if binstr[len(self.lbinstr)] == '0' else 1, 'life': 100000, 'speed': random.uniform(0.01, 0.02)})
                    self.lbinstr += binstr[len(self.lbinstr)]

                    while (len(self.particles) > 300):
                        self.particles.pop(0)

                sleep(refreshrate)
                offset_canvas = self.matrix.CreateFrameCanvas()
                matrix = [[0 for x in range(64)] for y in range(64)]

                nparticles = []

                for p in self.particles:
                    if (len(binstr) < 20):
                        r = random.randint(0,255*brightness/100)
                        g = random.randint(0,255*brightness/100)
                        b = random.randint(0,255*brightness/100)

                        circ = math.floor(math.pi * 2 * p['r'])
                        angle = 2*math.pi*p['pos']

                        p['x'] = int(math.floor(32 + math.cos(angle)*p['r']))
                        p['y'] = int(math.floor(32 + math.sin(angle)*p['r']))

                        offset_canvas.SetPixel(p['x'], p['y'], r, g, b)

                        if p['dir'] == 1:
                            p['pos'] += p['speed']
                            if (p['pos']) > 1: p['pos'] -= 1
                        elif p['dir'] == 0:
                            p['pos'] -= p['speed']
                            if (p['pos']) < 0: p['pos'] += 1

                        if p['life'] > 0:
                            nparticles.append(p)

                        p['life'] -= 1
                    elif (len(binstr) < 40):
                        r = random.randint(0,255*brightness/100)
                        g = random.randint(0,255*brightness/100)
                        b = random.randint(0,255*brightness/100)
                        offset_canvas.SetPixel(p['x'], p['y'], r, g, b)
                        matrix[p['x']][p['y']] = 1

                        if p['dir'] == 1 and p['y'] < 63 and matrix[p['x']][p['y'] + 1] == 0:
                            p['y'] += 1
                        elif p['dir'] == 0 and p['y'] > 0 and matrix[p['x']][p['y'] - 1] == 0:
                            p['y'] -= 1
                        elif p['dir'] == 1 and (p['y'] == 63 or matrix[p['x']][p['y'] + 1] != 0):
                            p['dir'] = 0
                        elif p['dir'] == 0 and (p['y'] == 0 or matrix[p['x']][p['y'] - 1] != 0):
                            p['dir'] = 1

                        if p['life'] > 0:
                            nparticles.append(p)

                        p['life'] -= 11
                    else:
                        r = random.randint(0,255*brightness/100)
                        g = random.randint(0,255*brightness/100)
                        b = random.randint(0,255*brightness/100)
                        offset_canvas.SetPixel(p['x'], p['y'], r, g, b)
                        matrix[p['x']][p['y']] = 1

                        if p['dir'] == 1 and p['y'] < 63 and matrix[p['x']][p['y'] + 1] == 0:
                            p['y'] += 1
                        elif p['dir'] == 0 and p['y'] > 0 and matrix[p['x']][p['y'] - 1] == 0:
                            p['y'] -= 1

                        if p['life'] > 0:
                            nparticles.append(p)

                        p['life'] -= 1

                self.particles = nparticles

                offset_canvas = self.matrix.SwapOnVSync(offset_canvas)



def draw_menu(stdscr):
    global binstr
    global lbt

    k = 0

    # Clear and refresh the screen for a blank canvas
    stdscr.clear()
    stdscr.refresh()

    # Start colors in curses
    curses.start_color()
    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_WHITE)

    lbt = LEDBin()
    lbt.daemon = True
    lbt.start()

    # Loop where k is the last character pressed
    while (k != ord('q')):

        # Initialization
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        if k == ord('a'):
            switchMode("gif")
        elif k == 259 or k == ord('0'):
            switchMode("binstr")

            #title += ("\nbinstr: " + binstr)

            # Pushed 0
            title += "\nentered: 0"
            binstr += "0"
        elif k == 350 or k == ord('1'):
            switchMode("binstr")

            #title += ("\nbinstr: " + binstr)

            # Pushed 1
            title += "\nentered: 1"
            binstr += "1"
        elif k == 258 or k == ord('2'):
            switchMode("binstr_fin")
        elif k == ord('3'):
            switchMode("text")
        elif k == ord('4'):
            switchMode("robot")
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
