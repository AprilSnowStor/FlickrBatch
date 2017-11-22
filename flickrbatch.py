#!/usr/bin/env python

# SEE LICENSE IN FILE LICENSE.txt

# Python script to update and manipulate photos and videos on Flickr.

# Inspired from:
#   https://github.com/trickortweak/flickr-uploader
#   https://github.com/julienc91/ShFlickr

# TODO:
# flickr.places.find
#   https://www.flickr.com/services/api/flickr.places.find.html
# flickr.places.getInfo
#   https://www.flickr.com/services/api/flickr.places.getInfo.html
# flickr.prefs.getContentType
#   https://www.flickr.com/services/api/flickr.prefs.getContentType.html
# flickr.prefs.getGeoPerms
#   https://www.flickr.com/services/api/flickr.prefs.getGeoPerms.html
# flickr.prefs.getHidden
#   https://www.flickr.com/services/api/flickr.prefs.getHidden.html
# flickr.prefs.getPrivacy
#   https://www.flickr.com/services/api/flickr.prefs.getPrivacy.html
# flickr.prefs.getSafetyLevel
#   https://www.flickr.com/services/api/flickr.prefs.getSafetyLevel.html


import logging

import os
import getopt
import re
import sys
import argparse
import fcntl

import time, datetime
from datetime import datetime
import webbrowser
import ConfigParser
from multiprocessing import Lock, Process, Queue, current_process
from PIL import Image
import imghdr, urllib2, mimetypes
import sqlite3 as lite
import hashlib
import flickrapi


if sys.version_info < (2, 7):
    sys.stderr.write('This script requires Python 2.7 or newer.\n')
    sys.stderr.write('Current version: ' + sys.version + '\n')
    sys.stderr.flush()
    sys.exit(1)


class BColors:
    BLACK     = '\033[90;1m'
    RED       = '\033[91;1m'
    GREEN     = '\033[92;1m'
    YELLOW    = '\033[93;1m'
    BLUE      = '\033[94;1m'
    MAGENTA   = '\033[95;1m'
    CYAN      = '\033[96;1m'
    WHITE     = '\033[97;1m'
    BOLD      = '\033[1m'
    RESET     = '\033[0m'
    UNDERLINE = '\033[4m'


config = ConfigParser.ConfigParser()

# CONFIG_DIR = $HOME/.config/flickrbatch
CONFIG_DIR = os.path.join(os.environ['HOME'],'.config/flickrbatch')
# CONFIG_INI = $HOME/.config/flickrbatch/config.ini
CONFIG_INI = os.path.join(os.environ['HOME'],'.config/flickrbatch/config.ini')

if not (os.path.isdir(CONFIG_DIR)):
    os.mkdir(CONFIG_DIR, 0700)
if not os.path.exists(CONFIG_INI):
    print('\n')
    print('*** %sFlickrBatch%s' % (BColors.BOLD, BColors.RESET))
    print('*** Copy your config.ini file in %s' % CONFIG_DIR)
    print('*** Make sure your have put your API key and secret you got')
    print('*** from <http://www.flickr.com/services/apps/create/apply>.')
    print('\n')
    sys.exit(1)

config.read(CONFIG_INI)

USER_ID                = eval(config.get('Config', 'USER_ID'))
FLICKR                 = eval(config.get('Config', 'FLICKR'))
PICTURE_FOLDER_PATH    = eval(config.get('Config', 'PICTURE_FOLDER_PATH'))
PICTURE_EXTENSIONS     = eval(config.get('Config', 'PICTURE_EXTENSIONS'))
SUBFOLDERS_REGEXP      = eval(config.get('Config', 'SUBFOLDERS_REGEXP'))
DB_PATH                = eval(config.get('Config', 'DB_PATH'))
LOCK_PATH              = eval(config.get('Config', 'LOCK_PATH'))
MAX_RETRIES            = eval(config.get('Config', 'MAX_RETRIES'))
MAX_CONSECUTIVE_ERRORS = eval(config.get('Config', 'MAX_CONSECUTIVE_ERRORS'))

#EXCLUDED_FOLDERS       = eval(config.get('Config', 'EXCLUDED_FOLDERS'))
#IGNORED_REGEX          = [re.compile(regex) for regex in eval(config.get('Config', 'IGNORED_REGEX'))]
#RAW_EXT                = eval(config.get('Config', 'RAW_EXT'))
#FILE_MAX_SIZE          = eval(config.get('Config', 'FILE_MAX_SIZE'))
#RAW_TOOL_PATH          = eval(config.get('Config', 'RAW_TOOL_PATH'))
#CONVERT_RAW_FILES      = eval(config.get('Config', 'CONVERT_RAW_FILES'))

