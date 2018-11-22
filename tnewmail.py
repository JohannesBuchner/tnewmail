"""
Helper program for popup desktop notifications when thunderbird receives a new email.
"""

"""
MIT License

Copyright (c) 2018 Johannes Buchner

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from dbus.mainloop.glib import DBusGMainLoop
from dbus.exceptions import DBusException
import os, sys
import signal, os
import notify2
import codecs
import traceback
import gi
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import GdkPixbuf, GLib
import argparse
from multiprocessing.connection import Listener, Client
from threading import Thread

class HelpfulParser(argparse.ArgumentParser):
        def error(self, message):
                sys.stderr.write('error: %s\n' % message)
                self.print_help()
                sys.exit(1)

parser = HelpfulParser(description=__doc__,
	epilog="""Johannes Buchner (C) 2018 <buchner.johannes@gmx.at>""",
	formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument('--icon-path', type=str,
	default="/usr/share/pixmaps/thunderbird-icon.png",
	help='Icon to show')

parser.add_argument('--summary', required=True, type=str,
	help='Notification summary')

parser.add_argument('--body', default='', type=str,
	help='Notification body')

parser.add_argument('--app-name', default='tnewmail', type=str,
	help='Name of app showing notification.')

parser.add_argument('--expire-time', default=0, type=int,
	help='Timeout in milliseconds at which to expire the notification. 0 means never.')

parser.add_argument('--on-click-exec', default='thunderbird', type=str,
	help='Program to run when clicking the notification')

parser.add_argument('--port', default=15100, type=int,
	help='Port to use for creating the server.')

cmdargs = parser.parse_args()

def sane_encoding(s):
	# remove weird symbols that will cause problems with dbus
	return codecs.decode(codecs.encode(s, errors='ignore'))

class NotifyHandler(object):
	def __init__(self):
		loop = DBusGMainLoop(set_as_default=True)

		notify2.init(cmdargs.app_name, mainloop=loop)
		if os.path.exists(cmdargs.icon_path):
			self.icon = GdkPixbuf.Pixbuf.new_from_file_at_size(cmdargs.icon_path, 25, 25)
		else:
			print("Warning: no icon found at: '%s'" % cmdargs.icon_path)
			self.icon = None

		self.mainloop = GLib.MainLoop()
	
	def run(self):
		self.mainloop.run()

	def on_clicked(self, *args, **kwargs):
		print("user clicked notification, opening '%s'" % cmdargs.on_click_exec)
		os.system(cmdargs.on_click_exec)
	
	def on_closed(self, *args, **kwargs):
		print("user closed it")
		#mainloop.quit()

	def show_new_message(self, summary, body):
		msg = notify2.Notification(sane_encoding(summary), sane_encoding(body))
		msg.timeout = cmdargs.expire_time
		if self.icon:
			msg.set_icon_from_pixbuf(self.icon)
		msg.add_action("default", "Open this", callback=self.on_clicked)
		msg.connect("closed", callback=self.on_closed)
		msg.show()

msg = (cmdargs.summary, cmdargs.body)

address = ('localhost', cmdargs.port)

def send_msg(msg):
	#print("starting send: open...")
	conn = Client(address)
	#print("starting send: send...")
	conn.send(msg)
	#print("starting send: close...")
	conn.close()
	#print("starting send: done.")


def run_listener(handler):
	while True:
		conn = listener.accept()
		#print('connection accepted from', listener.last_accepted)
		msg = conn.recv()
		# do something with msg
		try:
			print("showing msg:", msg)
			handler.show_new_message(*msg)
		except DBusException as e:
			print("Warning: showing message failed:", e)
			pass
		except Exception as e:
			print("UNEXPECTED ERROR:")
			traceback.print_exc()
			listener.close()
			# kill process from thread (haha!)
			os.kill(os.getpid(), signal.SIGKILL)
			pass

try:
	# Try to create a message server. This makes sure there is only one server running (otherwise Exception is raised)
	listener = Listener(address)
except Exception as e:
	if hasattr(e, 'errno') and e.errno == 98:
		# This occurs when there is already a server
		# So we give our message to the Server
		
		# Client mode:
		
		send_msg(msg)
		# we have done our job; terminate
		sys.exit(0)
	
	else: # re-raise exception, something odd happened
		raise e

# Server mode
handler = NotifyHandler()

listener_thread = Thread(target=run_listener, args=(handler,))
listener_thread.start()

self_msg_thread = Thread(target=send_msg, args=(msg,))
self_msg_thread.start()

try:
	handler.run()
except KeyboardInterrupt:
	# can reach here on Ctrl-C
	pass

# Shut down

print("shutting down process...")
handler.mainloop.quit()
#print("waiting for self-msg thread...")
self_msg_thread.join()
#print("waiting for listener thread...")
"""
listener_thread.join()
"""

# Harakiri
# This is necessary because there is no way to stop listener.accept, 
# and it cannot be in an independent process
os.kill(os.getpid(), signal.SIGKILL)


