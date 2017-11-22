
FlickrBatch
===========

Python script to update, delete or manipulate photos and videos on Flickr.

Installation
------------

To be able to use FlickBatch, you need to get an API key and secret from Flickr. They are available for free at <http://www.flickr.com/services/apps/create/apply>.

Copy file `config.ini.am` to `config.ini` and edit the following lines:

* Setup your **`USER_ID`**

        USER_ID = 'XXXXXXXX@N00'     

* Setup your **`PICTURE_FOLDER_PATH`**

        PICTURE_FOLDER_PATH = 'xxxxxxxxxxxxx'

* Setup your `api_key` and `api_secret` in dictionnary **`FLICKR`**

        FLICKR = {
                "title"                 : "",
                "description"           : "",
                "tags"                  : "auto-upload",
                "is_public"             : "0",
                "is_friend"             : "0",
                "is_family"             : "0",
                "api_key"               : u'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
                "api_secret"            : u'xxxxxxxxxxxxxxxx'
        }

    You can also edit the keys `title`, `description`, `tags`, `is_public`, `is_friend` and `is_family`.

When run without any option:

        $ flickrbatch.py

the directory `$HOME/.config/flickrbatch` is created. Copy your `config.ini` file in that directory:

        $ cp config.ini $HOME/.config/flickrbatch


Examples
--------

0. Get help

        $ flickrbatch.py [-h | --help]

1. Find someone's user id by email address:

        $ flickrbatch.py --find-userid-by-email --email xxx.yyy@domain.com
        USERNAME: ABCXYZ
        NSID: XXXXXXXX@N00


1. Find someone's user id by username:

        $ flickrbatch.py --find-userid-by-username --username ABCXYZ
        USERNAME: ABCXYZ
        NSID: XXXXXXXX@N00

    You can fill the **`USER_ID`** variable in your `config.ini` file.

1. Get your info

        $ flickrbatch.py --get-user-info

2. Get another user's info with his user id XXXXXXXX@N00

        $ flickrbatch.py --get-user-info --user-id XXXXXXXX@N00

3. Upload a photo with a title, a description and tags:

        $ flickrbatch.py --upload --filename ./path/to/photo.png --title "The title" --description "The description" --tags '''tag1 tag2 "long tag"'''

4. upload photos contained in sub-folder:

   Photos are located in ./path/to/folder/subfolder.   
   Photos will be uploaded on Flickr and put in a photoset named after the sub-folder's name.

        $ flickrbatch.py --upload-folder --folder ./path/to/folder

5. Get a list of photosets:

        $ flickrbatch.py --list-photosets
        0 :: TITLE: My beautiful pictures | DESCRIPTION: Pictures I have taken | PHOTOS: 431 | VIDEOS: 0 | CREATED: 1505068703 | PHOTOSET ID: 12345678901234567

6. Get a list of photos in a given photoset:

        $ flickrbatch.py --list-photos --photoset-id 12345678901234567
        0 :: PHOTO ID: 1234567890 | TITLE: My picture | IS PUBLIC: 1 | IS FRIEND: 0 | IS FAMILY: 0

7. List photos not in any set:

        $ flickrbatch.py --list-photos-not-in-set
        Total number of photos : 335 (1 pages)
        0 :: PHOTO ID: 98765432 | TITLE: A picture | OWNER: 12345678@N00 | IS PUBLIC: 0 | IS FRIEND: 0 | IS FAMILY: 0
        1 :: PHOTO ID: 98674532 | TITLE: A picture | OWNER: 12345678@N00 | IS PUBLIC: 0 | IS FRIEND: 0 | IS FAMILY: 0

8. List recently updated photos:

        $ flickrbatch.py --recently-updated --min-date 2017-03-27
        0 :: PHOTO ID: 37134838686 | TITLE: ./Screenshots/photo.jpg | OWNER: XXXXXXXX@N00 | IS PUBLIC: 0 | IS FRIEND: 0 | IS FAMILY: 0


