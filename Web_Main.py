from flask import Flask, request, jsonify


app = Flask(__name__)
@app.route('/api/data', methods=['POST'])
def handle_data():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    # Process the data (for demonstration, we'll just echo it back)
    processed_data = {
        "received": data,
        "message": "Data processed successfully"
    }
    return jsonify(processed_data), 200