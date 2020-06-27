from flask import Flask,render_template

app = Flask(__name__)

@app.route("/")
def index():
    title="Flask Site"
    name="Rizvan"
    junkdata="just pushing extra data to understand"
    return render_template("index.html",title=title,name=name,data=junkdata)

@app.route("/about/")
def about():
    return "Hi I am Rizvan. I am a web developer"


app.run(debug=True)
