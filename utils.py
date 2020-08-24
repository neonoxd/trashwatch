from app import APPURL
import requests


#requests
def send_sub_for_channel(channel_id, mode, token):
    print("send sub for channel")
    url = "https://pubsubhubbub.appspot.com/subscribe"
    topicurl = "https://www.youtube.com/xml/feeds/videos.xml?channel_id={}"
    cburl = "{}/hook".format(APPURL)
    out_param = {
        "hub.mode": mode,
        'hub.topic': topicurl.format(channel_id),
        'hub.callback': cburl,
        'hub.verify': "async",
        'hub.verify_token': token
    }
    headers = {}
    print("posting with params: {},\n headers: {}".format(out_param, headers))

    r = requests.post(url, data=out_param, headers=headers)
    return r