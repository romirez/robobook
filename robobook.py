#!/usr/bin/env python

import sys,os
import curses
import urllib2, urllib, commands, json
import shlex, subprocess

LED_IMAGE_VIEWER_PATH = "/home/pi/led-image-viewer"

brightness = 75
process = None

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

        # Initialization
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        title = "ROBOBOOK 0.1"[:width-1]

        if k == ord('1'):
            led_gif()
        elif k == 259:
            # Pushed 0
            title = "0"
        elif k == 350:
            # Pushed 1
            title = "1"
        elif k == 258:
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
