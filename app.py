from flask import Flask, request, jsonify
import atoma
import json
app = Flask(__name__)

with open('dummy.json', 'r', encoding="utf8") as file:
    dummy = json.loads(file.read())

@app.route('/getchannel/',methods=['GET'])
def test():
    return dummy

@app.route('/hook/',methods=['GET'])
def registerhook():
    challenge = request.args.get("hub.challenge")
    print(request.stream.read())
    if challenge is None:
        return "OK"
    else:
        print("verifying with challenge {}".format(challenge))
        return challenge

@app.route('/hook/',methods=['POST'])
def receivehook():
    body = request.get_data()
    print("data to hook received: {}".format(body))
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
            "METHOD" : "POST"
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