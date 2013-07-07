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
    print ("The script needs your ACCESS TOKEN.\n"
           "What would you like to do?\n"
           "1. Generate a new TOKEN.\n"
           "2. Supply one (if you know how to generate it).\n")

    choice = raw_input("Choice (1 or 2) ? :")
    if int(choice) == 2:
        access_token = raw_input("\nEnter the TOKEN string: ")
    else:
        print ("To generate your token the script needs access to your feeds"
               "and publishing\npermissions. Don't worry the script doesn't "
               "store anything or spam your wall!\nGo to the links which will"
               "open in your browser shortly and give the permissions\nto read"
               " your data, once you give that permission another link will "
               "open which \nhas your token, the token is a long string and "
               "looks something like this\nCAACEdEose0.......cBABKNtliuHS7.\n"
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
                  "(like 11:55, default is 11:45,enter d for default):")
    t = "11:45" if t == 'd' else t
    t = t.split(':')

    wish = bday.replace(year=datetime.datetime.now().year,
                        hour=int(t[0]),
                        minute=int(t[1]))-datetime.timedelta(days=1)

    fq = urllib.quote("SELECT post_id, actor_id, message,created_time "
                      "FROM stream WHERE source_id=me() AND filter_key="
                      "'others' LIMIT %s" % LIMIT)

    dataf = urllib2.urlopen(ACCESS_URL + "fql?q="+fq +
                            "&format=json&access_token="+ACCESS_TOKEN)
    post_data = json.loads(dataf.read())
    dataf.close()

    wish_timestamp = time.mktime(wish.timetuple())
    post_data['data'] = [x for x in post_data['data']
                         if x['created_time'] > wish_timestamp]

    dataf = urllib2.urlopen(ACCESS_URL+'me/feed?access_token='+ACCESS_TOKEN)
    post_from = json.loads(dataf.read())
    dataf.close()

    post_from['data'] = [x for x in
                         post_from['data'][:len(post_data['data'])+1]]
    from_dict = {x['id']: x['from']['name'] for x in post_from['data']}

    for i in post_data['data']:
        i['from'] = from_dict[i['post_id']]

    return post_data['data']


def reply_post(post_list):
    print ("\n\nHow would you like to reply?\nDefault reply is "
           "'Thank you [name] :)'\nWhen making your own reply "
           "use [name] to insert the name of the friend.\n")
    reply = raw_input("Enter your reply (enter d for default) : ")
    reply = 'Thank you [name] :)' if reply == 'd' else reply

    batch = [{"method": "POST",
              "relative_url": str(item['post_id'] +
                                  "/comments?message=" +
                                  reply.replace('[name]',
                                                item['from'].split()[0]))}
             for item in post_list]

    post_data = urllib.urlencode({'access_token': ACCESS_TOKEN,
                                  'batch': repr(batch)})
    print post_data
    dataf = urllib2.urlopen(ACCESS_URL, post_data)
    print json.loads(dataf.read())


if __name__ == "__main__":
    #ACCESS_TOKEN=getaccesstoken()
    post_data_list = collect_data()
    reply_post(post_data_list)

