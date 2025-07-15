from flask import Flask, request, render_template_string
import openai
import os

app = Flask(__name__)
openai.api_key = os.environ["OPENAI_API_KEY"]

TEMPLATE = """
<!doctype html>
<html>
<head><title>Bio: {{name}}</title></head>
<body>
  <h1>{{name}} &mdash; {{school}}</h1>
  <pre style="white-space:pre-wrap">{{bio}}</pre>
</body>
</html>
"""

@app.route("/bio")
def bio():
    name   = request.args.get("name","")
    school = request.args.get("school","")
    prompt = f"""
Write me a concise but thorough scouting‐style summary of the player {name}, 
who just transferred to or committed to {school}. 
Include career highlights, key stats & metrics, and current projected role.
Cross‐reference publicly available data where possible.
"""
    resp = openai.ChatCompletion.create(
      model="gpt-4o-mini",
      messages=[{"role":"user","content":prompt}],
      temperature=0.7,
      max_tokens=500
    )
    bio_text = resp.choices[0].message.content
    return render_template_string(TEMPLATE, name=name, school=school, bio=bio_text)

if __name__=="__main__":
    app.run(debug=True, port=8000)
