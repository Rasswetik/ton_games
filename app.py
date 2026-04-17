from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/market')
def market():
    return render_template('market.html')

@app.route('/crafts')
def crafts():
    return render_template('crafts.html')

@app.route('/profile')
def profile():
    return render_template('profile.html')

@app.route('/bot')
def bot():
    return render_template('bot.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)