9. Get a photo's info

        $ flickrbatch.py --get-photo-info --photo-id 1464293574
        PHOTO ID: 1464293574
        TITLE: 2007oktoberfest2
        DESCRIPTION: Oktoberfest 2007
        Cincinnati, Ohio
        LICENSE: All Rights Reserved (0)
        LAST UPDATED: 2010-08-02 10:31:37
        POSTED: 2007-09-30 19:29:12
        TAKEN: 2007-09-22 02:29:15
        IS PUBLIC: 1
        IS FRIEND: 0
        IS FAMILY: 0
        --- TAGS
	        0 | TAG: oktoberfest | TAG ID: 3547832-1464293574-9977 | AUTHOR NAME: Sandra Freyler | AUTHOR: 65591595@N00
        	1 | TAG: cincinnati | TAG ID: 3547832-1464293574-5630 | AUTHOR NAME: Sandra Freyler | AUTHOR: 65591595@N00
        	2 | TAG: ohio | TAG ID: 3547832-1464293574-226 | AUTHOR NAME: Sandra Freyler | AUTHOR: 65591595@N00
        	3 | TAG: downtown | TAG ID: 3547832-1464293574-3318 | AUTHOR NAME: Sandra Freyler | AUTHOR: 65591595@N00
        	4 | TAG: food | TAG ID: 3547832-1464293574-338 | AUTHOR NAME: Sandra Freyler | AUTHOR: 65591595@N00
        	5 | TAG: beer | TAG ID: 3547832-1464293574-808 | AUTHOR NAME: Sandra Freyler | AUTHOR: 65591595@N00
        	6 | TAG: fun | TAG ID: 3547832-1464293574-1743 | AUTHOR NAME: Sandra Freyler | AUTHOR: 65591595@N00
        	7 | TAG: german | TAG ID: 3547832-1464293574-13796 | AUTHOR NAME: Sandra Freyler | AUTHOR: 65591595@N00
        	8 | TAG: zincinnati | TAG ID: 3547832-1464293574-15863614 | AUTHOR NAME: Sandra Freyler | AUTHOR: 65591595@N00
        --- URLS
	        0 | TYPE: photopage | URL: https://www.flickr.com/photos/sandrafreyler/1464293574/
        Error: 2: Photo has no location information.
        --- SIZES
	        0 | MEDIA: photo | LABEL: Square | WIDTH: 75 | HEIGHT: 75
		        SOURCE: https://farm2.staticflickr.com/1210/1464293574_104d15049c_s.jpg
        		URL: https://www.flickr.com/photos/sandrafreyler/1464293574/sizes/sq/
	        1 | MEDIA: photo | LABEL: Large Square | WIDTH: 150 | HEIGHT: 150
		        SOURCE: https://farm2.staticflickr.com/1210/1464293574_104d15049c_q.jpg
        		URL: https://www.flickr.com/photos/sandrafreyler/1464293574/sizes/q/
	        2 | MEDIA: photo | LABEL: Thumbnail | WIDTH: 100 | HEIGHT: 67
		        SOURCE: https://farm2.staticflickr.com/1210/1464293574_104d15049c_t.jpg
        		URL: https://www.flickr.com/photos/sandrafreyler/1464293574/sizes/t/
	        3 | MEDIA: photo | LABEL: Small | WIDTH: 240 | HEIGHT: 160
		        SOURCE: https://farm2.staticflickr.com/1210/1464293574_104d15049c_m.jpg
        		URL: https://www.flickr.com/photos/sandrafreyler/1464293574/sizes/s/
	        4 | MEDIA: photo | LABEL: Medium | WIDTH: 500 | HEIGHT: 333
		        SOURCE: https://farm2.staticflickr.com/1210/1464293574_104d15049c.jpg
        		URL: https://www.flickr.com/photos/sandrafreyler/1464293574/sizes/m/
	        5 | MEDIA: photo | LABEL: Medium 640 | WIDTH: 640 | HEIGHT: 427
		        SOURCE: https://farm2.staticflickr.com/1210/1464293574_104d15049c_z.jpg?zz=1
        		URL: https://www.flickr.com/photos/sandrafreyler/1464293574/sizes/z/

