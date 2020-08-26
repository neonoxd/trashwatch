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


def handle_incoming_hook(conn, body):
    from dao import persist_event
    import json
    import xmltodict
    import time
    content_json = json.loads(json.dumps(xmltodict.parse(body)))
    if "entry" in content_json["feed"]:
        entry = content_json["feed"]["entry"]
        evt = {
            "name": entry["author"]["name"],
            "channelId": entry["yt:channelId"],
            "videoId": entry["yt:videoId"],
            "videoTitle": entry["title"],
            "type": "video"
        }
        print("waiting for youtube to catch up...")  # because pubsubhubbub is faster than yt's own api
        time.sleep(30)
        yt_json = check_user_yt(evt["channelId"])
        if "islive" in yt_json and yt_json["islive"]:
            evt["type"] = "live"
            evt["videoTitle"] = yt_json["title"]
            evt["videoId"] = yt_json["video_id"]
        persist_event(conn, evt)
    elif "at:deleted-entry" in content_json["feed"]:
        del_entry = content_json['feed']['at:deleted-entry']
        print("deleted, vid id: {}, when: {}, channel: {}"
              .format(del_entry['@ref'].split(":")[2], del_entry['@when'],
                      del_entry['at:by']['uri'].split("channel/")[1]))
    else:
        send_hook_bad_xml(body.decode())
