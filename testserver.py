import socketio
from aiohttp import web
from src.cheaserEncrypt import encrypt
from src.cheaserDecrypt import decrypt
import src.rsa as rsa
import json

sio = socketio.AsyncServer(async_mode='aiohttp')

app = web.Application()
sio.attach(app)

@sio.on("connect")
def connect(sid, environ):
    print("Yeni bağlantı kuruldu:", sid)

@sio.on("disconnect")
def disconnect(sid):
    print("Bir bağlantı kesildi:", sid)

@sio.on("newMessage")
async def newMessage(sid, data):
    try:
        owner = data["username"]
    except:
        data["username"] = "[KULLANICI ADI HATASI]"
        print("[UYARI]: Bir istemcinin gönderdiği mesaj isteğinde kullanıcı adı bulunamadı.")
    message = data["message"]
    print("{0} adlı kullanıcı yeni bir mesaj gönderdi. Kullanıcı SID'si: {1}".format(owner, sid))

    with open("./database.json", "r+", encoding="utf-8") as f:
        cache = json.load(f)
        cache["messageHistory"].append("{0}: {1}".format(owner, message))
        f.close()
    with open("./database.json", "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=4)
        f.close()
    await sendHistory()

@sio.on("showMessageHistory")
async def sendHistory(sid=None):
    with open("./database.json", "r+", encoding="utf-8") as f:
        cache = json.load(f)
        f.close()
    await sio.emit("messageHistoryChanged", {"messageHistory": cache["messageHistory"]})

@sio.on("newUser")
async def newUser(sid, data):
    with open("./database.json", "r+", encoding="utf-8") as f:
        cache = json.load(f)
        cache["messageHistory"].append("[SUNUCU]: {0} adlı kullanıcı odaya giriş yaptı.".format(data["username"]))
        f.close()
    with open("./database.json", "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=4)
        f.close()
    await sendHistory()

if __name__ == "__main__":
    web.run_app(app)