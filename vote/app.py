from flask import Flask, request, jsonify, make_response, g
from redis import Redis
import os
import socket
import random
import json
import logging

option_a = os.getenv('OPTION_A', "Cats")
option_b = os.getenv('OPTION_B', "Dogs")
hostname = socket.gethostname()

app = Flask(__name__)

gunicorn_error_logger = logging.getLogger('gunicorn.error')
app.logger.handlers.extend(gunicorn_error_logger.handlers)
app.logger.setLevel(logging.INFO)

def get_redis():
    if not hasattr(g, 'redis'):
        g.redis = Redis(host="redis", db=0, socket_timeout=5)
    return g.redis

@app.route("/api/options", methods=['GET'])
def get_options():
    return jsonify({
        "option_a": option_a,
        "option_b": option_b,
        "hostname": hostname
    })

@app.route("/api/vote", methods=['POST'])
def vote():
    voter_id = request.cookies.get('voter_id')
    if not voter_id:
        voter_id = hex(random.getrandbits(64))[2:-1]

    data = request.get_json(silent=True)
    vote_choice = None
    if data and 'vote' in data:
        vote_choice = data['vote']
    else:
        vote_choice = request.form.get('vote')
    
    if vote_choice:
        redis = get_redis()
        app.logger.info('Received vote for %s', vote_choice)
        vote_data = json.dumps({'voter_id': voter_id, 'vote': vote_choice})
        redis.rpush('votes', vote_data)
        
    resp = make_response(jsonify({
        "success": True,
        "voter_id": voter_id,
        "vote": vote_choice
    }))
    resp.set_cookie('voter_id', voter_id)
    return resp

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80, debug=True, threaded=True)
