Thunderbird Desktop Notifications
===================================

This program gives you popup desktop notifications when thunderbird receives a new email.

---------------------------
Features of this solution
---------------------------

1. On new emails, shows standard desktop notifications, containing

  * Mail subject
  * Sender name
  * Thunderbird icon

2. Can click notification, which brings up the Thunderbird window

Unfortunately, the Gnome Integration add-on stopped working correctly with Thunderbird 60, and never provided the second feature.

------------------
How to set up
------------------

1. Install the necessary python libraries. The packages are likely called
  
   * dbus-python (install from distribution)
   * pygobject (install from distribution)
   * notify2 (install with pip)

   If you installed correctly, the following must work without ImportErrors::

	$ python -c 'import multiprocessing, dbus, notify2, gi, argparse, threading'

2. Install the "Mailbox Alert" extension in Thunderbird (Alternatively, you can also use FiltaQuilla)
3. create a new alert that launches a command for a new email.

The command should be this script, i.e.:

/home/user/Downloads/tnewmail/tnewmail.sh "Mail from %sendername" "%subject"

The first argument is the title, the second is the body of the popup

For more placeholders, see https://tjeb.nl/Projects/Mailbox_Alert/Manual/


------------------
How it works
------------------

This script runs in two different ways:
When executed for the first time, it is running as a server, and keeps running.
When executed again, it merely forwards its message to the server and stops.

The server creates a TCP socket and receives messages about new notifications (title and body) to show.
It presents these as Dbus notifications.
It also installs a callback when the notifications are clicked. When clicked,
it runs thunderbird, which raises the Thunderbird window.

----------------------------
Try it out and Debugging
----------------------------

For a dry-run, do this first:

**Step 1**::

	$ python /home/user/Downloads/tnewmail/tnewmail.py --summary "Mail from foo" --body "bar"

This should give you a popup and hopefully no error message. It should also keep running.

You can add more arguments, such as the icon path::

	$ python /home/user/Downloads/tnewmail/tnewmail.py --help

**Step 2**: Second execution, which runs the client:

	$ python /home/user/Downloads/tnewmail/tnewmail.py --summary "Mail from foo 2" --body "blah"

This should give you a popup again. It should terminate immediately.

**Step 3**: Run through wrapper script::

	$ /home/user/Downloads/tnewmail/tnewmail.sh "Mail from foo" "bar"

This writes to a log file /tmp/tnewmail.log so you can debug issues.

Add any additional command line modifications in the wrapper script.

**Step 4**: Do not forget that when you change settings in the tnewmail.sh script, you need to kill the server so it starts with new settings. You can find the python process with::

	pgrep -f "python.*tnewmail.py"

**Step 5**: Set up Mailbox Alert to run the wrapper script, by setting the command to::

	/home/user/Downloads/tnewmail/tnewmail.sh "Mail from %sendername" "%subject"

Mailbox Alert needs full paths.

-----------------
Issues
-----------------

* Missing features:

  * Please open a Github issue.

* Potential security issues:

  * Forwarding arbitrary strings from mails to desktop notification could be exploited. Perhaps some filtering should be applied. 
  
    * However, this is relevant for all desktop notification programs, so I expect that GNOME etc. already filter and remove problematic characters.
  
  * A clever attacker could maybe overwrite command line arguments such as --on-click-exec, the program to execute once clicked. 
  
    * However, if successful that would only work if it is done with the first new email.
    * Also, it should not work because the arguments are encapsulated throughout.