#--------------------------------------------------------------------------------------
class FlickrBatch:

    flickr = None
    permission = u'delete'
    debug = 0


    #----------------------------------------------------------------------------------
    def __init__(self):
        '''
        Constructor
        '''
        print('+-------------------------------------+')
        print('|        %sF L I C K R B A T C H%s        |' % (BColors.BOLD, BColors.RESET))
        print('+-------------------------------------+')
        self.flickr = self.authentication(self.permission)


    #----------------------------------------------------------------------------------
    def authentication(self, permission):
        print('')
        print('----------------------------------------------------------------------')
        print('Authentication')

        try:
            flickr = flickrapi.FlickrAPI(FLICKR['api_key'], FLICKR['api_secret'], format='etree')

            if self.debug:
                print(flickr)

            flickr.authenticate_via_browser(perms=permission)

            return flickr

        except flickrapi.exceptions.FlickrError as ex:
            print(ex[0])


    #----------------------------------------------------------------------------------
    def get_user_profile(self, flickr, user_id):
        '''
        '''
        print('--- PROFILE')

        try:
            profile = flickr.profile.getProfile(user_id=user_id)

            if self.debug == 1:
                print('--- get_user_info ------')
                from xml.etree import ElementTree as ET
                ET.dump(profile)

            info = profile.find('profile')

            user_id = info.attrib['id']
            nsid = info.attrib['nsid']
            join_date = info.attrib['join_date']

            occupation = info.attrib['occupation']
            hometown = info.attrib['hometown']
            showcase_set = info.attrib['showcase_set']
            first_name = info.attrib['first_name']
            last_name = info.attrib['last_name']
            profile_description = info.attrib['profile_description']
            city = info.attrib['city']
            country = info.attrib['country']
            facebook = info.attrib['facebook']
            twitter = info.attrib['twitter']
            tumblr = info.attrib['tumblr']
            instagram = info.attrib['instagram']
            pinterest = info.attrib['pinterest']

            join_date = datetime.fromtimestamp(int(join_date)).strftime('%Y-%m-%d')

            print('USER ID: %s%s%s' % (BColors.RED, user_id, BColors.RESET))
            print('JOINED: %s' % join_date)
            print('OCCUPATION: %s' % occupation)
            print('HOMETOWN: %s' % hometown)
            print('SHOWCASE SET: %s' % showcase_set)
            print('FIRST NAME: %s' % first_name)
            print('LAST NAME: %s' % last_name)
            print('PROFILE DESCRIPTION: %s' % profile_description)
            print('CITY: %s' % city)
            print('COUNTRY: %s' % country)
            print('FACEBOOK: %s' % facebook)
            print('TWITTER: %s' % twitter)
            print('TUMBLR: %s' % tumblr)
            print('INSTAGRAM: %s' % instagram)
            print('PINTEREST: %s' % pinterest)

        except flickrapi.exceptions.FlickrError as ex:
            print(ex[0])


    #----------------------------------------------------------------------------------
    def get_user_info(self, flickr, user_id):
        '''
        Get information about a user.

        https://www.flickr.com/services/api/flickr.people.getInfo.html
        '''

        print('')
        print('----------------------------------------------------------------------')
        print('Get user info.')

        try:
            user = flickr.people.getInfo(user_id=user_id)

            if self.debug == 1:
                print('--- get_user_info ------')
                from xml.etree import ElementTree as ET
                ET.dump(user)

            attributes =  user.find('person')

            ispro      = attributes.attrib['ispro']
            path_alias = attributes.attrib['path_alias']
            if 'gender' in attributes.attrib:
                gender     = attributes.attrib['gender']

            username       = attributes.find('username').text
            realname       = attributes.find('realname')
            if not realname == None:
                realname = realname.text
            location       = attributes.find('location')
            if not location == None:
                location = location.text
            timezone       = attributes.find('timezone')
            label       = None
            offset      = None
            timezone_id = None
            if not timezone == None:
                label       = timezone.attrib['label']
                offset      = timezone.attrib['offset']
                timezone_id = timezone.attrib['timezone_id']
            photosurl      = attributes.find('photosurl').text
            profileurl     = attributes.find('profileurl').text
            mobileurl      = attributes.find('mobileurl').text
            count          = attributes.find('photos').find('count')
            if not count == None:
                count = count.text
            views          = attributes.find('photos').find('views')
            if not views == None:
                views = views.text
            firstdatetaken = attributes.find('photos').find('firstdatetaken')
            if not firstdatetaken == None:
                firstdatetaken = firstdatetaken.text
            firstdate      = attributes.find('photos').find('firstdate')
            if not firstdate == None:
                firstdate = firstdate.text

            print('USER ID: %s%s%s' % (BColors.RED, user_id, BColors.RESET))
            print('IS PRO: %s' % (ispro))
            print('USERNAME: %s' % (username))
            print('REALNAME: %s' % (realname))
            if 'gender' in attributes.attrib:
                print('GENDER: %s' % (gender))
            print('PATH ALIAS: %s' % (path_alias))
            print('LOCATION: %s' % (location))
            print('TIMEZONE: %s' % (label))
            print('OFFSET: %s' % (offset))
            print('TIMEZONE ID: %s' % (timezone_id))
            print('PHOTOS URL: %s%s%s' % (BColors.BLUE, photosurl, BColors.RESET))
            print('PROFILE URL: %s%s%s' % (BColors.BLUE, profileurl, BColors.RESET))
            print('MOBILE URL: %s%s%s' % (BColors.BLUE, mobileurl, BColors.RESET))
            print('NUMBER OF PHOTOS: %s' % (count))
            print('NUMBER OF VIEWS: %s' % (views))
            print('FIRST PHOTO TAKEN: %s' % (firstdatetaken))
            if firstdate == None:
                print('JOINED: N/A')
            else:
                print('JOINED: %s' % datetime.fromtimestamp(int(firstdate)).strftime('%Y-%m-%d'))

            if ispro == '1':
                try:
                    views = flickr.stats.getTotalViews()

                    if self.debug == 1:
                        from xml.etree import ElementTree as ET
                        ET.dump(views)

                    total = views.find('stats').find('total').attrib['views']
                    photos = views.find('stats').find('photos').attrib['views']
                    photostream = views.find('stats').find('photostream').attrib['views']
                    sets = views.find('stats').find('sets').attrib['views']
                    collections = views.find('stats').find('collections').attrib['views']

                    print('TOTAL: %s' % (total))
                    print('PHOTOS: %s' % (photos))
                    print('PHOTOSTREAM: %s' % (photostream))
                    print('SETS: %s' % (sets))
                    print('COLLECTIONS: %s' % (collections))

                except flickrapi.exceptions.FlickrError as ex:
                    print(ex[0])
            else:
                print('No stats. Not a Pro account.')

            self.get_user_profile(flickr, user_id)

        except flickrapi.exceptions.FlickrError as ex:
            print(ex[0])


    #----------------------------------------------------------------------------------
    # NOT WORKING!
    def get_method_info(self, flickr, method_name):
        '''
        Returns information for a given flickr API method.

        option --get-method-info or -gmi with --method-name or -mn
        
        https://www.flickr.com/services/api/flickr.reflection.getMethodInfo.html
        '''

        print('')
        print('----------------------------------------------------------------------')
        print('Method name: %s' % method_name)
        print type(method_name)

        try:
            # TypeError: do_flickr_call() got multiple values for keyword argument 'method_name'
            infos = flickr.reflection.getMethodInfo(method_name=method_name)

            if self.debug == 1:
                from xml.etree import ElementTree as ET
                ET.dump(infos)

            #info = infos.find('infos').findall('info')
            #print('List available brands (%s brands)' % (len(brand)))

        except flickrapi.exceptions.FlickrError as ex:
            print(ex[0])

    #----------------------------------------------------------------------------------
    def find_userid_by_email(self, flickr, find_email):
        '''
        Return a user's NSID, given their email address

        With option -gue or --get-user-by-email and --email
        
        https://www.flickr.com/services/api/flickr.people.findByEmail.html
        '''

        try:
            user = flickr.people.findByEmail(find_email=find_email)

            if self.debug == 1:
                from xml.etree import ElementTree as ET
                ET.dump(user)

            nsid = user.find('user').attrib['nsid']
            username = user.find('user').find('username').text

            print('USERNAME: %s' % username)
            print('NSID: %s%s%s' % (BColors.RED, nsid, BColors.RESET))

            return nsid

        except flickrapi.exceptions.FlickrError as ex:
            print(ex[0])


    #----------------------------------------------------------------------------------
    def find_userid_by_username(self, flickr, username):

        try:
            user = flickr.people.findByUsername(username=username)

            if self.debug == 1:
                from xml.etree import ElementTree as ET
                ET.dump(user)

            nsid = user.find('user').attrib['nsid']
            username = user.find('user').find('username').text

            print('USERNAME: %s' % username)
            print('NSID: %s%s%s' % (BColors.RED, nsid, BColors.RESET))

            return nsid

        except flickrapi.exceptions.FlickrError as ex:
            print(ex[0])


    def lookup_user(self, flickr, url):
        '''
        Returns a user NSID, given the url to a user's photos or profile.

        https://www.flickr.com/services/api/flickr.urls.lookupUser.html
        '''

        print('')
        print('----------------------------------------------------------------------')
        print('Lookup user with url.')

        try:
            info = flickr.urls.lookupUser(url=url)

            if self.debug == 1:
                from xml.etree import ElementTree as ET
                ET.dump(info)

            user_id = info.find('user').attrib['id']
            username = info.find('user').find('username').text

            print('USER ID: %s' % user_id)
            print('USERNAME: %s' % username)

        except flickrapi.exceptions.FlickrError as ex:
            print(ex[0])


    def get_user_profile_url(self, flickr, user_id):
        '''
        '''

        print('')
        print('----------------------------------------------------------------------')
        print('Get user''s profile url.')

        try:
            info = flickr.urls.getUserProfile(user_id=user_id)

            nsid = info.find('user').attrib['nsid']
            url  = info.find('user').attrib['url']

            print('NSID: %s' % nsid)
            print('USER''S PROFILE URL: %s' % url)

        except flickrapi.exceptions.FlickrError as ex:
            print(ex[0])


    def get_user_photos_url(self, flickr, user_id):
        '''
        Returns the url to a user's photos

        https://www.flickr.com/services/api/flickr.urls.getUserPhotos.html
        '''

        print('')
        print('----------------------------------------------------------------------')
        print('Get user''s photo url.')

        try:
            info = flickr.urls.getUserPhotos(user_id=user_id)

            nsid = info.find('user').attrib['nsid']
            url  = info.find('user').attrib['url']

            print('NSID: %s' % nsid)
            print('USER''S PHOTOS URL: %s' % url)

        except flickrapi.exceptions.FlickrError as ex:
            print(ex[0])

    #----------------------------------------------------------------------------------
    def get_photoset_list(self, flickr, user_id):
        '''
        Returns the photosets belonging to the specified user.

        https://www.flickr.com/services/api/flickr.photosets.getList.html
        '''

        # Get all photoset from user_id
        print('')
        print('----------------------------------------------------------------------')
        print('Get photo set from a given user.')

        try:
            photosets = flickr.photosets.getList(user_id=user_id, per_page=500)

            if self.debug == 1:
                from xml.etree import ElementTree as ET
                ET.dump(photosets)

            pages = photosets.find('photosets').attrib['pages']
            total = photosets.find('photosets').attrib['total']

            print('---- SETS ----------------------------')
            print('NUMBER OF SETS: %s (%s pages)' % (total, pages))

            idx = 0
            for ipage in range(1,int(pages)+1,1):
                photosets = flickr.photosets.getList(user_id=user_id, per_page=500, page=ipage)

                photoset = photosets.find('photosets').findall('photoset')

                for iphotoset in range(len(photoset)):
                    a = photoset[iphotoset]

                    self.print_photoset_info(idx, a)

                    idx = idx+1

            if total == '0':
                print('Found no set.')
            else:
                print('Found a total of %s sets.' % (total))

        except flickrapi.exceptions.FlickrError as ex:
            print(ex[0])

    #----------------------------------------------------------------------------------
    def print_photoset_info(self, photoset_idx, a):

        photoset_id = a.attrib['id']
        photos      = a.attrib['photos']
        videos      = a.attrib['videos']
        date_create = a.attrib['date_create']
        title       = a.find('title').text
        description = a.find('description').text

        date_create = datetime.fromtimestamp(int(date_create)).strftime('%Y-%m-%d')

        print('%d :: TITLE: %s\t | DESCRIPTION: %s | PHOTOS: %s | VIDEOS: %s | CREATED: %s | PHOTOSET ID: %s%s%s' %
                (photoset_idx, title, description, photos, videos, date_create, BColors.RED, photoset_id, BColors.RESET))

        return photoset_id


    #----------------------------------------------------------------------------------
    def get_photoset_info(self, flickr, user_id, photoset_id, print_info=1):
        '''
        Gets information about a photoset.

        https://www.flickr.com/services/api/flickr.photosets.getInfo.html
        '''

        if print_info:
            print('')
            print('----------------------------------------------------------------------')
            print('Get photoset info.')

            print('')
            print('--- USER ID: %s | PHOTOSET %s ----------------' % (user_id, photoset_id))

        try:
            user = flickr.people.getInfo(user_id=user_id)

            path_alias =  user.find('person').attrib['path_alias']
        except flickrapi.exceptions.FlickrError as ex:
            print(ex[0])

        try:
            info = flickr.photosets.getInfo(photoset_id=photoset_id, user_id=user_id)

            if self.debug == 1:
                from xml.etree import ElementTree as ET
                ET.dump(info)

            owner        = info.find('photoset').attrib['owner']
            username     = info.find('photoset').attrib['username']
            photos       = info.find('photoset').attrib['photos']
            count_photos = info.find('photoset').attrib['count_photos']
            count_videos = info.find('photoset').attrib['count_videos']
            date_create  = info.find('photoset').attrib['date_create']
            date_update  = info.find('photoset').attrib['date_update']
            primary      = info.find('photoset').attrib['primary']
            title        = info.find('photoset').find('title').text
            description  = info.find('photoset').find('description').text

            date_create = datetime.fromtimestamp(int(date_create)).strftime('%Y-%m-%d')
            date_update = datetime.fromtimestamp(int(date_update)).strftime('%Y-%m-%d')

            if print_info:
                print('\tTITLE: %s' % (title))
                print('\tDESCRIPTION: %s' % (description))
                print('\tPRIMARY PHOTO: %s' % (primary))
                print('\tPHOTOS: %s' % (photos))
                print('\tCOUNT PHOTOS: %s' % (count_photos))
                print('\tCOUNT VIDEOS: %s' % (count_videos))
                print('\tCREATED: %s' % (date_create))
                print('\tUPDATED: %s' % (date_update))
                print('\tPHOTOSET ID: %s%s%s' % (BColors.RED, photoset_id, BColors.RESET))
                print('\tPHOTOSET URL: %shttps://www.flickr.com/photos/%s/albums/%s%s' %
                        (BColors.BLUE, path_alias, photoset_id, BColors.RESET))

            return owner, username, photos, count_photos, count_videos, date_create, date_update, primary, title, description

        except flickrapi.exceptions.FlickrError as ex:
            print(ex[0])


    #----------------------------------------------------------------------------------
    def create_photoset(self, flickr, title, description, primary_photo_id):
        '''
        Create a new photoset for the calling user.

        https://www.flickr.com/services/api/flickr.photosets.create.html
        '''

        print('')
        print('----------------------------------------------------------------------')
        print('Create photoset (title: %s, description: %s, primary photo id: %s).' % (title, description, primary_photo_id))

        con = lite.connect(DB_PATH)
        con.text_factory = str

        try:
            create = flickr.photosets.create(title=title, description=description, primary_photo_id=primary_photo_id)

            if self.debug == 1:
                from xml.etree import ElementTree as ET
                ET.dump(create)

            photoset_id = create.find('photoset').attrib['id']
            url         = create.find('photoset').attrib['url']

            print('Photoset created (photoset id: %s%s%s, url: %s%s%s)' %
                    (BColors.RED, photoset_id, BColors.RESET, BColors.RED, url, BColors.RESET))

            cur = con.cursor()
            cur.execute("INSERT INTO sets (set_id, name, primary_photo_id) VALUES (?,?,?)", (photoset_id, title, primary_photo_id))
            cur.execute("UPDATE files SET set_id = ? WHERE files_id = ?", (photoset_id, primary_photo_id))
            con.commit()

        except flickrapi.exceptions.FlickrError as ex:
            print(ex[0])


    #----------------------------------------------------------------------------------
    def delete_photoset(self, flickr, photoset_id):
        '''
        Delete a photoset.

        https://www.flickr.com/services/api/flickr.photosets.delete.html
        '''

        if args.dry_run:
            print('\nDRY-RUN :: Delete photoset (photoset id: %s).' % (photoset_id))
            return True

        print('')
        print('----------------------------------------------------------------------')
        print('Delete photoset (photoset id: %s).' % (photoset_id))

        con = lite.connect(DB_PATH)
        con.text_factory = str

        try:
            delete = flickr.photosets.delete(photoset_id=photoset_id)

            if self.debug == 1:
                from xml.etree import ElementTree as ET
                ET.dump(create)

            print('Photoset deleted.')

            cur = con.cursor()

            # Let's check if a record for the photoset exists in the database.
            cur.execute("SELECT set_id FROM sets WHERE set_id = ?", (photoset_id,))
            row = cur.fetchone()

            if not row == None:
                cur.execute("DELETE FROM sets WHERE set_id = ?", (photoset_id,))
                con.commit()
            else:
                print('No record found in the database for photoset (id %s).' % photoset_id)

        except flickrapi.exceptions.FlickrError as ex:
            print(ex[0])


    #----------------------------------------------------------------------------------
    def modify_photoset_metadata(self, flickr, photoset_id, title, description):
        '''
        Modify the meta-data for a photoset.

        https://www.flickr.com/services/api/flickr.photosets.editMeta.html
        '''

        print('')
        print('----------------------------------------------------------------------')
        print('Modify the meta-data for a photoset (photoset id: %s%s%s).' % (BColors.RED, photoset_id, BColors.RESET))

        try:
            meta = flickr.photosets.editMeta(photoset_id=photoset_id, title=title, description=description)

            if self.debug == 1:
                from xml.etree import ElementTree as ET
                ET.dump(meta)

            print('Photoset''s meta-data modified.')

        except flickrapi.exceptions.FlickrError as ex:
            print(ex[0])


    #----------------------------------------------------------------------------------
    def get_photo_list(self, flickr, user_id, photoset_id):
        '''
        Returns the photosets belonging to the specified user.
        Get the list of photos in a set.

        https://www.flickr.com/services/api/flickr.photosets.getList.html
        https://www.flickr.com/services/api/flickr.photosets.getPhotos.html
        '''

        print('')
        print('----------------------------------------------------------------------')
        print('Get photos from a given photo set.')

        print('---- PHOTOS --------------------------')

        try:
            photos = flickr.photosets.getPhotos(photoset_id=photoset_id, user_id=user_id, per_page=500)

            if self.debug == 1:
                from xml.etree import ElementTree as ET
                ET.dump(photos)

            total = photos.find('photoset').attrib['total']
            pages = photos.find('photoset').attrib['pages']

            print('Total number of photos in album %s : %s (%s pages)' % (photoset_id, total, pages))

            idx = 0
            for ipage in range(1,int(pages)+1,1):
                photos = flickr.photosets.getPhotos(photoset_id=photoset_id, user_id=user_id, per_page=500, page=ipage)

                photo = photos.find('photoset').findall('photo')

                for iphoto in range(len(photo)):
                    a = photo[iphoto]

                    photo_id = a.attrib['id']
                    title    = a.attrib['title']
                    ispublic = a.attrib['ispublic']
                    isfriend = a.attrib['isfriend']
                    isfamily = a.attrib['isfamily']

                    print('%d :: PHOTO ID: %s%s%s | TITLE: %s | IS PUBLIC: %s | IS FRIEND: %s | IS FAMILY: %s' %
                            (idx, BColors.RED, photo_id, BColors.RESET, title, ispublic, isfriend, isfamily))

                    idx = idx+1

            if total == '0':
                print('Found no photo.')
            else:
                print('Found a total of %s photos.' % (total))

        except flickrapi.exceptions.FlickrError as ex:
            print(ex[0])


    #----------------------------------------------------------------------------------
    def get_photos_not_in_set(self, flickr, privacy_filter, media, max_taken_date, min_taken_date, max_upload_date, min_upload_date):
        '''
        Returns a list of your photos that are not part of any sets.

        https://www.flickr.com/services/api/flickr.photos.getNotInSet.html
        '''

        print('')
        print('----------------------------------------------------------------------')
        print('Get photos not in any set.')

        print('---- PHOTOS --------------------------')

        try:

            if max_taken_date == None:
                max_taken_date = ''
            else:
                max_taken_date = time.mktime(datetime.strptime(max_taken_date, '%Y-%m-%d').timetuple())

            if min_taken_date == None:
                min_taken_date = ''
            else:
                min_taken_date = time.mktime(datetime.strptime(min_taken_date, '%Y-%m-%d').timetuple())

            if max_upload_date == None:
                max_upload_date = ''
            else:
                max_upload_date = time.mktime(datetime.strptime(max_upload_date, '%Y-%m-%d').timetuple())

            if min_upload_date == None:
                min_upload_date = ''
            else:
                min_upload_date = time.mktime(datetime.strptime(min_upload_date, '%Y-%m-%d').timetuple())

            photos = flickr.photos.getNotInSet(
                            privacy_filter=privacy_filter,
                            media=media,
                            max_taken_date=max_taken_date, min_taken_date=min_taken_date,
                            max_upload_date=max_upload_date, min_upload_date=min_upload_date,
                            per_page=500)

            if self.debug == 1:
                from xml.etree import ElementTree as ET
                ET.dump(photos)

            pages = photos.find('photos').attrib['pages']
            total = photos.find('photos').attrib['total']

            print('Total number of photos : %s (%s pages)' % (total, pages))

            idx = 0
            for ipage in range(1,int(pages)+1,1):
                photos = flickr.photos.getNotInSet(
                                privacy_filter=privacy_filter,
                                media=media,
                                max_taken_date=max_taken_date, min_taken_date=min_taken_date,
                                max_upload_date=max_upload_date, min_upload_date=min_upload_date,
                                per_page=500, page=ipage)

                photo = photos.find('photos').findall('photo')

                for iphoto in range(len(photo)):
                    a = photo[iphoto]

                    photo_id  = a.attrib['id']
                    owner     = a.attrib['owner']
                    title     = a.attrib['title']
                    ispublic  = a.attrib['ispublic']
                    isfriend  = a.attrib['isfriend']
                    isfamily  = a.attrib['isfamily']

                    print('%d :: PHOTO ID: %s%s%s | TITLE: %s | OWNER: %s | IS PUBLIC: %s | IS FRIEND: %s | IS FAMILY: %s' %
                            (idx, BColors.RED, photo_id, BColors.RESET, title, owner, ispublic, isfriend, isfamily))

                    idx = idx+1

            if total == '0':
                print('Found no photo.')
            else:
                print('Found a total of %s photos.' % (total))

        except flickrapi.exceptions.FlickrError as ex:
            print(ex[0])


    #----------------------------------------------------------------------------------
    def get_public_photos(self, flickr, user_id, safe_search):
        '''
        Get a list of public photos for the given user.

        https://www.flickr.com/services/api/flickr.people.getPublicPhotos.html
        '''

        print('')
        print('----------------------------------------------------------------------')
        print('Get photos not in any set.')

        print('---- PHOTOS --------------------------')

        try:
            photos = flickr.people.getPublicPhotos(
                            user_id=user_id,
                            safe_search=safe_search,
                            per_page=500)
            #photos = flickr.people.getPhotos(
            #                user_id=user_id,
            #                safe_search=safe_search,
            #                per_page=500)

            if self.debug == 1:
                from xml.etree import ElementTree as ET
                ET.dump(photos)

            pages = photos.find('photos').attrib['pages']
            total = photos.find('photos').attrib['total']

            print('Total number of photos : %s (%s pages)' % (total, pages))

            idx = 0
            for ipage in range(1,int(pages)+1,1):
                photos = flickr.people.getPublicPhotos(
                                user_id=user_id,
                                safe_search=safe_search,
                                per_page=500, page=ipage)
                #photos = flickr.people.getPhotos(
                #                user_id=user_id,
                #                safe_search=safe_search,
                #                per_page=500, page=ipage)

                photo = photos.find('photos').findall('photo')

                for iphoto in range(len(photo)):
                    a = photo[iphoto]

                    photo_id  = a.attrib['id']
                    owner     = a.attrib['owner']
                    title     = a.attrib['title']
                    ispublic  = a.attrib['ispublic']
                    isfriend  = a.attrib['isfriend']
                    isfamily  = a.attrib['isfamily']

                    print('%d :: PHOTO ID: %s%s%s | TITLE: %s | OWNER: %s | IS PUBLIC: %s | IS FRIEND: %s | IS FAMILY: %s' %
                            (idx, BColors.RED, photo_id, BColors.RESET, title, owner, ispublic, isfriend, isfamily))

                    idx = idx+1

            if total == '0':
                print('Found no photo.')
            else:
                print('Found a total of %s photos.' % (total))

        except flickrapi.exceptions.FlickrError as ex:
            print(ex[0])


    #----------------------------------------------------------------------------------
    def get_popular_photos(self, flickr, user_id, sort):
        '''
        Returns a list of popular photos.

        https://www.flickr.com/services/api/flickr.photos.getPopular.html
        '''

        print('')
        print('----------------------------------------------------------------------')
        print('Returns a list of popular photos.')

        try:
            photos = flickr.photos.getPopular(user_id=user_id, sort=sort)

            if self.debug == 1:
                from xml.etree import ElementTree as ET
                ET.dump(photos)

            pages = photos.find('photos').attrib['pages']
            total = photos.find('photos').attrib['total']

            print('Total number of photos : %s (%s pages)' % (total, pages))

            idx = 0
            for ipage in range(1,int(pages)+1,1):
                photos = flickr.photos.getPopular(user_id=user_id, sort=sort, page=ipage)

                photo = photos.find('photos').findall('photo')

                for iphoto in range(len(photo)):
                    a = photo[iphoto]

                    photo_id  = a.attrib['id']
                    owner     = a.attrib['owner']
                    title     = a.attrib['title']
                    ispublic  = a.attrib['ispublic']
                    isfriend  = a.attrib['isfriend']
                    isfamily  = a.attrib['isfamily']

                    print('%d :: PHOTO ID: %s%s%s | TITLE: %s | OWNER: %s | IS PUBLIC: %s | IS FRIEND: %s | IS FAMILY: %s' %
                            (idx, BColors.RED, photo_id, BColors.RESET, title, owner, ispublic, isfriend, isfamily))

                    idx = idx+1

            if total == '0':
                print('Found no photo.')
            else:
                print('Found a total of %s photos.' % (total))

        except flickrapi.exceptions.FlickrError as ex:
            print(ex[0])


    #----------------------------------------------------------------------------------
    def get_photo_count(self, dates):
        '''
        Gets a list of photo counts for the given date ranges for the calling user.

        https://www.flickr.com/services/api/flickr.photos.getCounts.html
        '''

        print('')
        print('----------------------------------------------------------------------')
        print('Gets a list of photo counts for the given date ranges for the calling user.')

        try:
            if dates == None:
                dates = ''
            else:
                dates = time.mktime(datetime.strptime(max_taken_date, '%Y-%m-%d').timetuple())

        except flickrapi.exceptions.FlickrError as ex:
            print(ex[0])


    #----------------------------------------------------------------------------------
    def get_photo_info(self, flickr, photo_id, print_info=1):
        '''
        Get information about a photo. The calling user must have permission to view the photo.

        https://www.flickr.com/services/api/flickr.photos.getInfo.html
        '''

        if print_info:
            print('')
            print('----------------------------------------------------------------------')
            print('Get info for a given photo (id: %s)' % photo_id)

            print('---- PHOTO ---------------------------')

        try:
            photo = flickr.photos.getInfo(photo_id=photo_id)

            if self.debug == 1:
                from xml.etree import ElementTree as ET
                ET.dump(photo)

            attributes = photo.find('photo')

            dateuploaded = attributes.attrib['dateuploaded']

            license_id = attributes.attrib['license']

            title       = attributes.find('title').text
            description = attributes.find('description').text
            dates       = attributes.find('dates')
            lastupdate  = dates.attrib['lastupdate']
            posted      = dates.attrib['posted']
            taken       = dates.attrib['taken']

            self.get_permissions(flickr, photo_id)

            dateuploaded = datetime.fromtimestamp(int(dateuploaded)).strftime('%Y-%m-%d %H:%M:%S')
            lastupdate = datetime.fromtimestamp(int(lastupdate)).strftime('%Y-%m-%d %H:%M:%S')
            posted = datetime.fromtimestamp(int(posted)).strftime('%Y-%m-%d %H:%M:%S')

            if print_info:
                print('PHOTO ID: %s%s%s' % (BColors.RED, photo_id, BColors.RESET))
                print('TITLE: %s' % (title))
                print('DESCRIPTION: %s' % (description))
                print('LICENSE: %s (%s)' % (self.get_license(flickr, license_id), license_id))
                print('LAST UPDATED: %s' % (lastupdate))
                print('POSTED: %s' % (posted))
                print('TAKEN: %s' % (taken))
                print('IS PUBLIC: %s' % (self.is_public))
                print('IS FRIEND: %s' % (self.is_family))
                print('IS FAMILY: %s' % (self.is_family))

            try:
                tags = attributes.find('tags').findall('tag')

                if print_info:
                    print('--- TAGS')

                for itag in range(len(tags)):
                    tag_id = tags[itag].attrib['id']
                    author = tags[itag].attrib['author']
                    author_name = tags[itag].attrib['authorname']
                    #tag_name = tags[itag].attrib['raw']
                    tag_name = tags[itag].text

                    if print_info:
                        print('\t%d | TAG: %s | TAG ID: %s | AUTHOR NAME: %s | AUTHOR: %s' %
                                (itag, tag_name, tag_id, author_name, author))


                try:
                    notes = attributes.find('notes').findall('note')

                    if print_info:
                        print('--- NOTES')

                    for inote in range(len(notes)):
                        author  = notes[inote].attrib['author']
                        note_id = notes[inote].attrib['id']
                        note    = notes[inote].text

                        if print_info:
                            print('\t%d | AUTHOR: %s | ID: %s' % (inote, author, note_id, note))

                    try:
                        urls = attributes.find('urls').findall('url')

                        if print_info:
                            print('--- URLS')

                        for iurl in range(len(urls)):
                            url_type = urls[iurl].attrib['type']
                            url_link = urls[iurl].text

                            if print_info:
                                print('\t%d | TYPE: %s | URL: %s%s%s' % (iurl, url_type, BColors.BLUE, url_link, BColors.RESET))

                    except flickrapi.exceptions.FlickrError as ex:
                        print(ex[0])

                except flickrapi.exceptions.FlickrError as ex:
                    print(ex[0])

            except flickrapi.exceptions.FlickrError as ex:
                print(ex[0])

            self.get_photo_location(flickr, photo_id, 0)
            self.get_available_size_of_photo(flickr, photo_id)

        except flickrapi.exceptions.FlickrError as ex:
            print(ex[0])


    #----------------------------------------------------------------------------------
    def is_url_image(self, url):
        mimetype,encoding = mimetypes.guess_type(url)
        return (mimetype and mimetype.startswith('image'))


    def check_url(self, url):
        """
        Returns True if the url returns a response code between 200-300,
        otherwise return False.
        """
        try:
            headers={
                "Range": "bytes=0-10",
                "User-Agent": "MyTestAgent",
                "Accept":"*/*"
            }

            req = urllib2.Request(url, headers=headers)
            response = urllib2.urlopen(req)
            return response.code in range(200, 209)
        except Exception, ex:
            return False

    def is_image_and_ready(self, url):
        return self.is_url_image(url) and self.check_url(url)

    def show_image(self, photo_url):
        '''
        Shows an image on screen, either an image file or a valid url.
        '''

        try:
            if self.is_image_and_ready(photo_url):
                im = Image.open(urllib2.urlopen(photo_url))
            else:
                form = imghdr.what(photo_url)

                if form.lower() in ('jpg','jpeg','png','gif','pnm','ppn'):
                    im = Image.open(photo_url)

            im.show()
        except:
            print('URL %s is not an image!' % photo_url)



    #----------------------------------------------------------------------------------
    def set_photo_location(self, flickr, photo_id, lat, lon, accuracy, context):
        '''
        Sets the geo data (latitude and longitude and, optionally, the accuracy level)
        for a photo. Before users may assign location data to a photo they must define
        who, by default, may view that information. Users can edit this preference at
        http://www.flickr.com/account/geo/privacy/. If a user has not set this preference,
        the API method will return an error.

        www.flickr.com/services/api/flickr.photos.geo.setLocation.html
        '''

        try:
            flickr.photos.geo.setLocation(photo_id=photo_id, lat=lat, lon=lon, accuracy=accuracy, context=context)

        except flickrapi.exceptions.FlickrError as ex:
            print(ex[0])

        print('Photo location has been set.')


