from flask import Flask, render_template, request, jsonify, session
import os


from avocado_small.query_engine import rag_query as rag_query_small
from avocado_large.query_engine import rag_query as rag_query_large

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "defaultsecret")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/history', methods=['GET'])
def history():
    return jsonify(session.get('chat_history', []))

@app.route('/clear_history', methods=['POST'])
def clear_history():
    session.pop('chat_history', None)
    return jsonify({"status": "cleared"})

@app.route('/ask', methods=['POST'])
def ask_large():
    return process_query(rag_query_large)

@app.route('/ask-small', methods=['POST'])
def ask_small():
    return process_query(rag_query_small)

def process_query(rag_function):
    data = request.get_json()
    user_query = data.get('query')

    if 'chat_history' not in session:
        session['chat_history'] = []

    try:
        answer = rag_function(user_query, session['chat_history'])
        session['chat_history'] = answer['history']
        return jsonify({'response': answer['reply']})
    except Exception as e:
        return jsonify({'response': f"❌ Error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
