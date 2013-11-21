"""
Script to thank friends on their posts for your birthday.
"""

import sys
import urllib
import urllib2
import time
import datetime
import json
import webbrowser

LIMIT = 300     # Change if greater than 300 friends have wished! :P
ACCESS_TOKEN = ''
ACCESS_URL = "https://graph.facebook.com/"
USERNAME = ''


def getaccesstoken():
    """
    getaccesstoken()->ACCESS_TOKEN
    Presents user with the choice of creating a token or supplying
    one to the script which it uses later to fetch wall posts and
    comment on them.
    """
    print ("The script needs your ACCESS TOKEN.\n"
           "What would you like to do?\n"
           "1. Generate a new TOKEN.\n"
           "2. Supply one (if you know how to generate it).\n")
    
    choice = 0 
    while choice not in range(1,3):
      try:
        choice = int(raw_input("Choice (1 or 2) ? :"))
      except ValueError, e:
        continue

    if choice == 2:
        access_token = raw_input("\nEnter the TOKEN string: ")
    else:
        print ("\nTo generate your token the script needs access to your feeds"
               " and publishing\npermissions. Don't worry the script doesn't"
               " store anything or spam your wall!\nGo to the links which will"
               " open in your browser shortly and give the permissions to read"
               " your data, once you give that permission another link will"
               " open which has your token, the token is a long string and"
               " looks something like this\nCAACEdEose0.......cBABKNtliuHS7.\n"
               "Copy it and paste it below.")
    time.sleep(25)
    print "\nOpening links now..."
    webbrowser.open("https://www.facebook.com/dialog/oauth?"
                    "response_type=token&client_id=145634995501895&"
                    "redirect_uri=http://developers.facebook.com/tools/"
                    "explorer/callback&scope=user_birthday,publish_actions"
                    ",read_stream")
    time.sleep(40)
    webbrowser.open("http://developers.facebook.com/tools/explorer")
    access_token = raw_input("\nEnter the TOKEN string obtained from API "
                             "explorer page: ")
    return access_token


def collect_data():
    """
    collect_data()->post_data
    Collects user's birthday and gets all the wall posts on his wall
    from previous day and constructs a list of dictionaries containing
    post_id and name of the poster and returns the list as post_data.
    """
    # get user's birthday
    try:
        datafile = urllib2.urlopen(ACCESS_URL +
                                   'me?fields=birthday&access_token=' +
                                   ACCESS_TOKEN)
    except urllib2.URLError, urllib2.HTTPError:
        print ("\nAn error occured!"
               "\nCheck your internet connection...exiting now :(")
        sys.exit(1)
    bday = json.loads(datafile.read())['birthday']
    datafile.close()

    bday = datetime.datetime.strptime(bday, '%m/%d/%Y')

    t = raw_input("\nEnter the time of the first post on your wall\n"
                  "(like 11:55, default is 11:45,enter d for default): ")
    t = "11:45" if t == 'd' else t
    t = t.split(':')

    wish = bday.replace(year=datetime.datetime.now().year,
                        hour=int(t[0]),
                        minute=int(t[1]))-datetime.timedelta(days=1)

    # create a unix timestamp from first post's time
    wish_timestamp = time.mktime(wish.timetuple())

    # multiquery to select actor_id, post_id, message and first_name of the
    # poster
    query = {'actors': ('SELECT actor_id,post_id,message FROM '
                        'stream WHERE source_id=me() AND created_time > '
                        '%s LIMIT %s') % (int(wish_timestamp), LIMIT),
             'names': ('SELECT first_name FROM user WHERE '
                       'uid IN (SELECT actor_id FROM #actors)')}

    urlstring = {'access_token': ACCESS_TOKEN,
                 'q': query}

    fullurl = "https://graph.facebook.com/fql"+'?'+urllib.urlencode(urlstring)

    # GET request since there's no data dictionary as second parameter
    res = urllib2.urlopen(fullurl)
    result = json.loads(res.read())
    res.close()

    # create a post_list and name_list because we need only post_id and name
    # to reply
    post_list = result['data'][0]['fql_result_set']
    name_list = result['data'][1]['fql_result_set']
    size = len(name_list)

    print ("\n%s friends posted on your timeline for your birthday!"
           " :)") % size

    # pack name and post_id into a dict and send it in a list
    post_data = [{'post_id': post_list[i]['post_id'],
                  'from': name_list[i]['first_name']
                  } for i in xrange(size)]

    return post_data


def reply_post(post_list):
    """
    reply_post(post_data)
    Creates a batch request of all the replies and sends it
    to the server the batch requests contain the post_id
    and the reply.
    """
    print ("\n\nHow would you like to reply?\nDefault reply is "
           "'Thank you [name] :)'\nWhen making your own reply "
           "use [name] to insert the name of the friend.\n")
    reply = raw_input("Enter your reply (enter d for default) : ")
    reply = 'Thank you [name] :)' if reply == 'd' else reply

    # creates a single batch request instead of HTTP requests for
    # each post
    batch = [{"method": "POST",
              "relative_url": str(item['post_id'] +
                                  "/comments?message=" +
                                  reply.replace('[name]',
                                                item['from']))}
             for item in post_list]

    post_data = urllib.urlencode({'access_token': ACCESS_TOKEN,
                                  'batch': repr(batch)})

    # POST request since post_data is supplied as second parameter
    dataf = urllib2.urlopen(ACCESS_URL, post_data)
    response_list = json.loads(dataf.read())
    dataf.close()

    count = 0
    for i in response_list:
        if i['code'] == 200:    # 200 is 'OK' response
            count += 1
    print "\n Successfully replied to %s posts :)" % count


if __name__ == "__main__":
    ACCESS_TOKEN = getaccesstoken()
    post_data_list = collect_data()
    reply_post(post_data_list)