# <photo id='123'>
#   <location latitude='-17.685895' longitude='-63.36914' accuracy='6' />
# </photo>
    #----------------------------------------------------------------------------------
    def get_photo_location(self, flickr, photo_id, print_info=1):
        '''
        Get the geo data (latitude and longitude and the accuracy level) for a photo.

        www.flickr.com/services/api/flickr.photos.geo.getLocation.html
        '''

        if print_info:
            print('')
            print('----------------------------------------------------------------------')
            print('Get location for a given photo (id: %s)' % photo_id)

        try:
            photo = flickr.photos.geo.getLocation(photo_id=photo_id)

            if self.debug == 1:
                from xml.etree import ElementTree as ET
                ET.dump(photo)

            location = photo.find('photo').find('location')

            latitude  = location.attrib['latitude']
            longitude = location.attrib['longitude']
            accuracy  = location.attrib['accuracy']

            if not print_info:
                tab = '\t'
            else:
                tab = ''

            if int(accuracy) == 1:
                faccuracy = 'World'
            if int(accuracy) > 1:
                faccuracy = 'Country'
            if int(accuracy) > 3:
              faccuracy = 'Region'
            if int(accuracy) > 6:
              faccuracy = 'City'
            if int(accuracy) > 11:
                faccuracy = 'Street'

            print('--- LOCATION')
            print('\tLATITUDE: %s' % (latitude))
            print('\tLONGITUDE: %s' % (longitude))
            print('\tACCURACY: %s (%s)' % (faccuracy, accuracy))

        except flickrapi.exceptions.FlickrError as ex:
            print(ex[0])


    #----------------------------------------------------------------------------------
    def remove_photo_location(self, flickr, photo_id):
        '''
        Removes the geo data associated with a photo.

        www.flickr.com/services/api/flickr.photos.geo.removeLocation.html
        '''

        try:
            flickr.photos.geo.removeLocation(photo_id=photo_id)

        except flickrapi.exceptions.FlickrError as ex:
            print(ex[0])

        print('Photo location has been removed.')

    #----------------------------------------------------------------------------------
    def set_geo_permissions(self, flickr, is_public, is_contact, is_friend, is_family, photo_id):
        '''
        Set the permission for who may view the geo data associated with a photo.

        www.flickr.com/services/api/flickr.photos.geo.setPerms.html
        '''

        try:
            perms = flickr.photos.geo.setPerms(is_public=is_public, is_contact=is_contact, is_friend=is_friend, is_family=is_family, photo_id=photo_id)

            if self.debug == 1:
                from xml.etree import ElementTree as ET
                ET.dump(perms)

        except flickrapi.exceptions.FlickrError as ex:
            print(ex[0])


# <perms id='10592' ispublic='0' iscontact='0' isfriend='0' isfamily='1' />
    #----------------------------------------------------------------------------------
    def get_geo_permissions(self, flickr, photo_id, print_info=1):
        '''
        Get permissions for who may view geo data for a photo.

        www.flickr.com/services/api/flickr.photos.geo.getPerms.html
        '''

        try:
            perms = flickr.photos.geo.getPerms(photo_id=photo_id)

            if self.debug == 1:
                from xml.etree import ElementTree as ET
                ET.dump(perms)

            perm = perms.find('perms')

            self.is_public  = perm.attrib['ispublic']
            self.is_contact = perm.attrib['iscontact']
            self.is_friend  = perm.attrib['isfriend']
            self.is_family  = perm.attrib['isfamily']

            if print_info:
                print('--- GEO PERMISSIONS')
                print('\tIS PUBLIC: %s' % (self.is_public))
                print('\tIS CONTACT: %s' % (self.is_contact))
                print('\tIS FRIEND: %s' % (self.is_friend))
                print('\tIS FAMILY: %s' % (self.is_family))

        except flickrapi.exceptions.FlickrError as ex:
            print(ex[0])

        self.get_geo_permissions(flickr, photo_id)

    #----------------------------------------------------------------------------------
    def get_available_size_of_photo(self, flickr, photo_id):
        '''
        Returns the available sizes for a photo. The calling user must have permission to view the photo.

        https://www.flickr.com/services/api/flickr.photos.getSizes.html
        '''

        try:
            sizes = flickr.photos.getSizes(photo_id=photo_id)

            print('--- SIZES')

            if self.debug == 1:
                from xml.etree import ElementTree as ET
                ET.dump(sizes)

            attributes = sizes.find('sizes').findall('size')

            for idx in range(len(attributes)):
                a = attributes[idx]

                label  = a.attrib['label']
                height = a.attrib['height']
                width  = a.attrib['width']
                source = a.attrib['source']
                url    = a.attrib['url']
                media  = a.attrib['media']

                print('\t%d | MEDIA: %s | LABEL: %s | WIDTH: %s | HEIGHT: %s \n\t\tSOURCE: %s%s%s \n\t\tURL: %s%s%s' %
                        (idx, media, label, width, height, BColors.BLUE, source, BColors.RESET, BColors.BLUE, url, BColors.RESET))

        except flickrapi.exceptions.FlickrError as ex:
            print(ex[0])


