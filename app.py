from flask import Flask, session, redirect, url_for, escape, request, render_template
from flask.ext.mongoengine import MongoEngine
from pbkdf2 import crypt
from models import *
import logging, datetime, math, os

#SSL for future security maybe?
'''
import ssl
context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
context.load_cert_chain('yourserver.crt', 'yourserver.key')
'''

app = Flask(__name__)
app.debug = False
app.config['MONGODB_SETTINGS'] = {
    'db': 'dogebook',
    'host': '127.0.0.1',
    'port': 27017
}
db = MongoEngine(app)
app.logger.setLevel(logging.INFO)  # use the native logger of flask

# secret app key. keep this really secret:
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'

#Index route
@app.route('/')
def index():
    if 'userid' in session:
        return redirect('/posts/0')
    return render_template("index.html", data={})

#New post route
@app.route('/newpost', methods=['POST'])
def new_post():
    if 'userid' in session and request.method == 'POST':
        user = User.objects(id=session['userid']).first()
        postContent = request.form['inputText']
        post = Post(content=postContent, author=user).save()
    return redirect(url_for('index'))

#Add friend by userid route
@app.route('/add_friend/<userid>')
def add_friend(userid=None):
    if 'userid' in session:
        user = User.objects(id=session['userid']).first()
        #print user.friends.__class__.__name__
        friend = User.objects(id=userid).first()
        if friend not in user.friends:
            user.friends.append(friend)
            user.save()
        return redirect('/profile/'+session["userid"])
    return redirect('/profile/'+session["userid"])

#Remove friend by userid route
@app.route('/remove_friend/<userid>')
def remove_friend(userid=None):
    if 'userid' in session:
        user = User.objects(id=session['userid']).first()
        #print user.friends.__class__.__name__
        friend = User.objects(id=userid).first()
        if friend in user.friends:
            user.friends.remove(friend)
            user.save()
        return redirect(url_for('index'))
    return redirect(url_for('index'))

#Friend search route
@app.route('/find_friends', methods=['GET', 'POST'])
def find_friends():
    if 'userid' in session:
        user = User.objects(id=session['userid']).first()
        results = []
        if request.method == 'POST':
            somename = request.form['inputName']
            results = User.objects(name__contains=somename)
        return render_template("find_friends.html", data={"user":user, "results":results, "nresults":len(results)})
    return redirect(url_for('index'))

#Get a page of posts for your current user
@app.route('/posts/<page>')
def posts_page(page=0):
    if 'userid' in session:
        page = int(page)
        posts_per_page = 10
        user = User.objects(id=session['userid']).first()
        #print user.friends
        #User.objects.get(id='55a51d434c149d1f60daec89') #lookup by id example
        #print "Wat?"
        current_post = page * posts_per_page
        posts_full = Post.objects(db.Q(author__in = user.friends) | db.Q(author = user)).order_by('-datetime')
        page_count = int(math.ceil(posts_full.count()/10))
        page_count = min(page_count,10)
        posts = posts_full.skip(current_post).limit(10)
        comment_counts = []
        for post in posts:
            comment_counts.append(len(post.comments))
        next_page = page+1
        if next_page > page_count:
            next_page = page_count
        prev_page = page-1
        if prev_page < 0:
            prev_page = 0
        #print posts
        return render_template("feed.html", data={"prev_page": prev_page, "currpage":page, "next_page":next_page, \
            "page_count":page_count, "user":user, "posts":posts, "comment_counts":comment_counts})
    return redirect(url_for('index'))

#Get a single post by id (And view comments)
@app.route('/post/<postid>')
def post_id(postid=None):
    if 'userid' in session:
        post = Post.objects(id=postid).first()
        user = User.objects(id=session['userid']).first()
        comments = post.comments
        comments = sorted(comments, key=lambda r: r.datetime, reverse=True)[:15]
        return render_template("single_post.html", data={"user":user, "post":post, "comments":comments})
    return redirect(url_for('index'))
    
#Delete a user by id
@app.route('/delete_user/<userid>')
def delete_user_id(userid=None):
    if 'userid' in session: #My userid
        user = User.objects(id=session['userid']).first()
        if user.username == "Jacob@jacob.com":
            user = User.objects(id=session['userid']).first()
            targetUser = User.objects(id=userid).first()
            posts = Post.objects(author=targetUser)
            posts.delete()
            targetUser.delete()
        return redirect(url_for('index'))
    return redirect(url_for('index'))

