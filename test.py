from flask import Flask, render_template, redirect, url_for, request, session
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import smtplib, ssl
from email.mime.text import MIMEText

import imaplib
import email
from email.header import decode_header
import webbrowser
import os

app = Flask(__name__)
app.secret_key = "thisisasecretkey"
app.config['SECRET_KEY'] = 'C2HWGVoMGfNTBsrYQg8EcMrdTimkZfAb'

Bootstrap(app)

def clean(text):
    # clean text for creating a folder
    return "".join(c if c.isalnum() else "_" for c in text)

@app.route('/inbox')
def inbox():
    # account credentials
    # modify these to pass in from login page

    # create an IMAP4 class with SSL
    if "email" in session: # if user is logged in
        imap = imaplib.IMAP4_SSL("imap.gmail.com")
        # authenticate
        imap.login(session["email"], session["password"])
        status, messages = imap.select("INBOX")

        if "searchTerm" in session:
            status, messages = imap.search(None,f'(SUBJECT "{session["searchTerm"]}")')


        # total number of emails
        messages = int(messages[0])
        session["totMessages"] = messages

        # code to search inbox
        # selected_mails = mail.search(None, '(FROM "noreply@kaggle.com")')

        emailContentSend = []
        #emailContent = [["test subject", "noone", "index.html"],["test subject 2", "still noone", "index.html"]]
        j = 0
        for i in range(messages, messages-session["displayNum"], -1):
            # fetch the email message by ID
            res, msg = imap.fetch(str(i), "(RFC822)")
            for response in msg:
                if isinstance(response, tuple):
                    # parse a bytes email into a message object
                    msg = email.message_from_bytes(response[1])
                    # decode the email subject
                    subject, encoding = decode_header(msg["Subject"])[0]
                    if isinstance(subject, bytes) and encoding:
                        # if it's a bytes, decode to str
                        subject = subject.decode(encoding)
                    # decode email sender
                    From, encoding = decode_header(msg.get("From"))[0]
                    if isinstance(From, bytes):
                        From = From.decode(encoding)

                    # if the email message is multipart
                    if msg.is_multipart():
                        # iterate over email parts
                        for part in msg.walk():
                            # extract content type of email
                            content_type = part.get_content_type()
                            content_disposition = str(part.get("Content-Disposition"))
                            try:
                                # get the email body
                                body = part.get_payload(decode=True).decode()
                            except:
                                pass
                            if content_type == "text/plain" and "attachment" not in content_disposition:
                                # print text/plain emails and skip attachments
                                # body
                                string = "<i>Body</i></br>"
                            elif "attachment" in content_disposition:
                                # download attachment
                                filename = part.get_filename()
                                if filename:
                                    folder_name = clean(subject)
                                    if not os.path.isdir(folder_name):
                                        # make a folder for this email (named after the subject)
                                        os.mkdir(folder_name)
                                    filepath = os.path.join(folder_name, filename)
                                    # download attachment and save it
                                    open(filepath, "wb").write(part.get_payload(decode=True))
                    else:
                        # extract content type of email
                        content_type = msg.get_content_type()
                        # get the email body
                        body = msg.get_payload(decode=True).decode()
                    if content_type == "text/html":
                        # if it's HTML, create a new HTML file and open it in browser
                        folder_name = clean(subject)
                        filepath = os.path.join("templates", f"{folder_name}.html")
                        # write the file
                        open(filepath, "w").write(body)
                        # open in the default browser
                        ## webbrowser.open(filepath)
                    appendList = [subject, From, folder_name]
                    emailContentSend.append(appendList)

        # close the connection and logout
        imap.close()
        imap.logout()

        j+=1
        return render_template("inbox.html", email=emailContentSend)
    else: # user is not logged in
        return redirect(url_for("login"))

@app.route('/email/<email>')
def view_email(email):
    return f"Unable to render {email}."

@app.route('/')
def home():
    return redirect(url_for("inbox"))

@app.route('/login', methods=["POST","GET"])
def login():
    if request.method == "POST":
        session["email"] = request.form["email"]
        session["password"] = request.form["password"]
        session["displayNum"] = 2
        session["inboxView"] = "INBOX" # sets default view to inbox
        return redirect(url_for("inbox"))
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/search", methods=["POST","GET"])
def search():
    if request.method == "POST":
        session["searchTerm"] = request.form["searchTerm"]

    return redirect(url_for("inbox"))

@app.route("/showmore")
def showmore():
    session["displayNum"] += 2
    return redirect(url_for("inbox"))

@app.route("/showless")
def showless():
    session["displayNum"] -= 2
    return redirect(url_for("inbox"))

@app.route("/showSent")
def viewSent():
    session["search"] = "SENT"
    return redirect(url_for("inbox"))

@app.route("/showInbox")
def viewInbox():
    session["inboxView"] = "INBOX"
    return redirect(url_for("inbox"))

@app.route("/compose", methods=["POST","GET"])
def compose():
    if request.method == "POST": # if form submitted

        smtp_ssl_host = 'smtp.gmail.com'
        smtp_ssl_port = 465
        # use username or email to log in

        # the email lib has a lot of templates
        # for different message formats,
        # on our case we will use MIMEText
        # to send only text
        message = MIMEText(request.form["body"])
        message['subject'] = request.form["subject"]
        message['from'] = session["email"]
        message['to'] = request.form["to"]

        # we'll connect using SSL
        server = smtplib.SMTP_SSL(smtp_ssl_host, smtp_ssl_port)
        # to interact with the server, first we log in
        # and then we send the message
        server.login(session["email"], session["password"])
        server.sendmail(session["email"], request.form["to"], message.as_string())
        server.quit()

        return redirect(url_for("inbox"))
    else:
        return render_template("compose.html")