#   <perms id='1234567788' ispublic='0' isfriend='0' isfamily='1' permcomment='1' permaddmeta='1' />
    #----------------------------------------------------------------------------------
    def get_permissions(self, flickr, photo_id):
        '''
        Get permissions for a photo.

        https://www.flickr.com/services/api/flickr.photos.getPerms.html
        '''

        try:
            perms = flickr.photos.getPerms(photo_id=photo_id).find('perms')

            self.is_public = perms.attrib['ispublic']
            self.is_friend = perms.attrib['isfriend']
            self.is_family = perms.attrib['isfamily']

        except flickrapi.exceptions.FlickrError as ex:
            print(ex[0])


    #----------------------------------------------------------------------------------
    def set_permissions(self, flickr, photo_id, is_public, is_friend, is_family):
        '''
        Set permissions for a photo.

        https://www.flickr.com/services/api/flickr.photos.setPerms.html
        '''

        if args.dry_run:
            print('\nDRY-RUN :: Set permissions (id: %s, is_public: %s, is_friend: %s, is_family: %s, )' % (photo_id, is_public, is_friend, is_family))
            return True

        print('----------------------------------------------------------------------')
        print('Set permissions (id: %s, is_public: %s, is_friend: %s, is_family: %s )' % (photo_id, is_public, is_friend, is_family))

        try:
            flickr.photos.setPerms(photo_id=photo_id, is_public=is_public, is_friend=is_friend, is_family=is_family)
        except flickrapi.exceptions.FlickrError as ex:
            print(ex[0])


    #----------------------------------------------------------------------------------
    def set_photo_metadata(self, flickr, photo_id, title, description):
        '''
        Set the meta information for a photo.

        https://www.flickr.com/services/api/flickr.photos.setMeta.html
        '''

        if args.dry_run:
            print('\nDRY-RUN :: Set meta (id: %s, title: %s, description: %s )' % (photo_id, title, description))
            return True

        print('----------------------------------------------------------------------')
        print('Set meta (id: %s, title: %s, description: %s)' % (photo_id, title, description))

        try:
            flickr.photos.setMeta(photo_id=photo_id, title=title, description=description)
        except flickrapi.exceptions.FlickrError as ex:
            print(ex[0])


    #----------------------------------------------------------------------------------
    def rotate_photo(self, flickr, photo_id, degrees):
        '''
        Rotate a photo.

        https://www.flickr.com/services/api/flickr.photos.transform.rotate.html
        '''

        if args.dry_run:
            print('\nDRY-RUN :: Rotate photo (id: %s, degrees: %s)' % (photo_id, degrees))
            return True

        print('----------------------------------------------------------------------')
        print('Rotate photo (id: %s, degrees: %s)' % (photo_id, degrees))

        try:
            flickr.photos.transform.rotate(photo_id=photo_id, degrees=degrees)
        except flickrapi.exceptions.FlickrError as ex:
            print(ex[0])


    #----------------------------------------------------------------------------------
    def set_primary_photo(self, flickr, photoset_id, photo_id):
        '''
        Set photoset primary photo.

        https://www.flickr.com/services/api/flickr.photosets.setPrimaryPhoto.html
        '''

        if args.dry_run:
            print('\nDRY-RUN :: Set primary photo (photoset id: %s, photo id: %s)' % (photoset_id, photo_id))
            return True

        print('----------------------------------------------------------------------')
        print('Set primary photo (photoset id: %s, photo id: %s)' % (photoset_id, photo_iddegrees))

        try:
            flickr.photosets.setPrimaryPhoto(photoset_id=photoset_id, photo_id=photo_id)
        except flickrapi.exceptions.FlickrError as ex:
            print(ex[0])


    #----------------------------------------------------------------------------------
    def get_galleries_list(self, flickr, user_id):
        '''
        Return the list of galleries created by a user. Sorted from newest to oldest.

        https://www.flickr.com/services/api/flickr.galleries.getList.html
        '''

        try:
            galleries = flickr.galleries.getList(user_id=user_id, per_page=500)

            if self.debug == 1:
                from xml.etree import ElementTree as ET
                ET.dump(galleries)

            pages = galleries.find('galleries').attrib['pages']
            total = galleries.find('galleries').attrib['total']

            print('Total number of galleries : %s (%s pages)' % (total, pages))

            idx = 0
            for ipage in range(1,int(pages)+1,1):
                galleries = flickr.galleries.getList(user_id=user_id, per_page=500, page=ipage)

                gallery = galleries.find('galleries').findall('gallery')

                for igal in range(len(gallery)):
                    a = gallery[igal]

                    gallery_id = a.attrib['id']
                    url = a.attrib['url']
                    owner = a.attrib['owner']
                    date_create = a.attrib['date_create']
                    date_update = a.attrib['date_update']
                    primary_photo_id = a.attrib['primary_photo_id']
                    count_photos = a.attrib['count_photos']
                    count_videos = a.attrib['count_videos']
                    title = a.find('title').text
                    description = a.find('description').text

                    date_create = datetime.fromtimestamp(int(date_create)).strftime('%Y-%m-%d')
                    date_update = datetime.fromtimestamp(int(date_update)).strftime('%Y-%m-%d')

                    print('%s :: GALLERY ID: %s%s%s | OWNER: %s | PRIMARY PHOTO ID; %s | CREATED: %s | UPLOADED: %s | PHOTOS: %s | VIDEOS: %s' %
                            (idx, BColors.RED, gallery_id, BColors.RESET, owner, primary_photo_id, date_create, date_update, count_photos, count_videos))
                    print('\tTITLE: %s' % title)
                    print('\tDESCRIPTION: %s' % description)
                    print('\tURL: %s%s%s' % (BColors.BLUE, url, BColors.RESET))

                    idx = idx+1

        except flickrapi.exceptions.FlickrError as ex:
            print(ex[0])


    #----------------------------------------------------------------------------------
    def get_gallery_info(self, flickr, gallery_id):
        '''
        Get gallery info.

        https://www.flickr.com/services/api/flickr.galleries.getInfo.html
        '''

        try:
            info = flickr.galleries.getInfo(gallery_id=gallery_id)

            gallery_id       = info.find('gallery').attrib['id']
            url              = info.find('gallery').attrib['url']
            owner            = info.find('gallery').attrib['owner']
            date_create      = info.find('gallery').attrib['date_create']
            date_update      = info.find('gallery').attrib['date_update']
            primary_photo_id = info.find('gallery').attrib['primary_photo_id']
            count_photos     = info.find('gallery').attrib['count_photos']
            count_videos     = info.find('gallery').attrib['count_videos']
            title            = info.find('gallery').find('title').text
            description      = info.find('gallery').find('description').text

            date_create = datetime.fromtimestamp(int(date_create)).strftime('%Y-%m-%d')
            date_update = datetime.fromtimestamp(int(date_update)).strftime('%Y-%m-%d')

            print('GALLERY ID: %s%s%s' % (BColors.RED, gallery_id, BColors.RESET))
            print('TITLE: %s' % title)
            print('DESCRIPTION: %s' % description)
            print('OWNER: %s' % (owner))
            print('PRIMARY PHOTO ID: %s' % (primary_photo_id))
            print('CREATED: %s' % (date_create))
            print('UPLOADED: %s' % (date_update))
            print('PHOTOS: %s' % (count_photos))
            print('VIDEOS: %s' % (count_videos))
            print('URL: %s%s%s' % (BColors.BLUE, url, BColors.RESET))

        except flickrapi.exceptions.FlickrError as ex:
            print(ex[0])


    #----------------------------------------------------------------------------------
    def get_gallery_photos(self, flickr, gallery_id):
        '''
        Return the list of photos for a gallery

        https://www.flickr.com/services/api/flickr.galleries.getPhotos.html
        '''

        try:
            photos = flickr.galleries.getPhotos(gallery_id=gallery_id, per_page=500)

            if self.debug == 1:
                from xml.etree import ElementTree as ET
                ET.dump(galleries)

            pages = photos.find('photos').attrib['pages']
            total = photos.find('photos').attrib['total']

            print('Total number of photos : %s (%s pages)' % (total, pages))

            idx = 0
            for ipage in range(1,int(pages)+1,1):
                photos = flickr.galleries.getPhotos(gallery_id=gallery_id, per_page=500, page=ipage)

                photo = photos.find('photos').findall('photo')

                for iphoto in range(len(photo)):
                    a = photo[iphoto]

                    photo_id = a.attrib['id']
                    owner = a.attrib['owner']
                    title = a.attrib['title']
                    ispublic = a.attrib['ispublic']
                    isfriend = a.attrib['isfriend']
                    isfamily = a.attrib['isfamily']

                    print('%d :: PHOTO ID: %s%s%s | TITLE: %s | OWNER: %s | IS PUBLIC: %s | IS FRIEND: %s | IS FAMILY: %s' %
                            (idx, BColors.RED, photo_id, BColors.RESET, title, owner, ispublic, isfriend, isfamily))

                    idx = idx+1

        except flickrapi.exceptions.FlickrError as ex:
            print(ex[0])


    ##
    # Get the list of files to synchronize with Flickr.
    # @param folder     Path to the main folder
    # @return A tuple (photos_to_sync, photosets_to_create) where photos_to_sync
    #  is the list of files to synchronize for each subfolder, and
    #  photoset_ids is the list of albums with their respective id on Flickr,
    #  or None if the album does not exist yet.
    #
    #----------------------------------------------------------------------------------
    def synclist(self, user_id, folder):

        print 'Getting the list of pictures to synchronize...'

        subfolders = [lfile for lfile in os.listdir(unicode(folder))
                      if os.path.isdir(os.path.join(folder, lfile))
                      and re.match(SUBFOLDERS_REGEXP, lfile)]

        print subfolders, os.path.isdir(os.path.join(folder, lfile)), os.listdir(unicode(folder))

        photosets = self.flickr.photosets_getList(user_id=user_id)
        photos_to_sync = {}
        photoset_ids = {}

        for subfolder in subfolders:
            subfolder = subfolder.encode('UTF-8')
            # Check if the album already exists on Flickr
            photoset_id = None

            for photoset in photosets.find('photosets').findall('photoset'):
                photoset_title = photoset.find('title').text

                if type(photoset_title) == unicode:
                    photoset_title = photoset_title.encode('UTF-8')

                if photoset_title == subfolder:
                    photoset_id = str(photoset.attrib['id'])
                    break

            photoset_ids[subfolder] = photoset_id

            # Get the list of pictures to synchronize within this album
            photos_to_sync[subfolder] = self.synclist_subfolder(os.path.join(folder, subfolder), photoset_id)

        return photos_to_sync, photoset_ids


    ##
    # Get the list of pictures to synchronize within an album.
    # @param subfolder     Complete path to the subfolder to synchronize
    # @param photoset_id   Id of the album on Flickr, or None of the album does not exist yet
    # @return The list of the pictures to synchronize.
    #
    #----------------------------------------------------------------------------------
    def synclist_subfolder(self, subfolder, photoset_id=None):
        files = [lfile for lfile in os.listdir(unicode(subfolder))
                 if lfile.endswith(PICTURE_EXTENSIONS)]
        files_to_sync = []
        if photoset_id is not None:
            # Find which file were not uploaded
            photoset = list(self.flickr.walk_set(photoset_id))
            for lfile in files:
                lfile = lfile.encode('UTF-8')
                found = False
                for photo in photoset:
                    photo = photo.get('title')
                    if type(photo) == unicode:
                        photo = photo.encode('UTF-8')
                    if photo == lfile:
                        found = True
                        break
                if not found:
                    files_to_sync.append(lfile)
        else:
            for lfile in files:
                files_to_sync.append(lfile)
        return files_to_sync


    #----------------------------------------------------------------------------------
    def upload_folder(self, photos_to_sync, tags, is_public, is_friend, is_family, folder, photosets={}):
        '''
        '''

        print('')
        print('----------------------------------------------------------------------')
        print('Upload photos from folder %s' % folder)

        con = lite.connect(DB_PATH)
        con.text_factory = str
        cur = con.cursor()

        for subfolder in sorted(photos_to_sync):
            count = 1
            total = len(photos_to_sync[subfolder])
            len_count = len(str(total))
            consecutive_errors = 0

            print('Folder with sub-folders is %s' % folder)
            print('Album %s: %s photos to synchronize' % (subfolder, total))

            for photo in sorted(photos_to_sync[subfolder]):
                print '%-*s/%s\t %s' % (len_count, count, total, photo)

                nb_errors = 0
                done = False
                while nb_errors < MAX_RETRIES and not done:
                    try:
                        path = os.path.join(folder, subfolder, photo).encode('UTF-8')
                        photo = photo.encode('UTF-8')

                        file_checksum = self.md5_checksum(path)
                        _tags = '%s md5-%s' % (tags, file_checksum)

                        response = self.flickr.upload(filename=path,
                                                      title=photo,
                                                      tags=_tags,
                                                      is_public=is_public,
                                                      is_family=is_family,
                                                      is_friend=is_friend)

                    except KeyboardInterrupt:
                        print('Exit by user request')
                        return
                    except:
                        nb_errors += 1
                        consecutive_errors += 1
                        if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                            print('%s failed uploads in a row, aborting.' % MAX_CONSECUTIVE_ERRORS)
                            return
                        else:
                            print('Error, retrying upload (%s/%s)' % (nb_errors, MAX_RETRIES))
                    else:
                        if self.debug == 1:
                            from xml.etree import ElementTree as ET
                            ET.dump(response)

                        photo_id = response.find('photoid').text
                        done = True
                        count += 1
                        consecutive_errors = 0

                        # Create photoset.
                        if photoset_ids[subfolder] is None:
                            print('Creating the remote album %s' % subfolder)
                            response = self.flickr.photosets_create(title=subfolder, primary_photo_id=photo_id)
                            photoset_ids[subfolder] = response.find('photoset').attrib['id']

                            print('Created a photoset (id: %s%s%s) with primary photo (id: %s%s%s)' %
                                    (BColors.RED, photoset_ids[subfolder], BColors.RESET, BColors.BLUE, photo_id, BColors.RESET))

                            cur.execute("INSERT INTO sets (set_id, name, primary_photo_id) VALUES (?,?,?)",
                                        (photoset_ids[subfolder], subfolder, photo_id))
                            cur.execute("UPDATE files SET set_id = ? WHERE files_id = ?", (photoset_ids[subfolder], photo_id))
                            con.commit()

                        # Add photo to photoset.
                        else:
                            self.flickr.photosets.addPhoto(photoset_id=photoset_ids[subfolder], photo_id=photo_id)

                            print('Added photo (id: %s%s%s) to photoset (id: %s%s%s)' % 
                                    (BColors.BLUE, photo_id, BColors.RESET, BColors.RED, photoset_ids[subfolder], BColors.RESET))

                        # Add photo to database.
                        last_modified = os.stat(path).st_mtime;
                        cur.execute('INSERT INTO files (files_id, set_id, path, md5, last_modified, tagged) VALUES (?, ?, ?, ?, ?, 1)',
                                    (photo_id, photoset_ids[subfolder], path, file_checksum, last_modified))
                        con.commit()

                if nb_errors == 3:
                    print('%s failed to upload' % photo)


    #----------------------------------------------------------------------------------
    def upload_photo(self, flickr, filename, title, description, tags, is_public, is_friend, is_family):
        """
        Upload a file to flickr.

        Be extra careful you spell the parameters correctly, or you will
        get a rather cryptic 'Invalid Signature' error on the upload!

        Supported parameters:

        filename
            name of a file to upload
        fileobj
            an optional file-like object from which the data can be read
        title
            title of the photo
        description
            description a.k.a. caption of the photo
        tags
            space-delimited list of tags, ``'''tag1 tag2 "long tag"'''``
        is_public
            '1' or '0' for a public resp. private photo
        is_friend
            '1' or '0' whether friends can see the photo while it's
            marked as private
        is_family
            '1' or '0' whether family can see the photo while it's
            marked as private
        content_type
            Set to '1' for Photo, '2' for Screenshot, or '3' for Other.
        hidden
            Set to '1' to keep the photo in global search results, '2'
            to hide from public searches.
        format
            The response format. You can only choose between the
            parsed responses or 'rest' for plain REST.
        timeout
            Optional timeout for the HTTP request, as float in seconds.

        The ``fileobj`` parameter can be used to monitor progress via
        a callback method. For example::

            class FileWithCallback(object):
                def __init__(self, filename, callback):
                    self.file = open(filename, 'rb')
                    self.callback = callback
                    # the following attributes and methods are required
                    self.len = os.path.getsize(path)
                    self.fileno = self.file.fileno
                    self.tell = self.file.tell

                def read(self, size):
                    if self.callback:
                        self.callback(self.tell() * 100 // self.len)
                    return self.file.read(size)

            fileobj = FileWithCallback(filename, callback)
            rsp = flickr.upload(filename, fileobj, parameters)

        The callback method takes one parameter:
        ``def callback(progress)``

        Progress is a number between 0 and 100.
        """

        if args.dry_run:
            print('\nDRY-RUN :: Upload a photo')
            return True

        print('')
        print('----------------------------------------------------------------------')
        print('Upload photo %s.' % (filename))

        con = lite.connect(DB_PATH)
        con.text_factory = str
        cur = con.cursor()

        # Uploading file
        try:
            file_checksum = self.md5_checksum(filename)
            _tags = '%s md5-%s' % (tags, file_checksum)

            uploaded = flickr.upload(filename=filename,
                                     title=title,
                                     description=description,
                                     tags=_tags,
                                     is_public=is_public,
                                     is_family=is_family,
                                     is_friend=is_friend)

            if self.debug == 1:
                from xml.etree import ElementTree as ET
                ET.dump(uploaded)

            photo_id = uploaded.find('photoid').text

            print('Photo (id: %s%s%s) has been uploaded.' % (BColors.RED, photo_id, BColors.RESET))

            # Add photo to database.
            last_modified = os.stat(filename).st_mtime;
            cur.execute('INSERT INTO files (files_id, path, md5, last_modified, tagged) VALUES (?, ?, ?, ?, ?)',
                        (photo_id, filename, file_checksum, last_modified, _tags))
            con.commit()

        except flickrapi.exceptions.FlickrError as ex:
            print(ex[0])


    #----------------------------------------------------------------------------------
    def add_photo_to_photoset(self, flickr, photoset_id, photo_id):
        '''
        Add a photo to the end of an existing photoset.

        https://www.flickr.com/services/api/flickr.photosets.addPhoto.html
        '''

        print('')
        print('----------------------------------------------------------------------')
        print('Add photo %s to photoset %s.' % (photo_id, photoset_id))

        con = lite.connect(DB_PATH)
        con.text_factory = str
        cur = con.cursor()

        try:
            photo = flickr.photosets.addPhoto(photoset_id=photoset_id, photo_id=photo_id)

            if self.debug == 1:
                from xml.etree import ElementTree as ET
                ET.dump(photo)

            cur.execute("UPDATE files SET set_id = ? WHERE files_id = ?", (photoset_id, photo_id))
            con.commit()

        except flickrapi.exceptions.FlickrError as ex:
            print(ex[0])


    #----------------------------------------------------------------------------------
    #def remove_photo_from_photoset(self, flickr, nphotos, photoset_id, photo_id):
    def remove_photo_from_photoset(self, flickr, photoset_id, photo_id):
        '''
        Add a photo to the end of an existing photoset.

        https://www.flickr.com/services/api/flickr.photosets.removePhoto.html
        https://www.flickr.com/services/api/flickr.photosets.removePhotos.html
        '''

        print('')
        print('----------------------------------------------------------------------')
        print('Remove photo %s from photoset %s.' % (photo_id, photoset_id))

        con = lite.connect(DB_PATH)
        con.text_factory = str
        cur = con.cursor()

        try:
            #if nphotos > 1:
            #    photo = flickr.photosets.removePhotos(photoset_id=photoset_id, photo_ids=photo_id)
            #else:
            photo = flickr.photosets.removePhoto(photoset_id=photoset_id, photo_id=photo_id)

            if self.debug == 1:
                from xml.etree import ElementTree as ET
                ET.dump(photo)

            # Find out if the file is the last item in a set, if so, remove the set from the local db
            cur.execute("SELECT set_id FROM files WHERE files_id = ?", (photo_id,))
            row = cur.fetchone()
            cur.execute("SELECT set_id FROM files WHERE set_id = ?", (row[0],))
            rows = cur.fetchall()
            if (len(rows) == 1):
                print("File is the last of the set, deleting the set ID: " + str(row[0]))
                cur.execute("DELETE FROM sets WHERE set_id = ?", (row[0],))

            # Update the database.
            cur.execute("UPDATE files SET set_id = ? WHERE files_id = ?", ('NULL', photo_id))
            con.commit()

        except flickrapi.exceptions.FlickrError as ex:
            print(ex[0])


    #----------------------------------------------------------------------------------
    def get_recent_photos(self, flickr, min_date):
        '''
        Return a list of your photos that have been recently created or which have been recently modified.

        Recently modified may mean that the photo's metadata (title, description, tags)
        may have been changed or a comment has been added (or just modified somehow :-)

        https://www.flickr.com/services/api/flickr.photos.recentlyUpdated.html
        '''

        print('')
        print('----------------------------------------------------------------------')
        print('Recently updated photos (after %s).' % (min_date))

        try:
            recent = flickr.photos.recentlyUpdated(min_date=min_date, per_page=500)

            if self.debug == 1:
                from xml.etree import ElementTree as ET
                ET.dump(recent)

            pages = recent.find('photos').attrib['pages']
            total = recent.find('photos').attrib['total']

            print('Total number of photos : %s (%s pages)' % (total, pages))

            idx = 0
            for ipage in range(1,int(pages)+1,1):
                recent = flickr.photos.recentlyUpdated(min_date=min_date, per_page=500, page=ipage)

                photo = recent.find('photos').findall('photo')

                for iphoto in range(len(photo)):
                    a = photo[iphoto]

                    photo_id  = a.attrib['id']
                    owner     = a.attrib['owner']
                    title     = a.attrib['title']
                    ispublic  = a.attrib['ispublic']
                    isfriend  = a.attrib['isfriend']
                    isfamily  = a.attrib['isfamily']

                    print('%d :: PHOTO ID: %s%s%s | TITLE: %s | OWNER: %s | IS PUBLIC: %s | IS FRIEND: %s | IS FAMILY: %s' %
                            (idx, BColors.RED, photo_id, BColors.RESET, title, owner, ispublic, isfriend, isfamily))

                    idx = idx+1

        except flickrapi.exceptions.FlickrError as ex:
            print(ex[0])


    #----------------------------------------------------------------------------------
    def delete_photo(self, flickr, photo_id):
        '''
        Delete a photo from flickr.

        https://www.flickr.com/services/api/flickr.photos.delete.html
        '''

        if args.dry_run:
            print('\nDRY-RUN :: delete a photo (id: %s)' % photo_id)
            return True

        # Connect to database.
        con = lite.connect(DB_PATH)
        con.text_factory = str
        cur = con.cursor()

        print('')
        print('----------------------------------------------------------------------')
        print('Deleting photo (id: %s).' % photo_id)

        ans = raw_input('Do you really want to delete this photo? (y/n) ')

        if ans not in ('y', 'Y', 'yes', 'Yes', 'YES'):
            print('Photo not deleted.')
            return False

        try:
            delete = flickr.photos.delete(photo_id=photo_id)

            # Let's check if a record for the photo exists in the database.
            cur.execute("SELECT files_id FROM files WHERE files_id = ?", (photo_id,))
            row = cur.fetchone()

            if not row == None:
                # Find out if the file is the last item in a set, if so, remove the set from the local db
                cur.execute("SELECT set_id FROM files WHERE files_id = ?", (photo_id,))
                row = cur.fetchone()

                cur.execute("SELECT set_id FROM files WHERE set_id = ?", (row[0],))
                rows = cur.fetchall()

                # Deleting photoset from database.
                if (len(rows) == 1):
                    print("File is the last of the set, deleting the set ID: " + str(row[0]))
                    cur.execute("DELETE FROM sets WHERE set_id = ?", (row[0],))

                # Delete file record from the local database.
                cur.execute("DELETE FROM files WHERE files_id = ?", (photo_id,))
                con.commit()
            else:
                print('No record found in the database for photo (id %s).' % photo_id)

            print('Photo deleted.')

        except flickrapi.exceptions.FlickrError as ex:
            print(ex[0])


    #----------------------------------------------------------------------------------
    def set_tags(self, flickr, photo_id, tags):
        '''
        Set the tags for a photo.

        https://www.flickr.com/services/api/flickr.photos.setTags.html
        '''

        if args.dry_run:
            print('\nDRY-RUN :: Set tags (id: %s, tags: %s)' % (photo_id, tags))
            return True

        print('----------------------------------------------------------------------')
        print('Set tags (id: %s, tags: %s)' % (photo_id, tags))

        try:
            flickr.photos.setTags(photo_id=photo_id, tags=tags)
        except flickrapi.exceptions.FlickrError as ex:
            print(ex[0])


    #----------------------------------------------------------------------------------
    def remove_tag(self, flickr, tag_id):
        '''
        Remove a tag from a photo.

        https://www.flickr.com/services/api/flickr.photos.removeTag.html
        '''

        if args.dry_run:
            print('\nDRY-RUN :: Remove tag (tag id: %s)' % (tag_id))
            return True

        print('----------------------------------------------------------------------')
        print('Remove tag (tag id: %s)' % (tag_id))

        ans = raw_input('Do you really want to remove this tag? (y/n)')

        if ans not in ('y', 'Y', 'yes', 'Yes', 'YES'):
            print('Tag not deleted.')
            return False

        try:
            remove_tag = flickr.photos.removeTag(tag_id=tag_id)

            if self.debug == 1:
                from xml.etree import ElementTree as ET
                ET.dump(remove_tag)

        except flickrapi.exceptions.FlickrError as ex:
            print(ex[0])


    #----------------------------------------------------------------------------------
    def get_user_groups(self, flickr, user_id):
        '''
        Returns the list of groups a user is a member of.

        https://www.flickr.com/services/api/flickr.people.getGroups.html
        '''

        print('----------------------------------------------------------------------')

        try:
            groups = flickr.people.getGroups(user_id=user_id)

            if self.debug == 1:
                from xml.etree import ElementTree as ET
                ET.dump(groups)

            group = groups.find('groups').findall('group')
            print('List groups a user is member of (%s groups)' % (len(group)))

            for igroup in range(len(group)):
                a = group[igroup]

                # PROBLEM: uid 38954353@N06
                # <group admin="0" eighteenplus="0" iconfarm="6" iconserver="5289" invitation_only="0" members="8657" name="BBC Winterwatch" nsid="1603025@N22" pool_count="173484" topic_count="213" />
                admin = a.attrib['admin']
                is_admin = 'N/A'
                is_member = 'N/A'
                is_moderator = 'N/A'
                if 'is_admin' in a.attrib:
                    is_admin = a.attrib['is_admin']
                if 'is_member' in a.attrib:
                    is_member = a.attrib['is_member']
                if 'is_moderator' in a.attrib:
                    is_moderator = a.attrib['is_moderator']
                members = a.attrib['members']
                name = a.attrib['name']
                nsid = a.attrib['nsid']
                pool_count = a.attrib['pool_count']
                topic_count = a.attrib['topic_count']

                print('%d :: NAME: %s | NSID: %s | IS ADMIN: %s | IS MEMBER: %s | MEMBERS: %s | POOL COUNT: %s | TOPIC COUNT: %s' %
                        (igroup, name, nsid, is_admin, is_member, members, pool_count, topic_count))

        except flickrapi.exceptions.FlickrError as ex:
            print(ex[0])


    #----------------------------------------------------------------------------------
    def get_group_member_list(self, flickr, group_id):
        '''
        '''

        try:
            members = flickr.groups.members.getList(group_id=group_id, per_page=500)

            if self.debug == 1:
                from xml.etree import ElementTree as ET
                ET.dump(members)

            pages = members.find('members').attrib['pages']
            total = members.find('members').attrib['total']

            print('Total number of members : %s (%s pages)' % (total, pages))

            idx = 0
            for ipage in range(1,int(pages)+1,1):
                members = flickr.groups.members.getList(group_id=group_id, per_page=500, page=ipage)

                member = members.find('members').findall('member')

                for imember in range(len(member)):
                    a = member[imember]

                    nsid = a.attrib['nsid']
                    membertype = a.attrib['membertype']
                    username = a.attrib['username']

                    if membertype == '2':
                        membertype = 'member'
                    if membertype == '3':
                        membertype = 'moderator'
                    if membertype == '4':
                        membertype = 'admin'

                    print('%d :: MEMBER ID: %s%s%s | USERNAME: %s | MEMBER TYPE: %s' %
                            (idx, BColors.RED, nsid, BColors.RESET, username, membertype))

                    idx = idx+1

        except flickrapi.exceptions.FlickrError as ex:
            print(ex[0])


    #----------------------------------------------------------------------------------
    def get_exif_data(self, flickr, photo_id):
        '''
        Retrieves a list of EXIF/TIFF/GPS tags for a given photo.
        The calling user must have permission to view the photo.

        https://www.flickr.com/services/api/flickr.photos.getExif.html
        '''

        print('')
        print('----------------------------------------------------------------------')

        try:
            exifs = flickr.photos.getExif(photo_id=photo_id)

            if self.debug == 1:
                from xml.etree import ElementTree as ET
                ET.dump(exifs)

            camera = exifs.find('photo').attrib['camera']
            print('CAMERA: %s' % camera)

            exif = exifs.find('photo').findall('exif')

            for iexif in range(len(exif)):
                a = exif[iexif]

                make = a.attrib['label']
                model = a.find('raw').text

                print('%s | %s' % (make, model))

        except flickrapi.exceptions.FlickrError as ex:
            print(ex[0])


    #----------------------------------------------------------------------------------
    def get_license(self, flickr, license_id):
        '''
        Fetches a list of available photo licenses for Flickr.

        https://www.flickr.com/services/api/flickr.photos.licenses.getInfo.html
        '''

        lid = int(license_id)

        try:
            licenses = flickr.photos.licenses.getInfo()

            license = licenses.find('licenses').findall('license')[lid]
            name = license.attrib['name']

            return name

        except flickrapi.exceptions.FlickrError as ex:
            print(ex[0])


    #----------------------------------------------------------------------------------
    def get_licenses_info(self, flickr):
        '''
        Fetches a list of available photo licenses for Flickr.

        option --get-license-info or -gli .

        https://www.flickr.com/services/api/flickr.photos.licenses.getInfo.html
        '''

        print('')
        print('----------------------------------------------------------------------')

        try:
            licenses = flickr.photos.licenses.getInfo()

            if self.debug == 1:
                from xml.etree import ElementTree as ET
                ET.dump(licenses)

            license = licenses.find('licenses').findall('license')
            print('List available licenses (%s licenses)' % (len(license)))

            for ilicense in range(len(license)):
                a = license[ilicense]

                id = a.attrib['id']
                name = a.attrib['name']
                url = a.attrib['url']

                print('%s :: NAME: %s | URL: %s%s%s' % (id, name, BColors.BLUE, url, BColors.RESET))

        except flickrapi.exceptions.FlickrError as ex:
            print(ex[0])

    #----------------------------------------------------------------------------------
    def get_camera_brands(self, flickr):
        '''
        Returns all the brands of cameras that Flickr knows about.

        option --get-camera-brands or -gcb
        
        www.flickr.com/services/api/flickr.cameras.getBrands.html
        '''

        print('')
        print('----------------------------------------------------------------------')

        try:
            brands = flickr.cameras.getBrands()

            if self.debug == 1:
                from xml.etree import ElementTree as ET
                ET.dump(brands)

            brand = brands.find('brands').findall('brand')
            print('List available brands (%s brands)' % (len(brand)))

            lst = []

            for ibrand in range(len(brand)):
                a = brand[ibrand]

                name = a.attrib['name']

                lst.append(name)


            lst.sort()

            idx = 0
            for ibrand in range(len(brand)):
                print('%s :: BRAND: %s' % (idx, lst[idx]))

                idx = idx+1

        except flickrapi.exceptions.FlickrError as ex:
            print(ex[0])

    #----------------------------------------------------------------------------------
    def get_camera_brand_models(self, flickr, brand):
        '''
        Retrieve all the models for a given camera brand.

        option --get-camera-brand-model or -gcm
        
        www.flickr.com/services/api/flickr.cameras.getBrandModels.html

        <camera id="dsc-w270">
		<name>Sony DSC-W270</name>
		<details>
			<megapixels>12.1</megapixels>
			<lcd_screen_size>2.7</lcd_screen_size>
			<memory_type>Memory Stick PRO-HG Duo, Memory Stick Duo, Memory Stick PRO Duo</memory_type>
		</details>
		<images>
			<small>https://farm4.staticflickr.com/3459/cameras/72157615637709753_model_small_c88941f2c6.jpg</small>
			<large>https://farm4.staticflickr.com/3459/cameras/72157615637709753_model_large_0e137596d9.jpg</large>
		</images>
	</camera>

       	<camera id="galaxy-s5">
		<name>Galaxy S5</name>
		<images>
			<small>https://farm9.staticflickr.com/8415/cameras/72157640364800414_model_small_2c02bd240d.jpg</small>
			<large>https://farm9.staticflickr.com/8415/cameras/72157640364800414_model_large_97c092b00d.jpg</large>
		</images>
	</camera>


        '''

        print('')
        print('----------------------------------------------------------------------')

        try:
            models = flickr.cameras.getBrandModels(brand=brand)

            if self.debug == 1:
                from xml.etree import ElementTree as ET
                ET.dump(models)

            model = models.find('cameras').findall('camera')
            print('List available models (%s models)' % (len(model)))

            idx = 0
            for imodel in range(len(model)):
                a = model[imodel]

                model_id  = a.attrib['id']
                name = a.find('name').text

                print('%d :: CAMERA ID: %s | NAME: %s' % (idx, model_id, name))

                details = a.find('details')

                if not details == None:
                    megapixels = details.find('megapixels')
                    if not megapixels == None:
                        megapixels = megapixels.text

                    lcd_screen_size = details.find('lcd_screen_size')
                    if not lcd_screen_size == None:
                        lcd_screen_size = lcd_screen_size.text

                    memory_type = details.find('memory_type')
                    if not memory_type == None:
                        memory_type = memory_type.text


                    if megapixels == None:
                        print('\tMEGAPIXELS: N/A')
                    else:
                        print('\tMEGAPIXELS: %s' % megapixels)

                    if lcd_screen_size == None:
                        print('\tLCD SCREEN SIZE: N/A')
                    else:
                        print('\tLCD SCREEN SIZE: %s' % lcd_screen_size)

                    if memory_type == None:
                        print('\tMEMORY TYPE: N/A')
                    else:
                        print('\tMEMORY TYPE: %s' % memory_type)

                images = a.find('images')
                if not images == None:
                    small = images.find('small')
                    if not small == None:
                        small = small.text
                    large = images.find('large')
                    if not large == None:
                        large = large.text

                    if small == None:
                        print('\tSMALL IMAGE: N/A')
                    else:
                        print('\tSMALL IMAGE: %s' % small)

                    if large == None:
                        print('\tLARGE IMAGE: N/A')
                    else:
                        print('\tLARGE IMAGE: %s' % large)


                idx = idx+1


        except flickrapi.exceptions.FlickrError as ex:
            print(ex[0])

    #----------------------------------------------------------------------------------
    def set_license(self, flickr, photo_id, license_id):
        '''
        Sets the license for a photo.

        https://www.flickr.com/services/api/flickr.photos.licenses.setLicense.html
        '''

        print('')
        print('----------------------------------------------------------------------')

        try:
            licenses = flickr.photos.licenses.setLicense(photo_id=photo_id, license_id=license_id)
        except flickrapi.exceptions.FlickrError as ex:
            print(ex[0])


    #----------------------------------------------------------------------------------
    def search_photos(self, flickr, page, print_on_screen, **kwargs):

        print('Search criteria:')
        for key in kwargs:
            if not kwargs[key] == None:
                print "\t%s: %s" % (key, kwargs[key])
                if key == 'per_page':
                    per_page = kwargs[key]

        try:
            search = flickr.photos.search(**kwargs)

            if self.debug == 1:
                from xml.etree import ElementTree as ET
                ET.dump(search)

            pages = search.find('photos').attrib['pages']
            total = search.find('photos').attrib['total']

            print('Total number of photos (or videos) : %s (%s pages, %s per page)' % (total, pages, per_page))

            if print_on_screen:

                if page == None:
                    s_page = 1
                    e_page = int(pages)+1
                    idx = 0
                else:
                    s_page = int(page)
                    e_page = int(page)+1
                    idx = ((s_page-1) * int(per_page))

                for ipage in range(s_page,e_page,1):
                    search = flickr.photos.search(page=ipage, **kwargs)

                    photo = search.find('photos').findall('photo')

                    for iphoto in range(len(photo)):
                        a = photo[iphoto]

                        photo_id  = a.attrib['id']
                        owner     = a.attrib['owner']
                        title     = a.attrib['title']
                        ispublic  = a.attrib['ispublic']
                        isfriend  = a.attrib['isfriend']
                        isfamily  = a.attrib['isfamily']

                        print('%d :: PHOTO ID: %s%s%s | TITLE: %s | OWNER: %s | IS PUBLIC: %s | IS FRIEND: %s | IS FAMILY: %s' %
                                (idx, BColors.RED, photo_id.encode('utf-8'), BColors.RESET, title.encode('utf-8'), owner.encode('utf-8'),
                                    ispublic.encode('utf-8'), isfriend.encode('utf-8'), isfamily.encode('utf-8')))

                        idx = idx+1

        except flickrapi.exceptions.FlickrError as ex:
            print(ex[0])


    #----------------------------------------------------------------------------------
    def md5_checksum(self, filePath):
        with open(filePath, 'rb') as fh:
            m = hashlib.md5()
            while True:
                data = fh.read(8192)
                if not data:
                    break
                m.update(data)
            return m.hexdigest()

    #----------------------------------------------------------------------------------
    def setup_database(self):

        print('')
        print('----------------------------------------------------------------------')
        print("Setting up the database: " + DB_PATH)

        con = None

        try:
            con = lite.connect(DB_PATH)
            con.text_factory = str
            cur = con.cursor()
            cur.execute('CREATE TABLE IF NOT EXISTS files (files_id INT, path TEXT, set_id INT, md5 TEXT, tagged INT)')
            cur.execute('CREATE TABLE IF NOT EXISTS sets (set_id INT, name TEXT, primary_photo_id INTEGER)')
            cur.execute('CREATE UNIQUE INDEX IF NOT EXISTS fileindex ON files (path)')
            cur.execute('CREATE INDEX IF NOT EXISTS setsindex ON sets (name)')
            con.commit()
            cur = con.cursor()
            cur.execute('PRAGMA user_version')
            row = cur.fetchone()
            if (row[0] == 0):
                print('Adding last_modified column to database');
                cur = con.cursor()
                cur.execute('PRAGMA user_version="1"')
                cur.execute('ALTER TABLE files ADD COLUMN last_modified REAL');
                con.commit()
            con.close()
        except lite.Error, e:
            print("Error: %s" % e.args[0])
            if con != None:
                con.close()
            sys.exit(1)
        finally:
            print("Completed database setup")


