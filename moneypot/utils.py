#coding: utf-8
import hashlib
import time


def create_identifier(username=''):
    '''create a unique identifier by time
    this is not really secure and should be overthougt'''
    #hashlib only "eats" strings, therefore encode unicodes in utf-8
    if type(username) == unicode:
        username = username.encode('utf-8')
    return hashlib.sha1(username + str(time.time())).hexdigest()[-10:]


def hash_password(clear_passwd):
    if type(clear_passwd) == unicode:
        clear_passwd = clear_passwd.encode('utf-8')
    return hashlib.sha512(clear_passwd).hexdigest()


def dummy_translate(x):
    return x
