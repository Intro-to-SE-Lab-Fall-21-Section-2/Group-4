from flask import Flask, render_template, redirect, url_for, request, session
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import smtplib, ssl
from email.mime.text import MIMEText
from imap_tools import MailBox, OR, AND
from flask import send_file
from flask import flash
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart

import imaplib
import email
from email.header import decode_header
import webbrowser
import os

app = Flask(__name__)
app.secret_key = "thisisasecretkey"
app.config['SECRET_KEY'] = 'C2HWGVoMGfNTBsrYQg8EcMrdTimkZfAb'

Bootstrap(app)


@app.route('/inbox')
def inbox():
    # account credentials
    # modify these to pass in from login page

    # create an IMAP4 class with SSL
    if "email" in session: # if user is logged in

        emailContentSend = [] #emailContent = [["test subject", "noone", "index.html"],["test subject 2", "still noone", "index.html"]]
        emailCount = 0

        if "searchTerm" in session:
            with MailBox('imap.gmail.com').login(session["email"], session["password"]) as mailbox:
                for msg in mailbox.fetch(AND(subject = session["searchTerm"]), reverse=True, limit = session["displayNum"]):
                    attatchCount = 0
                    for att in msg.attachments:
                        attatchCount += 1
                    emailContentSend.append([msg.subject, msg.from_, msg.date, msg.uid, attatchCount])
        else:
            with MailBox('imap.gmail.com').login(session["email"], session["password"]) as mailbox:
                for msg in mailbox.fetch(reverse=True, limit = session["displayNum"]):
                    attatchCount = 0
                    for att in msg.attachments:
                        attatchCount += 1
                    emailContentSend.append([msg.subject, msg.from_, msg.date, msg.uid, attatchCount])

        # close the connection and logout
        return render_template("inbox.html", email=emailContentSend)
    else: # user is not logged in
        return redirect(url_for("login"))

@app.route('/viewEmail/<emailUid>')
def viewEmail(emailUid):
    if "email" in session: # if user is logged in

        emailContentSend = [] #emailContent = [["test subject", "noone", "index.html"],["test subject 2", "still noone", "index.html"]]
        attachmentList = []
        with MailBox('imap.gmail.com').login(session["email"], session["password"]) as mailbox:
            #i = 0
            for msg in mailbox.fetch(AND(uid=emailUid)):
                for att in msg.attachments:
                    attachmentList.append(att.filename)
                emailContentSend.append([msg.subject, msg.from_, msg.reply_to, msg.date, msg.to, msg.html, msg.uid, attachmentList])

        return render_template("viewEmail.html", email=emailContentSend)

    else: # user is not logged in
        return redirect(url_for("login"))

@app.route('/downloadAttachments/<emailUid>')
def downloadAttachments(emailUid):
    counter = 0
    with MailBox('imap.gmail.com').login(session["email"], session["password"]) as mailbox:
        for msg in mailbox.fetch(AND(uid=emafilUid)):
            for att in msg.attachments:
                with open('C:/Users/colli/softwareLab/downloads/{}'.format(att.filename), 'wb+') as f:
                    f.write(att.payload)
                returnFileName = att.filename

    return redirect(url_for("downloadFile", fileName = returnFileName))

@app.route('/download/<fileName>')
def downloadFile (fileName):
    path = "C:/Users/colli/softwareLab/downloads/" + fileName
    #For windows you need to use drive name [ex: F:/Example.pdf]
    #path = "/Examples.pdf"
    return send_file(path, as_attachment=True)

@app.route('/')
def home():
    return redirect(url_for("inbox"))

@app.route('/login', methods=["POST","GET"])
def login():
    if request.method == "POST":
        session["email"] = request.form["email"]
        session["password"] = request.form["password"]
        session["displayNum"] = 6
        return redirect(url_for("inbox"))
    else:
        if "email" in session:
            return redirect(url_for("inbox"))
        else: # user is not logged in
            return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/search", methods=["POST","GET"])
def search():
    if request.method == "POST":
        if request.form["searchTerm"]:
            session["searchTerm"] = request.form["searchTerm"]
        else:
            flash("Please enter a search term before searching. <br>")

    return redirect(url_for("inbox"))