def compile_script():
    import py_compile
    py_compile.compile(sys.argv[0])
    print('Script %s compiled!' % sys.argv[0])
    sys.exit()


    #----------------------------------------------------------------------------------
def argument_parser():
    # Parse arguments.

    _description = '''
{0}NAME{1}
    {2}

{0}DESCRIPTION{1}
    Uploads a photo or folders containing photos to Flickr.
    Deletes photos from Flickr.
    Manipulates photos on Flickr.

{0}SYNOPSIS{1}
'''

    _epilog = '''
{0}EXAMPLES{1}
    You can store your user id (or nsid) in your config.ini file.

    To find your nsid (or user id) using your contact email address:
        {2} --find-userid-by-email your.email.address@gmail.com

    To find your nsid (or user id) using your username:
        {2} --find-userid-by-username your_username

    To get your info:
        {2} --get-user-info

    To get someone else's info:
        {2} --get-user-info --user-id XXXXXXXX@N00

    To upload a photo with a title, a description and tags:
        {2} --upload --filename ./path/to/photo.png --title 'The title' --description 'The description' --tags \'\'\'tag1 tag2 "long tag"\'\'\'

    To upload photos contained in sub-folder:
    Photos are located in ./path/to/folder/subfolder.
    Photos will be uploaded on Flickr and put in a photoset named after the sub-folder's name.
        {2} --upload-folder --folder ./path/to/folder

    To get a list of photosets:
        {2} --list-photosets
        0 :: TITLE: My beautiful pictures | DESCRIPTION: Pictures I have taken | PHOTOS: 431 | VIDEOS: 0 | CREATED: 2015-01-05 | PHOTOSET ID: {0}12345678901234567{1}

    To get a list of photos in a given photoset:
        {2} --list-photos --photoset-id {0}12345678901234567{1}
        0 :: PHOTO ID: {0}1234567890{1} | TITLE: My picture | IS PUBLIC: 1 | IS FRIEND: 0 | IS FAMILY: 0

    To list photos not in any set:
        {2} --list-photos-not-in-set
        Total number of photos : 335 (1 pages)
        0 :: PHOTO ID: {0}98765432{1} | TITLE: A picture | OWNER: 12345678@N00 | IS PUBLIC: 0 | IS FRIEND: 0 | IS FAMILY: 0
        1 :: PHOTO ID: {0}98674532{1} | TITLE: A picture | OWNER: 12345678@N00 | IS PUBLIC: 0 | IS FRIEND: 0 | IS FAMILY: 0

    To list recently updated photos:
        {2} --recently-updated --min-date {0}2017-03-27{1}

    To get info of a photo:
        {2} --get-photo-info --photo-id {0}1234567890{1}

    To delete a photo from Flickr:
        {2} --delete --photo-id {0}1234567890{1}

{0}AUTHOR{1}
    Fujisan, 2017
'''
    _parser = argparse.ArgumentParser(
            description=_description.format(BColors.BOLD, BColors.RESET, os.path.basename(__file__)),
            epilog = _epilog.format(BColors.BOLD, BColors.RESET, os.path.basename(__file__)),
            formatter_class=argparse.RawTextHelpFormatter)

    _parser.add_argument('-c',   '--compile-script',             action='store_true', help='Compile this python script.')
    _parser.add_argument('-p',   '--print-on-screen',            action='store_true', help='Print on screen.')
    _parser.add_argument('-dbg', '--debug',                      action='store_true', help='Debug.')
    _parser.add_argument('-v',   '--verbose',                    action='store_true', help='Verbose.')
    _parser.add_argument('-n',   '--dry-run',                    action='store_true', help='Dry run.')

    # Info.
    _info = _parser.add_argument_group('%sInformation%s' % (BColors.BOLD, BColors.RESET), 'Get information about user, photosets, photos, exif data, ...')
    _info.add_argument('-fue', '--find-userid-by-email',         action='store_true', help='Find user by email. Use with option --email.')
    _info.add_argument('-fuu', '--find-userid-by-username',      action='store_true', help='Find user by username. Use with option --username.')
    _info.add_argument('-gui', '--get-user-info',                action='store_true', help='Get your user info.\nCan be used with option --user-id to get another user info.')
    _info.add_argument('-lu',  '--lookup-user',                  action='store_true', help='Lookup user with a url.\nUse with option --url.')
    _info.add_argument(        '--get-user-profile-url',         action='store_true', help='Get user''s url from a user''s id.\nUse with option --user-id.')
    _info.add_argument(        '--get-user-photos-url',          action='store_true', help='Get user''s photos from a user''s id.\nUse with option --user-id.')
    _info.add_argument('-gcb', '--get-camera-brands',            action='store_true', help='Get list of camera brands.')
    _info.add_argument('-gcm', '--get-camera-brand-models',      action='store_true', help='Get info of camera brand models.')
    _info.add_argument('-gsi', '--get-photoset-info',            action='store_true', help='Get info of given photoset.\nUse with option --photoset-id.')
    _info.add_argument('-gpi', '--get-photo-info',               action='store_true', help='Get info of given photo.\nUse with option --photo-id.')
    _info.add_argument('-ggi', '--get-gallery-info',             action='store_true', help='Get info of given gallery.\nUse with option --gallery-id.')
    _info.add_argument('-gli', '--get-licenses-info',            action='store_true', help='Get licenses info.')
    _info.add_argument('-gpp', '--get-popular-photos',           action='store_true', help='Get popular photo for a given user.\nUse with option --user-id.')
    _info.add_argument('-gpu', '--get-public-photos',            action='store_true', help='Get public photo for a given user.\nUse with option --user-id.')
    _info.add_argument('-ge',  '--get-exif',                     action='store_true', help='Get Exif data for a given photo.\nUse with option --photo-id (comma-separated photo ids).')
    _info.add_argument('-ggp', '--get-geo-perms',                action='store_true', help='Get geo permissions of given photo.\nUse with option --photo-id (comma-separated photo ids).')
    _info.add_argument('-ggm', '--get-group-member-list',        action='store_true', help='Get group member list.\nUse with option --group-id.')
    _info.add_argument('-ru',  '--recently-updated',             action='store_true', help='List recently updated photos.\nUse with option --min-date.')
    _info.add_argument('-ls',  '--list-photosets',               action='store_true', help='List photosets')
    _info.add_argument('-lp',  '--list-photos',                  action='store_true', help='List photos in given set.\nUse with option --photoset-id.')
    _info.add_argument('-lg',  '--list-galleries',               action='store_true', help='Return the list of galleries created by a user. Sorted from newest to oldest.\nUse with option --user-id.')
    _info.add_argument('-lpg', '--list-photos-in-gallery',       action='store_true', help='List photos in given gallery.\nUse with option --gallery-id.')
    _info.add_argument('-lns', '--list-photos-not-in-set',       action='store_true', help='List photos in not in any set.')
    _info.add_argument('-gpl', '--get-photo-location',           action='store_true', help='Get location of given photo.\nUse with option --photo-id (comma-separated photo ids).')
    _info.add_argument('-g',   '--groups',                       action='store_true', help='Return the list of groups a user is a member of.\nUse with option --user-id.')
    _info.add_argument('-s',   '--search',                       action='store_true', help='Return a list of photos matching some criteria.\nUse with option --user-id. '
                                                                                           'Can be used with an NSID for a specific user or \'\' for any user.\n'
                                                                                           'Other options are available below to refine the search.')
    _info.add_argument('-si',  '--show-image',                   action='store_true', help='Show an image file or a valid image url.\nUse with option --url.')
    _info.add_argument('-gmi', '--get-method-info',              action='store_true', help='Returns information for a given flickr API method.')

    # Upload.
    _upload = _parser.add_argument_group('%sUpload%s' % (BColors.BOLD, BColors.RESET), 'Uploading photos on Flickr.')
    _upload.add_argument('-u',   '--upload',                     action='store_true', help='Upload a photo. Use with options --filename and --tags.')
    _upload.add_argument('-uf',  '--upload-folder',              action='store_true', help='Upload photos in sub-folders contained in folder. Use with option --folder.')

    # Modify.
    _modify = _parser.add_argument_group('%sModify%s' % (BColors.BOLD, BColors.RESET), 'Modify photos on Flickr.')
    _modify.add_argument('-rp',  '--rotate-photo',               action='store_true', help='Rotate photo. Use with option --photo-id (comma-separated photo ids) and --degrees.')
    _modify.add_argument('-sl',  '--set-license',                action='store_true', help='Set license for a given photo.  Use with option --photo-id (comma-separated photo ids) and --license-id.')
    _modify.add_argument('-st',  '--set-tags',                   action='store',      help='Space-separated tags for uploaded files. Use with option --photo-id (comma-separated photo ids).')
    _modify.add_argument('-sp',  '--set-perms',                  action='store_true', help='Set permissions of given photo. Use with option --photo-id (comma-separated photo ids) and -ipu, -ifr and/or -ifa.')
    _modify.add_argument('-spl', '--set-photo-location',         action='store_true', help='Set location of given photo. Use with option --photo-id.')
    _modify.add_argument('-sgp', '--set-geo-perms',              action='store_true', help='Set geo permissions of given photo.\nUse with option --photo-id (comma-separated photo ids) and --is-public, --is-contact, --is-friend and/or --is-family.')
    _modify.add_argument('-spm', '--set-photo-metadata',         action='store_true', help='Set title and description of given photo. Use with option --photo-id (comma-separated photo ids), --title and/or --description.')
    _modify.add_argument('-mpm', '--modify-photoset-metadata',   action='store_true', help='Create a photoset. Use with options --title, --description and --photo-id.')
    _modify.add_argument('-cps', '--create-photoset',            action='store_true', help='Create a photoset. Use with options --title, --description and --photo-id.')
    _modify.add_argument('-app', '--add-photo-to-photoset',      action='store_true', help='Add a photo to an existing photoset. Use with option --photo-id (comma-separated photo ids) and --photoset-id.')

    # Delete.
    _delete = _parser.add_argument_group('%sDelete%s' % (BColors.BOLD, BColors.RESET), 'Delete photos, photosets, tags or location on Flickr.')
    _delete.add_argument('-d',   '--delete',                     action='store_true', help='Delete a photo. Use with option --photo-id (comma-separated photo ids).')
    _delete.add_argument('-dps', '--delete-photoset',            action='store_true', help='Delete a photoset. Use with option --photoset-id.')
    _delete.add_argument('-rt',  '--remove-tag',                 action='store_true', help='Remove tag. Use with option --tag-id. Get tag id with option --get-photo-info.')
    _delete.add_argument('-rpl', '--remove-photo-location',      action='store_true', help='Remove photo location. Use with option --photo-id (comma-separated photo ids).')
    _delete.add_argument('-rpp', '--remove-photo-from-photoset', action='store_true', help='Remove photo(s) from a photoset. Use with option --photo-id (comma-separated photo ids).')

    # Additional args.
    _additional = _parser.add_argument_group('%sAdditional option%s' % (BColors.BOLD, BColors.RESET), 'Additional options to add with the previous ones.')
    _additional.add_argument('-uid', '--user-id',                action='store',      help='User id (NSID, something like xxxxxxxx@Nyy).', default=USER_ID)
    _additional.add_argument('-pid', '--photo-id',               action='store',      help='The id of the photo to get information for.')
    _additional.add_argument('-sid', '--photoset-id',            action='store',      help='The ID of the photoset to fetch information for.')
    _additional.add_argument('-gid', '--gallery-id',             action='store',      help='The ID of the gallery to fetch information for.')
    _additional.add_argument(        '--group-id',               action='store',      help='The ID of the group to fetch information for.')
    _additional.add_argument(        '--url',                    action='store',      help='A url. Use with option --lookup-user.')
    _additional.add_argument('-ti',  '--title',                  action='store',      help='New title.\nUse with option --set-photo-metadata.')
    _additional.add_argument('-de',  '--description',            action='store',      help='New description.\nUse with option --set-photo-metadata.', default='')
    _additional.add_argument('-t',   '--tags',                   action='store',      help='Space-separated tags for uploaded files. Ex: "tag1 tag2"', default='')
    _additional.add_argument('-tid', '--tag-id',                 action='store',      help='The tag. This parameter should contain a tag id,\n'
                                                                                           'as returned by --get-photo-info.')
    _additional.add_argument('-eml', '--email',                  action='store',      help='User contact email. Use with option --find-userid-by-email.')
    _additional.add_argument('-usr', '--username',               action='store',      help='Username. Use with option --find-userid-by-username.')
    _additional.add_argument('-f',   '--filename',               action='store',      help='Path to photo filename. Can be an absolute or relative path.\nUse with option --upload.')
    _additional.add_argument('-fo',  '--folder',                 action='store',      help='Folder with sub-folders containing photos to upload.\nUse with option --upload-folder.', default=PICTURE_FOLDER_PATH)
    _additional.add_argument('-ss',  '--safe-search',            action='store',      help='Safe search (1 for safe (default), 2 for moderate, 3 for restricted).\nUse with option --get-public-photos.')
    _additional.add_argument('-ipu', '--is-public',              action='store',      help='Set public permission of given photo.\nUse with option --photo-id.', default='0')
    _additional.add_argument('-ico', '--is-contact',             action='store',      help='Set contact permission of given photo.\nUse with option --photo-id.', default='0')
    _additional.add_argument('-ifr', '--is-friend',              action='store',      help='Set friend permission of given photo.\nUse with option --photo-id.', default='0')
    _additional.add_argument('-ifa', '--is-family',              action='store',      help='Set family permission of given photo.\nUse with option --photo-id.', default='0')
    _additional.add_argument('-pf',  '--privacy-filter',         action='store',      help='Privacy filter. Possible values are 0 (all photos, default), 1 (public photos),\n'
                                                                                           '2 (private photos visible to friends),\n3 (private photos visible to family),\n'
                                                                                           '4 (private photos visible to friends & family), or 5 (completely private photos).\nUse with option --list-photos-not-in-set.')
    _additional.add_argument('-ps',  '--popular-sort',           action='store',      help='Sort popular photos. Possible values are faves, views, comments or interesting\n'
                                                                                           '(default).', default='interesting')
    _additional.add_argument('-min', '--min-date',               action='store',      help='Minimum date. Date can be a Unix timestamp or any English textual datetime\n'
                                                                                           'description indicating the date from which modifications should be compared.\nUse with option --recently-updated.')
    _additional.add_argument('-m',   '--media',                  action='store',      help='Media type. Possible values are all (default), photos or videos.\nUse with option --list-photos-not-in-set.', default='all')
    _additional.add_argument(        '--min-upload-date',        action='store',      help='Minimum upload date. Photos with an upload date greater than or equal to this\n'
                                                                                           'value will be returned. The date can be in the form of a unix timestamp or\n'
                                                                                           'mysql datetime.\nUse with option --list-photos-not-in-set.')
    _additional.add_argument(        '--max-upload-date',        action='store',      help='Maximum upload date. Photos with an upload date less than or equal to this\n'
                                                                                           'value will be returned. The date can be in the form of a unix timestamp or\n'
                                                                                           'mysql datetime.\nUse with option --list-photos-not-in-set.')
    _additional.add_argument(        '--min-taken-date',         action='store',      help='Minimum taken date. Photos with an taken date greater than or equal to this\n'
                                                                                           'value will be returned. The date can be in the form of a mysql datetime or\n'
                                                                                           'unix timestamp.\nUse with option --list-photos-not-in-set.')
    _additional.add_argument(        '--max-taken-date',         action='store',      help='Maximum taken date. Photos with an taken date less than or equal to this value\n'
                                                                                           'will be returned. The date can be in the form of a mysql datetime or unix\n'
                                                                                           'timestamp.\nUse with option --list-photos-not-in-set.')
    _additional.add_argument('-lid', '--license-id',             action='store',      help='License id.\nSee option --get-license-info.')
    _additional.add_argument('-lat', '--latitude',               action='store',      help='Latitude of photo.\nUse with option --set-photo-location.')
    _additional.add_argument('-lon', '--longitude',              action='store',      help='Longitude of photo.\nUse with option --set-photo-location.')
    _additional.add_argument('-deg', '--degrees',                action='store',      help='Angle of rotation. Possible value are 90, 180 or 270.\n'
                                                                                         'Use with option --photo-id and --rotate-photo.')
    _additional.add_argument('-cb',  '--camera-brand',           action='store',      help='Camera brand')
    _additional.add_argument('-mn',  '--method-name',            action='store',      help='Method name.\nSee option --get-method-info.')

    # Search.
    _search = _parser.add_argument_group('%sSearch%s' % (BColors.BOLD, BColors.RESET), 'Search photos with option --search. Use the option below as well as --user-id, \n'
                                                                                       '--privacy-filter, --tags, --accuracy, --safe-search, --group-id, --media, --latitude, --longitude.')
    _search.add_argument(            '--text',                   action='store',      help='A free text search.Photos who''s title, description or tags contain the text\n'
                                                                                           'will be returned. You can exclude results that match a term by prepending it\n'
                                                                                           'with a - character.\n'
                                                                                           'Use with option --photo-id and --rotate-photo.')
    _search.add_argument(            '--sort',                   action='store',      help='The order in which to sort returned photos. Defaults to date-posted-desc\n'
                                                                                           '(unless you are doing a radial geo query, in which case the default sorting\n'
                                                                                           'is by ascending distance from the point specified). The possible values are:\n'
                                                                                           'date-posted-asc, date-posted-desc, date-taken-asc, date-taken-desc,\n'
                                                                                           'interestingness-desc, interestingness-asc, and relevance.\n'
                                                                                           'Use with option --photo-id and --rotate-photo.')
    _search.add_argument(            '--contacts',               action='store',      help='Search your contacts. Either ''all'' or ''ff'' for just friends and family. (Experimental)')
    _search.add_argument(            '--accuracy',               action='store',      help='Recorded accuracy level of the location information. Current range is 1-16:\n'
                                                                                           '- World level is 1\n- Country is ~3\n- Region is ~6\n- City is ~11\n- Street is ~16')
    _search.add_argument(            '--content-type',           action='store',      help='Content Type setting:\n'
                                                                                           '- 1 for photos only.\n'
                                                                                           '- 2 for screenshots only.\n'
                                                                                           '- 3 for ''other'' only.\n'
                                                                                           '- 4 for photos and screenshots.\n'
                                                                                           '- 5 for screenshots and ''other''.\n'
                                                                                           '- 6 for photos and ''other''.\n'
                                                                                           '- 7 for photos, screenshots, and ''other'' (all).\n')
    _search.add_argument(            '--has-geo',                action='store',      help='Any photo that has been geotagged, or if the value is "0" any photo that has not\n'
                                                                                           'been geotagged.\n'
                                                                                           'Geo queries require some sort of limiting agent in order to prevent the database\n'
                                                                                           'from crying. This is basically like the check against "parameterless searches" for\n'
                                                                                           'queries without a geo component.\n'
                                                                                           'A tag, for instance, is considered a limiting agent as are user defined min_date_taken\n'
                                                                                           'and min_date_upload parameters - If no limiting factor is passed we return only photos\n'
                                                                                           'added in the last 12 hours (though we may extend the limit in the future).')
    _search.add_argument(            '--geo-context',            action='store',      help='Geo context is a numeric value representing the photo''s geotagginess beyond latitude\n'
                                                                                           'and longitude. For example, you may wish to search for photos that were taken "indoors"\n'
                                                                                           'or "outdoors".\n'
                                                                                           'The current list of context IDs is :\n- 0, not defined.\n- 1, indoors.\n- 2, outdoors.\n'
                                                                                           'Geo queries require some sort of limiting agent in order to prevent the database from\n'
                                                                                           'crying. This is basically like the check against "parameterless searches" for queries\n'
                                                                                           'without a geo component. \n'
                                                                                           'A tag, for instance, is considered a limiting agent as are user defined min_date_taken\n'
                                                                                           'and min_date_upload parameters - If no limiting factor is passed we return only photos\n'
                                                                                           'added in the last 12 hours (though we may extend the limit in the future).')
    _search.add_argument(            '--per-page',               action='store',      help='Number of photos to return per page. If this argument is omitted, it defaults to 100.\n'
                                                                                           'The maximum allowed value is 500.\n', default='500')
    _search.add_argument(            '--page',                   action='store',      help='The page of results to return. If this argument is omitted, it defaults to 1.\n')

    _args = _parser.parse_args()

    if not len(sys.argv) > 1:
        _parser.print_help()
        sys.exit(1)

    return _args


