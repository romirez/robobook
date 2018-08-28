#!/usr/bin/env python

import RPi.GPIO as GPIO
import sys,os,random,math
import curses
import urllib2, urllib, commands, json
import shlex, subprocess, pexpect
import threading
from PIL import Image
from colour import Color

from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics
from time import sleep


LED_IMAGE_VIEWER_PATH = "/home/pi/led-image-viewer"

brightness = 60
process = None
lbt = None
mode = "off"

matrix = None
particles = []
lbinstr = ""

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

import sys
import select
import tty
import termios

matrix = None
particles = []
lbinstr = ""
binstr = ""

class LEDBin(threading.Thread):
    def run(self):
        global matrix
        global particles
        global lbinstr
        global binstr

        matrix = RGBMatrix(options = options)
        while True:
            # add new particles
            while (len(lbinstr) < len(binstr)):
                r = random.randint(10,30)
                pos = random.random()
                particles.append({'r': r, 'pos': pos,'x': random.randint(0,63), 'y': random.randint(53,63) if binstr[len(lbinstr)] == '0' else random.randint(0,10),
                    'dir': 0 if binstr[len(lbinstr)] == '0' else 1, 'life': 100000, 'speed': random.uniform(0.01, 0.02)})
                lbinstr += binstr[len(lbinstr)]

                while (len(particles) > 300):
                    particles.pop(0)

            sleep(refreshrate)
            offset_canvas = matrix.CreateFrameCanvas()
            nmatrix = [[0 for x in range(64)] for y in range(64)]

            nparticles = []

            for p in particles:
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
                    nmatrix[p['x']][p['y']] = 1

                    if p['dir'] == 1 and p['y'] < 63 and nmatrix[p['x']][p['y'] + 1] == 0:
                        p['y'] += 1
                    elif p['dir'] == 0 and p['y'] > 0 and nmatrix[p['x']][p['y'] - 1] == 0:
                        p['y'] -= 1
                    elif p['dir'] == 1 and (p['y'] == 63 or nmatrix[p['x']][p['y'] + 1] != 0):
                        p['dir'] = 0
                    elif p['dir'] == 0 and (p['y'] == 0 or nmatrix[p['x']][p['y'] - 1] != 0):
                        p['dir'] = 1

                    if p['life'] > 0:
                        nparticles.append(p)

                    p['life'] -= 11
                else:
                    r = random.randint(0,255*brightness/100)
                    g = random.randint(0,255*brightness/100)
                    b = random.randint(0,255*brightness/100)
                    offset_canvas.SetPixel(p['x'], p['y'], r, g, b)
                    nmatrix[p['x']][p['y']] = 1

                    if p['dir'] == 1 and p['y'] < 63 and nmatrix[p['x']][p['y'] + 1] == 0:
                        p['y'] += 1
                    elif p['dir'] == 0 and p['y'] > 0 and nmatrix[p['x']][p['y'] - 1] == 0:
                        p['y'] -= 1

                    if p['life'] > 0:
                        nparticles.append(p)

                    p['life'] -= 1

            particles = nparticles

            offset_canvas = matrix.SwapOnVSync(offset_canvas)

lbt = LEDBin()
lbt.daemon = True
lbt.start()

while True:
    line = sys.stdin.readline()
    print 'adding' + line[0]
    binstr += line[0]