@app.route("/clearsearch")
def clearsearch():
    if "searchTerm" in session:
        session.pop('searchTerm')
        flash("Search terms cleared. <br>")
    else:
        flash("There was no search term entered. <br>")
    return redirect(url_for("inbox"))

@app.route("/delete/<emailUid>")
def delete(emailUid):
    with MailBox('imap.gmail.com').login(session["email"], session["password"]) as mailbox:
        mailbox.delete(emailUid)
    flash("Email deleted successfully. <br>")
    return redirect(url_for("inbox"))

@app.route("/showmore")
def showmore():
    session["displayNum"] += 2
    return redirect(url_for("inbox"))

@app.route("/showless")
def showless():
    if session["displayNum"] > 2:
        session["displayNum"] -= 2
    return redirect(url_for("inbox"))


@app.route("/compose/<emailUid>", methods=["POST","GET"])
@app.route("/compose", methods=["POST","GET"])
def compose(emailUid = -1):
    if request.method == "POST": # if form submitted




        # else: # no attachment

        smtp_ssl_host = 'smtp.gmail.com'
        smtp_ssl_port = 465
        # use username or email to log in

        # the email lib has a lot of templates
        # for different message formats,
        # on our case we will use MIMEText
        # to send only text
        message = MIMEMultipart()
        message['subject'] = request.form["subject"]
        message['from'] = session["email"]
        message['to'] = request.form["to"]
        message.attach(MIMEText(request.form["body"], 'plain'))

        uploaded_file = request.files['attachment']

        if uploaded_file.filename != '':
            fileLocation = "C:/Users/colli/softwareLab/uploads/" + uploaded_file.filename
            uploaded_file.save(fileLocation)

            with open(fileLocation, "rb") as attachment:
                # Add file as application/octet-stream
                # Email client can usually download this automatically as attachment
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
            encoders.encode_base64(part)

            # Add header as key/value pair to attachment part
            part.add_header(
                "Content-Disposition",
                f"attachment; filename= {fileLocation}",
            )

            # Add attachment to message and convert message to string
            message.attach(part)
            text = message.as_string()

        # we'll connect using SSL
        context = ssl.create_default_context()
        server = smtplib.SMTP_SSL(smtp_ssl_host, smtp_ssl_port, context=context)

        # to interact with the server, first we log in
        # and then we send the message
        server.login(session["email"], session["password"])
        server.sendmail(session["email"], request.form["to"], message.as_string())
        server.quit()

        return redirect(url_for("inbox"))
    else: # if form has not been yet submitted // initial loading
        if (emailUid == -1):
            emailContentSend = ['','']
        else:
            with MailBox('imap.gmail.com').login(session["email"], session["password"]) as mailbox:
                for msg in mailbox.fetch(AND(uid=emailUid)):
                    emailContentSend = ["RE" + msg.subject, msg.from_]

        return render_template("compose.html",email=emailContentSend)

@app.route("/forward/<emailUid>", methods=["POST","GET"])
def forward(emailUid):
    if request.method == "POST": # if form submitted

        with MailBox('imap.gmail.com').login(session["email"], session["password"]) as mailbox:
            for msg in mailbox.fetch(AND(uid=emailUid)):
                subject = "FW:" + msg.subject
                body = msg.html

        smtp_ssl_host = 'smtp.gmail.com'
        smtp_ssl_port = 465

        # the email lib has a lot of templates
        # for different message formats,
        # on our case we will use MIMEText
        # to send only text
        message = MIMEMultipart('alternative')
        message['subject'] = subject
        message['from'] = session["email"]
        message['to'] = request.form["forwardEmail"]

        message.attach(MIMEText(body, 'html'))

        # we'll connect using SSL
        server = smtplib.SMTP_SSL(smtp_ssl_host, smtp_ssl_port)
        # to interact with the server, first we log in
        # and then we send the message
        server.login(session["email"], session["password"])
        server.sendmail(session["email"], request.form["forwardEmail"], message.as_string())
        server.quit()
        flash("Email forwarded successfully.<br><br>")
        return redirect(url_for("viewEmail", emailUid = emailUid))
    else: # if form has not been yet submitted
        return redirect(url_for("login"))
