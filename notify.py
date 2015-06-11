#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import sqlite3
import sys
import os
from time import sleep
from urllib2 import urlopen, URLError



def is_network_connection():
    """
    It is useless to notify user about things that require network
    connection (eg. mails) if the device is not conncted. Therefore
    we check connection and print only relevant notifications. Using
    Google page, as it loads quickly, and using directly IP address,
    so we avoid DNS lookup.
    """

    try:
        r = urlopen('http://74.125.228.100', timeout=1)
        return True
    except URLError:
        return False



def connect_db():
    try:
        notifications_db = sqlite3.connect(FILENAME)
        cursor = notifications_db.cursor()
        return (notifications_db, cursor)
    except sqlite3.Error as e:
        print '[ERROR]', e.args[0]
        sys.exit()



def notify():
    """
    Print notifications.

    If the script is not run from terminal (is run after boot), sleep
    for five minutes (eg the computer may take a while to connect to
    network (authentication is needed and so), then connect to new
    xterm to print out notifications.
    If there is not network connection, don't print notfications about
    mails, searching web etc. (depending on supported notification
    types).
    """

    notifications_db, cursor = connect_db()[0], connect_db()[1]

    cursor.execute('select * from notifications')
    notifications = cursor.fetchall()

    if not sys.stdout.isatty():
        sleep(5 * 60)
        xterm = 'xterm -e'
        bash = 'bash -c'
        cmd = 'python /home/veronika/Documents/py/notify/notify.py; bash'
        os.system('{} \'{} "{}"\''.format(xterm, bash, cmd))

    is_connection = True if is_network_connection() else False
    if not is_connection:
        print 'You have no network connection, showing only notifications'\
              ' where it may not be\nnecessary:\n'

    for notification in notifications:
        if not is_connection and notification[0] in [1]:
            continue
        print notification[0], ' ', INDEX_TO_TYPE[notification[1]],\
              notification[2]

    notifications_db.close()



def usage(args):
    print '[usage, u] for usage\n' \
          '<type of notification> <notes> for creating new notification\n'\
          '\t\ttype is one of [mail, work, study], notes < 70chars\n' \
          '[remove, r] <number> for removing given notification'



def create_new_notification(args):
    """
    Insert new notification into database.

    If no database exists (new user, file was deleted, ...), create
    new. Get the number of the new notification, check if the
    notification type is supported and insert the notification to
    database.
    """

    notifications_db, cursor = connect_db()[0], connect_db()[1]

    cursor.execute('create table if not exists notifications '
                   '(n integer, type integer, notes text)')

    cursor.execute('select count(*) from notifications')

    notification_number = cursor.fetchone()[0] + 1

    try:
        notification_type = TYPE_TO_INDEX[args[0]]
    except KeyError:
        print '[ERROR] Not supported type, see "<script> u" for possible'\
              ' types'
        return

    notification_body = ' '.join(args[1:])

    cursor.execute(
            'insert into notifications(n, type, notes) values (?, ?, ?)',
            (notification_number, notification_type, notification_body))

    notifications_db.commit()
    notifications_db.close()




def remove_notification(args):
    notifications_db, cursor = connect_db()[0], connect_db()[1]

    cursor.execute('delete from notifications where n = ?', (int(args[1]),))

    notifications_db.commit()
    cursor.execute('select * from notifications')
    notifications_db.close()



"""Constants"""


TYPE_TO_INDEX = {
        'mail': 1,
        'study': 2,
        'work': 3
        }

INDEX_TO_TYPE = {
        1: 'mail',
        2: 'study',
        3: 'work'
        }

FUNCTION_MAPPING = {
        'usage': usage,
        'u': usage,
        'notify': notify,
        'n': notify,
        'remove': remove_notification,
        'r': remove_notification
        }

FILENAME = os.path.expanduser('~') + '/.notify'



def main():
    if len(sys.argv) == 1:
        notify()
        return
    FUNCTION_MAPPING.get(sys.argv[1], create_new_notification)(sys.argv[1:])


if __name__ == '__main__':
    main()
