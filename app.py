import time
import os
import datetime
import xmltodict
import psycopg2
from flask import Flask, request, jsonify, render_template, send_from_directory
import json
from dotenv import load_dotenv
from utils import check_user_yt, send_hook_bad_xml, handle_incoming_hook

app = Flask(__name__)

load_dotenv()

DATABASE_URL = os.environ['DATABASE_URL']
SUBTOKEN = os.getenv('SUB_SECRET')
APPURL = os.getenv('APPURL')
DC_WEBHOOK_URL = os.getenv('DC_WEBHOOK_URL')
YT_APIKEY = os.getenv('YT_APIKEY')

conn = psycopg2.connect(DATABASE_URL, sslmode='require')
conn.autocommit = True


@app.route('/subscribe', methods=['POST'])
def sub():
    from utils import send_sub_for_channel
    # send subscription request to pubhubsubbub
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
def register_hook():
    from dao import persist_sub
    challenge, token, topic, mode = [request.args.get("hub.challenge"), request.args.get("hub.verify_token"),
                                     request.args.get("hub.topic"), request.args.get("hub.mode")]
    print("register hook called: \n mode : {}\n token: {}\n topic: {}".format(mode, token, topic))

    lease_seconds = request.args.get("hub.lease_seconds")
    now = datetime.datetime.now()
    lease = now + datetime.timedelta(0, int(lease_seconds))
    print("now: %s lease: %s" % (now, lease))

    if None not in [mode, challenge]:
        if token == SUBTOKEN:
            channel_id = topic.split("channel_id=")[1]
            print("verifying sub change of channel: {} with challenge {}".format(channel_id, challenge))
            persist_sub(conn, channel_id, lease)
            return challenge
        else:
            print("invalid or missing token")
            return "NOTOK"
    else:
        print('no missing mode, or challenge')
        return "OK"


@app.route('/hook', methods=['POST'])
def receive_event():
    # receive updates from the hub
    body = request.get_data(cache=False, as_text=False, parse_form_data=False)
    print(
        "data to hook of type {}, length: {}, received: {}".format(request.content_type, request.content_length, body))
    try:
        from threading import Thread
        thread = Thread(target=handle_incoming_hook, kwargs={'conn': conn, 'body': body})
        thread.start()
        return "OKAY"
    except Exception as e:
        send_hook_bad_xml(body.decode())
        return "NOTOKAY"


@app.route('/list', methods=['GET'])
def list_subs():
    from dao import get_subs_data
    return jsonify(get_subs_data(conn))


# A welcome message to test our server
@app.route('/')
def index():
    from dao import get_subs_data
    subs = get_subs_data(conn)
    return render_template('main.html', results=subs)


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


if __name__ == '__main__':
    # Threaded option to enable multiple instances for multiple user access support
    app.run(threaded=True, port=5000)
