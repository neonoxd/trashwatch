import requests


def send_sub_for_channel(channel_id, mode, token):
    from app import APPURL
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


def send_hook_bad_xml(body):
    from app import DC_WEBHOOK_URL
    content = {
        "content": "Unparseable XML received from hub ```xml\n{}```".format(body)
    }
    r = requests.post(DC_WEBHOOK_URL, data=content, headers={})
    print(r.status_code)
    return r


def check_user_yt(channel_id):
    from app import YT_APIKEY
    url = "https://www.googleapis.com/youtube/v3/search?part=snippet&channelId={0}&type=video&eventType=live&key={1}"
    req = requests.get(url=url.format(channel_id, YT_APIKEY))
    jsondata = req.json()
    print(jsondata)
    if req.status_code != 200:
        print("request returned with code: {}, \n response json: {}", req.status_code, jsondata)
        return {"islive": False}
    try:
        is_live = jsondata["items"][0]["snippet"]["liveBroadcastContent"] == "live"
        thumbnail = jsondata["items"][0]["snippet"]["thumbnails"]["high"]["url"]
        title = jsondata["items"][0]["snippet"]["title"]
        video_id = jsondata["items"][0]["id"]["videoId"]

        return {"islive": is_live, "thumbnail": thumbnail, "title": title, "video_id": video_id}
    except Exception as e:
        return {"islive": False}
