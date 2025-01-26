"""
Requirements:
- Flask==3.1.0
"""
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/callback', methods=['GET'])
def callback():
	code = request.args.get('code')
	state = request.args.get('state')
	
	if code:
		# Process the OAuth callback here
		return jsonify({'status': 'success', 'code': code, 'state': state})
	else:
		return jsonify({'status': 'error', 'message': 'No code provided'}), 400

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=8080, debug=True)
