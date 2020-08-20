from flask import Flask, request, jsonify
import json

app = Flask(__name__)
from dotenv import load_dotenv
import xmltodict
import requests

load_dotenv()

import os
import psycopg2

DATABASE_URL = os.environ['DATABASE_URL']
SUBTOKEN = os.getenv('SUB_SECRET')
APPURL = os.getenv('APPURL')


def dbtest():
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')

        cursor = conn.cursor()
        postgreSQL_select_Query = "select * from distributors"

        cursor.execute(postgreSQL_select_Query)
        print("Selecting rows from mobile table using cursor.fetchall")
        mobile_records = cursor.fetchall()

        print("Print each row and it's columns values")
        for row in mobile_records:
            print("Id = ", row[0], )
            print("Model = ", row[1])

    except (Exception, psycopg2.Error) as error:
        print("Error while fetching data from PostgreSQL", error)

    finally:
        # closing database connection.
        if (conn):
            conn.close()
            conn.close()
            print("PostgreSQL connection is closed")


def persist_sub(channelId):
    print("saving subscription of channel {}".format(channelId))


def persist_event(evt):
    print("persisting event")
    print("channel: {} - {}, videoid: {}, videotitle: {}".format(
        evt["name"], evt["channelId"], evt["videoId"], evt["videoTitle"]))

def send_sub_for_channel(channelId,mode,token):
    print("send sub for channel")
    url = "https://pubsubhubbub.appspot.com/subscribe"
    topicurl = "https://www.youtube.com/xml/feeds/videos.xml?channel_id={}"
    cburl = "{}/hook".format(APPURL)
    out_param = {
        "hub.mode": mode,
        'hub.topic': topicurl.format(channelId),
        'hub.callback': cburl,
        'hub.verify': "async",
        'hub.verify_token': token
    }
    headers = {}
    print("posting with params: {},\n headers: {}".format(out_param, headers))

    r = requests.post(url, data=out_param, headers=headers)
    return r

@app.route('/subscribe', methods=['POST'])
def sub():
    in_param = {
        "token": request.form.get('token'),
        "channelId": request.form.get('channelId'),
        "mode": request.form.get('mode')
    }
    print(in_param)
    if None not in [in_param[k] for k in in_param]:
        req = send_sub_for_channel(in_param["channelId"], in_param["mode"], in_param["token"])
        print(req.status_code)
        return "OK"
    else:
        return "NOTOK"


@app.route('/hook', methods=['GET'])
def registerhook():
    challenge, token, topic, mode = [request.args.get("hub.challenge"), request.args.get("hub.verify_token"),
                                     request.args.get("hub.topic"), request.args.get("hub.mode")]
    print("register hook called: \n mode : {}\n token: {}\n topic: {}".format(mode, token, topic))
    if None not in [mode, challenge]:
        if token == SUBTOKEN:
            channelId = topic.split("channel_id=")[1]
            print("verifying sub change of channel: {} with challenge {}".format(channelId, challenge))
            persist_sub(channelId)
            return challenge
        else:
            print("invalid or missing token")
            return "NOTOK"
    else:
        print('no missing mode, or challenge')
        return "OK"


@app.route('/hook', methods=['POST'])
def receivehook():
    body = request.get_data(cache=False, as_text=False, parse_form_data=False)
    print(
        "data to hook of type {}, length: {}, received: {}".format(request.content_type, request.content_length, body))

    content_json = json.loads(json.dumps(xmltodict.parse(body)))
    entry = content_json["feed"]["entry"]
    evt = {
        "name": entry["author"]["name"],
        "channelId": entry["yt:channelId"],
        "videoId": entry["yt:videoId"],
        "videoTitle": entry["title"]
    }

    persist_event(evt)
    return "OKAY"


@app.route('/getmsg/', methods=['GET'])
def respond():
    # Retrieve the name from url parameter
    name = request.args.get("name", None)
    # For debugging
    print(f"got name {name}")

    response = {}

    # Check if user sent a name at all
    if not name:
        response["ERROR"] = "no name found, please send a name."
    # Check if the user entered a number not a name
    elif str(name).isdigit():
        response["ERROR"] = "name can't be numeric."
    # Now the user entered a valid name
    else:
        response["MESSAGE"] = f"Welcome {name} to our awesome platform!!"

    # Return the response in json format
    return jsonify(response)


@app.route('/post/', methods=['POST'])
def post_something():
    param = request.form.get('name')
    print(param)
    # You can add the test cases you made in the previous function, but in our case here you are just testing the POST functionality
    if param:
        return jsonify({
            "Message": f"Welcome {name} to our awesome platform!!",
            # Add this option to distinct the POST request
            "METHOD": "POST"
        })
    else:
        return jsonify({
            "ERROR": "no name found, please send a name."
        })


# A welcome message to test our server
@app.route('/')
def index():
    return "<h1>Welcome to our server !!</h1>"


if __name__ == '__main__':
    # Threaded option to enable multiple instances for multiple user access support
    app.run(threaded=True, port=5000)
