from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    print(f"Webhook received: {data}")
    return jsonify({"status": "Received"}), 200

if __name__ == '__main__':
    app.run(port=5001, debug=True)
