import eml_parser
import sys
import os
import json
import base64
from datetime import datetime

def json_serial(obj):
  if isinstance(obj, datetime):
      serial = obj.isoformat()
      return serial

messages = map(lambda f: os.path.join(sys.argv[1], f), filter(lambda f: f.endswith(".eml"), os.listdir(sys.argv[1])))

posts = {}

ep = eml_parser.EmlParser(include_attachment_data=True, include_raw_body=True)

for message_file in messages:
    with open(message_file, 'rb') as eml_file:
        raw_email = eml_file.read()

    print(f"Parsing {message_file}...")
    eml = ep.decode_email_bytes(raw_email)

    post_date = eml["header"]["date"].strftime("%Y-%m-%d_%H-%M-%S")

    message_data = {
        "date": post_date,
        "subject": eml["header"]["subject"],
        "body": next(filter(lambda body: body["content_type"] == "text/plain", eml["body"]))["content"].strip(),
        "attachments": [],
    }

    for index, attachment in enumerate(eml["attachment"]):
        content = base64.b64decode(attachment["raw"])
        extension = attachment.get("extension", "bin")
        if extension not in ["jpg", "jpeg", "png"]:
            if content[0:3] == bytes([0xFF, 0xD8, 0xFF]):
                extension = "jpg"
            elif content[0:5] == bytes([0x25, 0x50, 0x44, 0x46, 0x2D]):
                extension = "pdf"
            else:
                raise ValueError("Invalid attachment type")
        attachment_path = os.path.join("attachments", f"{post_date}_{index}.{extension}")
        with open(attachment_path, "wb") as attachment_file:
            attachment_file.write(content)
        message_data["attachments"].append(attachment_path)

    print(f"{message_data['date']}: {message_data['subject']} - {len(message_data['attachments'])} files")

    if post_date in posts:
        raise KeyError("Date already exists")

    posts[post_date] = message_data

with open("posts.json", "w") as posts_file:
    json.dump(posts, posts_file, indent=2)
