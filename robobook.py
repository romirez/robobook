#!/usr/bin/env python

import sys,os,random
import curses
import urllib2, urllib, commands, json
import shlex, subprocess
import threading

from rgbmatrix import RGBMatrix, RGBMatrixOptions
from time import sleep


LED_IMAGE_VIEWER_PATH = "/home/pi/led-image-viewer"

brightness = 75
process = None
lbt = None
binstr = ""
mode = "off"

def led_gif():
    global LED_IMAGE_VIEWER_PATH
    global process
    global brightness

    if (process != None):
        process.kill()
        process = None

    process = subprocess.Popen(shlex.split(LED_IMAGE_VIEWER_PATH
        + " --led-rows=64 --led-cols=64 --led-brightness=" + str(brightness)
        + " gifs/1.gif & > /dev/null"))

def switchMode(nmode):
    global mode
    global process
    global lbt

    if nmode == mode:
        return

    if mode == "binstr":
        lbt.matrix.Clear()

    if nmode == "binstr":
        if (process != None):
            process.kill()
            process = None
    elif nmode == "off":
        if (process != None):
            process.kill()
            process = None
    elif nmode == "gif":
        led_gif()

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

        self.matrix = RGBMatrix(options = options)

        global process

        ct = 0

        while True:
            if mode != "binstr":
                sleep(1)

            else:
                if (len(binstr) < len(self.lbinstr)):
                    self.particles = []
                    self.lbinstr = ""

                while (len(self.lbinstr) < len(binstr)):
                    self.particles.append({'x': random.randint(0,63), 'y': random.randint(53,63) if binstr[len(self.lbinstr)] == '0' else random.randint(0,10),
                        'dir': 0 if binstr[len(self.lbinstr)] == '0' else 1, 'life': 100000})
                    self.lbinstr += binstr[len(self.lbinstr)]

                    while (len(self.particles) > 300):
                        self.particles.pop(0)

                sleep(0.01)
                offset_canvas = self.matrix.CreateFrameCanvas()
                matrix = [[0 for x in range(64)] for y in range(64)]

                nparticles = []
                for p in self.particles:
                    r = random.randint(0,255)
                    g = random.randint(0,255)
                    b = random.randint(0,255)
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

                # i = 0
                #for c in binstr:
                #    if (c == '0'):
                    #     for i2 in range(0,64):
                    #         offset_canvas.SetPixel(i, i2, 0, 0, 0)
                    # if (c == '1'):
                    #     r = random.randint(0,255)
                    #     g = random.randint(0,255)
                    #     b = random.randint(0,255)
                    #     for i2 in range(0,64):
                    #         offset_canvas.SetPixel(i, i2, r, g, b)
                    #
                    # i += 2
                if mode == "binstr":
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

    lbt.matrix.Clear()

    # Loop where k is the last character pressed
    while (k != ord('q')):

        # Initialization
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        title = "ROBOBOOK 0.1"[:width-1]

        if k == ord('a'):
            led_gif()
        elif k == 259 or k == ord('0'):
            switchMode("binstr")

            # Pushed 0
            title = "0"
            binstr += "0"
        elif k == 350 or k == ord('1'):
            switchMode("binstr")

            # Pushed 1
            title = "1"
            binstr += "1"
        elif k == 258 or k == ord('2'):
            switchMode("off")
            binstr = ""

            # Pushed done
            title = "done"
        elif k != 0:
            title = "pushed: " + str(k)

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

def main():
    curses.wrapper(draw_menu)

if __name__ == "__main__":
    main()