10. Delete photos from Flickr

    - A single photo:

            $ flickrbatch.py --delete --photo-id 1234567890
            Deleting photo (id: 1234567890).
            Do you really want to delete this photo? (y/n) n
            Photo deleted.

    - Multiple photos with comma-separated photo ids:

            $ flickrbatch.py --delete --photo-id 1234567890,1098765432,2109876543
            Deleting photo (id: 1234567890).
            Do you really want to delete this photo? (y/n) n
            Photo deleted.
            Deleting photo (id: 1098765432).
            Do you really want to delete this photo? (y/n) n
            Photo deleted.
            Deleting photo (id: 2109876543).
            Do you really want to delete this photo? (y/n) n
            Photo deleted.

11. Get public photos from a user:

        $ flickrbatch.py --get-public-photos --user-id 97624390@N00

12. Get a list of galleries of a given user:

        $ flickrbatch.py --list-galleries --user-id 97624390@N00

13. List photos from a gallery:

        $ flickrbatch.py --list-photos-in-gallery --gallery-id 341101-72157624736896636

14. Search photos or videos:

    Get number of public photos on Flickr.

        $ flickrbatch.py --search --user-id '' --media photos
        Total number of photos (or videos) : 348555 (698 pages)

    Get number of public videos on Flickr.

        $ flickrbatch.py --search --user-id '' --media videos
        Total number of photos (or videos) : 427819 (856 pages, 500 per page)

        $ flickrbatch.py --search --user-id '' --tags 永平寺
        Total number of photos : 1467 (3 pages)
        0 :: PHOTO ID: 36072607564 | TITLE: ZAZEN (座禅） | OWNER: 36015194@N00 | IS PUBLIC: 1 | IS FRIEND: 0 | IS FAMILY: 0
        1 :: PHOTO ID: 36541974121 | TITLE: DSC02208 | OWNER: 151065778@N06 | IS PUBLIC: 1 | IS FRIEND: 0 | IS FAMILY: 0
        2 :: PHOTO ID: 33976319234 | TITLE: Eihei-ji: meditation chamber | OWNER: 106445736@N05 | IS PUBLIC: 1 | IS FRIEND: 0 | IS FAMILY: 0
        3 :: PHOTO ID: 34432964420 | TITLE: Eihei-ji | OWNER: 106445736@N05 | IS PUBLIC: 1 | IS FRIEND: 0 | IS FAMILY: 0
        4 :: PHOTO ID: 34415795575 | TITLE: 20160826_150637-01 | OWNER: 142226915@N06 | IS PUBLIC: 1 | IS FRIEND: 0 | IS FAMILY: 0
        5 :: PHOTO ID: 34374449016 | TITLE: 20160826_150739-01 | OWNER: 142226915@N06 | IS PUBLIC: 1 | IS FRIEND: 0 | IS FAMILY: 0
        6 :: PHOTO ID: 34415794115 | TITLE: 20160826_150654-01 | OWNER: 142226915@N06 | IS PUBLIC: 1 | IS FRIEND: 0 | IS FAMILY: 0


15. Lookup user with url:

        $ flickrbatch.py --lookup-user --url https://www.flickr.com/photos/opencage/albums
        Lookup user with url.
        USER ID: 97624390@N00
        USERNAME: Daiju Azuma


16. Get user's profile url:

        $ flickrbatch.py --get-user-profile-url --user-id 97624390@N00
        Get users profile url.
        NSID: 97624390@N00
        USERS PROFILE URL: https://www.flickr.com/people/opencage/

17. Get user's photo url:

        $ flickrbatch.py --get-user-photos-url --user-id 97624390@N00
        Get users photo url.
        NSID: 97624390@N00
        USERS PHOTOS URL: https://www.flickr.com/photos/opencage/

18. View image:

    * from a url:

            $ flickrbatch.py --show-image --url https://farm5.staticflickr.com/4403/37276683461_5da2f8d42c_b.jpg

    * from a file:

            $ flickrbatch.py --show-image --url ./path/to/image.jpg
