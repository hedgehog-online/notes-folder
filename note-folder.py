#!/usr/bin/env python3
from flask import Flask, request, render_template, send_from_directory, escape
from natsort import natsorted
import random
import os
import subprocess
import argparse
app = Flask(__name__)

parser = argparse.ArgumentParser(description="Display folders as notes")
parser.add_argument("--path", type=str, default=os.getcwd())
parser.add_argument("--randomize", action='store_true')
args = parser.parse_args()

def shuffle(array):
    a = array.copy()
    random.shuffle(a)
    return a

sort_fn = natsorted
if args.randomize:
    sort_fn = shuffle

root_path = os.path.abspath(args.path)


def proper_path(item):
    # unsanitized evil
    full_path = os.path.abspath(os.path.join(root_path, item))
    print(full_path)
    if not full_path.startswith(root_path):
        raise Exception("bad path")
    return full_path


@app.route("/serve/<path:path>")
def serve(path):
    print(path)
    # return app.send_static_file(proper_path(path))
    return send_from_directory(root_path, path)


@app.route("/open")
def open_item():
    item = request.args.get("item", default=".", type=str)
    reveal_only = request.args.get("reveal_only", default=False, type=bool)
    print(reveal_only)
    full_path = proper_path(item)

    cmd = ["open", full_path]
    if reveal_only:
        cmd.append("-R")
    subprocess.call(cmd)

    return ""


@app.route("/")
def root():
    return render_template("index.html", title=os.path.basename(root_path), body=render(root_path))


def render(path=None):
    short_path = None
    if path is None:
        path = root_path
        short_path = "/"
    else:
        short_path = proper_path(path)[len(root_path)+1:]

    display_path = os.path.basename(path)

    type = "binary"
    buttons = [("Show in Finder", f"""openItem('{short_path}', true)"""),
               ("Open", f"""openItem('{short_path}')""")]
    content = ""

    if os.path.isdir(path):
        type = "folder"
        display_path += "/"
        buttons = [("Show in Finder", f"""openItem('{short_path}', true)""")]
        for item in sort_fn(os.listdir(path)):
            if item[0] == ".":  # skip hidden
                continue
            content += render(os.path.join(path, item))
    else:
        _, extension = os.path.splitext(display_path)
        if extension in [".jpg", ".png", ".gif"]:
            type = "image"
            serve_path = os.path.join("/serve/", short_path)
            content = f"""<a href="{serve_path}"><img src="{serve_path}"></a>"""
        elif extension in [".md", ".txt"]:
            type = "text"
            with open(path) as file:
                content = escape(file.read())

    return render_template("item.html", type=type, name=display_path, buttons=buttons, content=content)


if __name__ == "__main__":
    app.run()