##########################################################################
##########################################################################

if __name__ == '__main__':

    try:
        # Ensure that only one instance of this script is running
        LOCK_PATH = os.path.join(os.path.dirname(sys.argv[0]), '.flickrlock')
        f = open(LOCK_PATH, 'w')
        try:
            fcntl.lockf(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except IOError, e:
            if e.errno == errno.EAGAIN:
                sys.stderr.write('[%s] Script already running.\n' % time.strftime('%c'))
                sys.exit(-1)
            raise

        # Get parsed arguments.
        args = argument_parser()

        if args.compile_script:
            compile_script()

        if args.verbose:
            print args

        if args.debug:
            print('%s%sBLACK%s RED%s GREEN%s YELLOW%s BLUE%s MAGENTA%s CYAN%s WHITE%s' %
                    (BColors.BOLD, BColors.BLACK, BColors.RED, BColors.GREEN, BColors.YELLOW, BColors.BLUE, BColors.MAGENTA, BColors.CYAN, BColors.WHITE, BColors.RESET))
            print('PICTURE_FOLDER_PATH = %s' % (PICTURE_FOLDER_PATH))

        if args.debug:
            logging.basicConfig(level=logging.DEBUG)
            logging.getLogger('requests_oauthlib').setLevel(logging.INFO)
            logging.getLogger('oauthlib').setLevel(logging.INFO)

        # Check if USER_ID and API key/secret exist.
        if USER_ID == '':
            if args.user_id == '':
                print('Edit file config.ini and add your USER_ID or use option --user-id.')
                sys.exit(1)
        if FLICKR['api_key'] == '':
            print('Edit file config.ini and add your API key.')
            sys.exit(1)
        if FLICKR['api_secret'] == '':
            print('Edit file config.ini and add your API secret.')
            sys.exit(1)

        print('--------- Start time: ' + time.strftime('%c') + ' ---------')
        print('')

        # If no option, should print the help message.
        fb = FlickrBatch()

        fb.setup_database()

        if args.verbose:
            fb.verbose = 1
        if args.debug:
            fb.debug = 1

        # Returns information for a given flickr API method.
        if args.get_method_info:
            print('Method name: %s (%s)' % (args.method_name, args.get_method_info))
            fb.get_method_info(fb.flickr, args.method_name)

        # Find user id by email.
        if args.find_userid_by_email:
            nsid = fb.find_userid_by_email(fb.flickr, args.email)

        # Find user id by username.
        if args.find_userid_by_username:
            nsid = fb.find_userid_by_username(fb.flickr, args.username)

        # Lookup user with url.
        if args.lookup_user:
            fb.lookup_user(fb.flickr, args.url)

        # Get user's url.
        if args.get_user_profile_url:
            fb.get_user_profile_url(fb.flickr, args.user_id)

        # Get user's photos.
        if args.get_user_photos_url:
            fb.get_user_photos_url(fb.flickr, args.user_id)

        # Show user info.
        if args.get_user_info:
            fb.get_user_info(fb.flickr, args.user_id)

        # List groups user is member of.
        if args.groups:
            fb.get_user_groups(fb.flickr, args.user_id)

        # List group members.
        if args.get_group_member_list:
            if args.group_id == None:
                print('Give group id. Use option --group-id.')
                sys.exit(1)

            fb.get_group_member_list(fb.flickr, args.group_id)

        # List photos not in any set.
        if args.list_photos_not_in_set:
            fb.get_photos_not_in_set(fb.flickr, args.privacy_filter, args.media,
                    args.max_taken_date, args.min_taken_date,
                    args.max_upload_date, args.min_upload_date)

        # Exif data
        if args.get_exif:
            if args.photo_id == None:
                print('Give comma-separated photo ids. Use option --photo-id.')
                sys.exit(1)

            for photo_id in args.photo_id.split(','):
                fb.get_exif_data(fb.flickr, photo_id)

        # Get licenses.
        if args.get_licenses_info:
            fb.get_licenses_info(fb.flickr)

        # Set licenses.
        if args.set_license:
            if args.photo_id == None:
                print('Give comma-separated photo ids. Use option --photo-id.')
                sys.exit(1)

            if args.license_id == None:
                print('Give license id. Use option --license-id.')
                sys.exit(1)

            for photo_id in args.photo_id.split(','):
                fb.set_license(fb.flickr, photo_id, args.license_id)


        # Get list of photosets.
        if args.list_photosets:
            fb.get_photoset_list(fb.flickr, args.user_id)

        # Get list of photos ina photoset.
        if args.list_photos:
            if args.photoset_id == None:
                print('Give photoset id. Use option --photoset-id.')
                sys.exit(1)

            fb.get_photo_list(fb.flickr, args.user_id, args.photoset_id)

        # Get gallery info.
        if args.get_gallery_info:
            if args.gallery_id == None:
                print('Give gallery id. Use option --gallery-id.')
                sys.exit(1)

            fb.get_gallery_info(fb.flickr, args.gallery_id)

        if args.list_galleries:
            fb.get_galleries_list(fb.flickr, args.user_id)

        if args.list_photos_in_gallery:
            if args.gallery_id == None:
                print('Give gallery id. Use option --gallery-id.')
                sys.exit(1)

            fb.get_gallery_photos(fb.flickr, args.gallery_id)

        if args.get_public_photos:
            fb.get_public_photos(fb.flickr, args.user_id, args.safe_search)

        # Get list of popular photos.
        if args.get_popular_photos:
            fb.get_popular_photos(fb.flickr, args.user_id, args.sort)

        # Get list of camera brands.
        if args.get_camera_brands:
            fb.get_camera_brands(fb.flickr)

        # Get info of camera brand models.
        if args.get_camera_brand_models:
            if args.camera_brand == None:
                print('Give brand. Use option --camera-brand.')
                sys.exit(1)

            fb.get_camera_brand_models(fb.flickr, args.camera_brand)

        # Get photoset info.
        if args.get_photoset_info:
            if args.photoset_id == None:
                print('Give photoset id. Use option --photoset-id.')
                sys.exit(1)

            (owner,username,photos,count_photos,count_videos,date_create,date_update,primary,title,description) = fb.get_photoset_info(fb.flickr, args.user_id, args.photoset_id)

        # Get photo info.
        if args.get_photo_info:
            if args.photo_id == None:
                print('Give comma-separated photo ids. Use option --photo-id.')
                sys.exit(1)

            for photo_id in args.photo_id.split(','):
                fb.get_photo_info(fb.flickr, photo_id)

        # Get photo location.
        if args.set_photo_location:
            if args.photo_id == None:
                print('Give photo id. Use option --photo-id.')
                sys.exit(1)

            if args.latitude == None:
                print('Give latitude. Use option --longitude.')
                sys.exit(1)

            if args.longitude == None:
                print('Give longitude. Use option --longitude.')
                sys.exit(1)

            fb.set_photo_location(fb.flickr, args.photo_id, args.latitude, args.longitude, accuracy=15, context=0)

        # Get photo location.
        if args.get_photo_location:
            if args.photo_id == None:
                print('Give comma-separated photo ids. Use option --photo-id.')
                sys.exit(1)

            for photo_id in args.photo_id.split(','):
                fb.get_photo_location(fb.flickr, photo_id)

        # Get photo location.
        if args.remove_photo_location:
            if args.photo_id == None:
                print('Give comma-separated photo ids. Use option --photo-id.')
                sys.exit(1)

            for photo_id in args.photo_id.split(','):
                fb.remove_photo_location(fb.flickr, photo_id)

        # Search photos
        if args.search:
            if args.user_id == '':
                args.user_id = None
            if args.tags == '':
                args.tags = None

            if not args.text == None:
                args.text = args.text.lower()

            tag_mode         = None
            bbox             = None
            machine_tags     = None
            machine_tag_mode = None
            woe_id           = None
            place_id         = None
            radius           = None
            radius_units     = None
            is_commons       = None
            in_gallery       = None
            is_getty         = None

            kwargs = {
                    'user_id'          : args.user_id,
                    'tags'             : args.tags,
                    'tag_mode'         : tag_mode,
                    'text'             : args.text,
                    'min_upload_date'  : args.min_upload_date,
                    'max_upload_date'  : args.max_upload_date,
                    'min_taken_date'   : args.min_taken_date,
                    'max_taken_date'   : args.max_taken_date,
                    'license'          : args.license_id,
                    'sort'             : args.sort,
                    'privacy_filter'   : args.privacy_filter,
                    'bbox'             : bbox,
                    'accuracy'         : args.accuracy,
                    'safe_search'      : args.safe_search,
                    'content_type'     : args.content_type,
                    'machine_tags'     : machine_tags,
                    'machine_tag_mode' : machine_tag_mode,
                    'group_id'         : args.group_id,
                    'contacts'         : args.contacts,
                    'woe_id'           : woe_id,
                    'place_id'         : place_id,
                    'media'            : args.media,
                    'has_geo'          : args.has_geo,
                    'geo_context'      : args.geo_context,
                    'lat'              : args.latitude,
                    'lon'              : args.longitude,
                    'radius'           : radius,
                    'radius_units'     : radius_units,
                    'is_commons'       : is_commons,
                    'in_gallery'       : in_gallery,
                    'is_getty'         : is_getty,
                    'per_page'         : args.per_page
                    }

            fb.search_photos(fb.flickr, args.page, args.print_on_screen, **kwargs)

        # Upload photo to flickr.
        if args.upload:
            if not os.path.isfile(args.filename):
                print('File %s not found!' % args.filename)
                sys.exit(1)

            title = args.title
            if args.title == None:
                title = os.path.basename(args.filename)

            t0 = time.time()
            fb.upload_photo(fb.flickr, args.filename, title, args.description, args.tags, args.is_public, args.is_friend, args.is_family)
            print('Total time : %f s' % (time.time()-t0))

        # Upload photos in subfolder.
        if args.upload_folder:
            photos_to_sync, photoset_ids = fb.synclist(args.user_id, args.folder)
            t0 = time.time()
            fb.upload_folder(photos_to_sync, args.tags, args.is_public, args.is_friend, args.is_family, args.folder, photoset_ids)
            print('Total time : %f s' % (time.time()-t0))

        # Add photo to existing photoset.
        if args.add_photo_to_photoset:
            if args.photo_id == None:
                print('Give comma-separated photo ids. Use option --photo-id.')
                sys.exit(1)

            for photo_id in args.photo_id.split(','):
                fb.add_photo_to_photoset(fb.flickr, args.photoset_id, photo_id)

        # Remove photo from existing photoset.
        if args.remove_photo_from_photoset:
            if args.photo_id == None:
                print('Give comma-separated photo ids. Use option --photo-id.')
                sys.exit(1)

            #nphotos =  len(args.photo_id.split(','))
            #fb.remove_photo_from_photoset(fb.flickr, nphotos, args.photoset_id, args.photo_id)
            fb.remove_photo_from_photoset(fb.flickr, args.photoset_id, args.photo_id)

        # Create a photoset.
        if args.create_photoset:
            if args.photo_id == None:
                print('A photo id is required for the primary photo to create a photoset. Use option --photo-id.')
                sys.exit(1)

            if args.title == None:
                print('Title is required to create a photoset. Use option --title.')
                sys.exit(1)

            fb.create_photoset(fb.flickr, args.title, args.description, args.photo_id)

        # Delete a photoset.
        if args.delete_photoset:
            if args.photoset_id == None:
                print('Option --photoset-id is missing!')
                sys.exit(1)

            fb.delete_photoset(fb.flickr, args.photoset_id)

        # Modify a photoset's meta-data.
        if args.modify_photoset_metadata:
            if args.photoset_id == None:
                print('Option --photoset-id is missing!')
                sys.exit(1)

            if args.title == None:
                print('Option --title is missing!')
                sys.exit(1)

            description = args.description

            if args.description == None:
                (owner,username,photos,count_photos,count_videos,date_create,date_update,primary,title,description) = fb.get_photoset_info(fb.flickr, args.user_id, args.photoset_id, 0)

            fb.modify_photoset_metadata(fb.flickr, args.photoset_id, args.title, description)

        # Show recently updated photos after 'min_date'
        if args.recently_updated:
            if args.min_date == None:
                print('Option --min-date is missing!')
                sys.exit(1)

            fb.get_recent_photos(fb.flickr, args.min_date)

        # Delete photo
        if args.delete:
            if args.photo_id == None:
                print('Give comma-separated photo ids. Use option --photo-id.')
                sys.exit(1)

            for photo_id in args.photo_id.split(','):
                fb.delete_photo(fb.flickr, photo_id)

        # Set tags of a photo.
        if args.set_tags:
            if args.photo_id == None:
                print('Give comma-separated photo ids. Use option --photo-id.')
                sys.exit(1)

            if args.tags == None:
                print('Give tags. Use option --tags.')
                sys.exit(1)

            for photo_id in args.photo_id.split(','):
                fb.set_tags(fb.flickr, photo_id, args.set_tags)

        # Remove tags.
        if args.remove_tag:
            if args.tag_id == None:
                print('Give tags. Use option --tag-id.')
                sys.exit(1)

            fb.remove_tag(fb.flickr, args.tag_id)

        # Set permissions.
        if args.set_perms:
            if args.photo_id == None:
                print('Give comma-separated photo ids. Use option --photo-id.')
                sys.exit(1)

            for photo_id in args.photo_id.split(','):
                fb.get_permissions(fb.flickr, photo_id)

                ispublic = fb.is_public
                isfriend = fb.is_friend
                isfamily = fb.is_family

                if args.is_public == '0':
                    ispublic = 0
                if args.is_public == '1':
                    ispublic = 1
                if args.is_friend == '0':
                    isfriend = 0
                if args.is_friend == '1':
                    isfriend = 1
                if args.is_family == '0':
                    isfamily = 0
                if args.is_family == '1':
                    isfamily = 1

                fb.set_permissions(fb.flickr, photo_id, ispublic, isfriend, isfamily)

        # Set geo permissions.
        if args.set_geo_perms:
            if args.photo_id == None:
                print('Give comma-separated photo ids. Use option --photo-id.')
                sys.exit(1)

            for photo_id in args.photo_id.split(','):
                fb.get_geo_permissions(fb.flickr, photo_id, 0)

                ispublic  = fb.is_public
                iscontact = fb.is_contact
                isfriend  = fb.is_friend
                isfamily  = fb.is_family

                if args.is_public == '0':
                    ispublic = '0'
                if args.is_public == '1':
                    ispublic = '1'
                if args.is_contact == '0':
                    iscontact = '0'
                if args.is_contact == '1':
                    iscontact = '1'
                if args.is_friend == '0':
                    isfriend = '0'
                if args.is_friend == '1':
                    isfriend = '1'
                if args.is_family == '0':
                    isfamily = '0'
                if args.is_family == '1':
                    isfamily = '1'

                fb.set_geo_permissions(fb.flickr, ispublic, iscontact, isfriend, isfamily, photo_id)
                fb.get_geo_permissions(fb.flickr, photo_id)

        # Get geo permissions.
        if args.get_geo_perms:
            if args.photo_id == None:
                print('Give comma-separated photo ids. Use option --photo-id.')
                sys.exit(1)

            for photo_id in args.photo_id.split(','):
                fb.get_geo_permissions(fb.flickr, photo_id)

        # Set photo metadata.
        if args.set_photo_metadata:
            if args.photo_id == None:
                print('Give comma-separated photo ids. Use option --photo-id.')
                sys.exit(1)

            for photo_id in args.photo_id.split(','):
                fb.set_photo_metadata(fb.flickr, photo_id, args.title, args.description)

        # Rotate photo.
        if args.rotate_photo:
            if args.photo_id == None:
                print('Give comma-separated photo ids. Use option --photo-id.')
                sys.exit(1)

            if args.degrees not in ('90', '180', '270'):
                print('Angle of rotation must be 90, 180 or 270! (%s)' % args.degrees)
                sys.exit(1)

            for photo_id in args.photo_id.split(','):
                fb.rotate_photo(fb.flickr, photo_id, args.degrees)

        # Display image on screen.
        if args.show_image:
            fb.show_image(args.url)

        print('')
        print('--------- End time: ' + time.strftime('%c') + ' ---------')

    except KeyboardInterrupt:
        print('\nExit by user request (CTRL-C)!\n')
        sys.exit()

    ### That's all, Folks! ###
