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


def draw_menu(stdscr):

    k = 0

    # Clear and refresh the screen for a blank canvas
    stdscr.clear()
    stdscr.refresh()

    # Start colors in curses
    curses.start_color()
    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_WHITE)


    # Loop where k is the last character pressed
    while (k != ord('q')):

        process = pexpect.spawn(LED_IMAGE_VIEWER_PATH
            + " --led-rows=64 --led-cols=64 --led-brightness=" + str(brightness)
            + " /home/pi/robobook/greeting.gif")


        title = "ROBOBOOK 0.1"
        title += ("\nmode: ")

        # Centering calculations

        # Turning on attributes for title
        stdscr.attron(curses.color_pair(2))
        stdscr.attron(curses.A_BOLD)

        # Rendering title
        stdscr.addstr(0, 0, title)

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