#Delete a post by id
@app.route('/post/<postid>/delete')
def delete_post_id(postid=None):
    if 'userid' in session:
        user = User.objects(id=session['userid']).first()
        post = Post.objects(id=postid).first()
        if(post.author == user): #Actually delete the post here
            post.delete()
        return redirect(url_for('index')) #Ultimately redirect
    return redirect(url_for('index'))

#Add comment to post by id
@app.route('/post/<postid>/add_comment', methods=['POST'])
def comment_post_id(postid=None):
    if request.method == 'POST':
        if 'userid' in session:
            user = User.objects(id=session['userid']).first()
            post = Post.objects(id=postid).first()
            if user in post.author.friends or post.author == user: #Actually add comment here
                print "Adding comment"
                comment = Comment(content=request.form['inputText'],author=user).save()
                post.comments.append(comment)
                post.save()
        return redirect('/post/'+str(post.id)) #Ultimately redirect
    return redirect(url_for('index'))

#Log in to the app
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        someusername = request.form['inputEmail']
        alleged_password = request.form['inputPassword']
        user = User.objects(username=someusername).first()
        if user != None and user.password == crypt(alleged_password, user.password):
            session['userid'] = str(user.id)
            return redirect(url_for('index'))
        return render_template('login.html', data={"message":"Wrong email or password"})
    else:
        if 'userid' in session:
            return render_template('error.html', data={"error":"You're already logged in..."})
        else:
            return render_template('login.html', data={})

#Create an account
@app.route('/create_account', methods=['GET', 'POST'])
def create_account():
    if request.method == 'POST':
        name = request.form['inputName']
        someemail = request.form['inputEmail']
        pwhash = crypt(request.form['inputPassword'])
        count = User.objects(username=someemail).count()
        if(count == 0):
            user = User(username=someemail, password=pwhash, name=name).save()
            session['userid'] = str(user.id)
            return redirect(url_for('index'))
        else:
            return render_template('create_account.html', data={"message":"Sorry, that email is already taken."})
    else:
        if 'userid' in session:
            return render_template('error.html', data={"error":"You're already logged in. Please log out to create a new account."})
        else:
            return render_template('create_account.html')

#Log out of app
@app.route('/logout')
def logout():
    # remove the username from the session if it's there
    session.pop('userid', None)
    return redirect(url_for('index'))

#Redirect for supporting cool url scheme with convenience wrapped
@app.route('/profile')
def profile():
    if 'userid' in session:
        return redirect('/profile/'+session['userid'])
    return redirect(url_for('index'))

#Go to profile by id
@app.route('/profile/<profileid>')
def profile_id(profileid=None):
    if 'userid' in session:
        user = User.objects(id=profileid).first()
        currentuser = User.objects(id=session["userid"]).first()
        userid = str(user.id)
        return render_template("profile.html", data={"user":user, "friends":user.friends, "currentuser":currentuser, "userid":userid})
    return redirect(url_for('index'))

#Edit profile by id. Only your own :)
@app.route('/profile/<profileid>/edit', methods=['GET', 'POST'])
def edit_profile_id(profileid=None):
    if 'userid' in session:
        if request.method == 'POST':
            if session['userid'] == profileid:
                user = User.objects(id=session['userid']).first()
                user.update(name=request.form['inputName'], tagline=request.form['inputTagline'],city=request.form['inputCity'],state=request.form['inputState'],bio=request.form['inputBio'])
                return redirect('/profile/'+profileid)
            else:
                print "Hackerrzzz"
        else:
            user = User.objects(id=session['userid']).first()
            return render_template("edit_profile.html", data={"user":user})
    else:
        return redirect(url_for('index'))

#Handle some errors
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

#Handle some more errors
@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 404

#Start the app
if (__name__ == '__main__'):
    app.run(host=os.getenv('IP', '0.0.0.0'),port=int(os.getenv('PORT', 8080)))
	#app.run(host="127.0.0.1", port=8080, ssl_context=context) #No way to do ssl yet