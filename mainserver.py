#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
!              Şifreli Mesajlaşma Uygulaması - Sunucu
"""

import socketio #? İstemciyle iletişime geçmemizi sağlayan modül
from aiohttp import web #? Ağ içinde sunucunun yayın yapmasını sağlayan modül
from src.cheaserDecrypt import decrypt #? Sezar yöntemiyle şifrelenmiş metinlerin şifresini çözen fonksiyon
import src.rsa as rsa #? RSA şifrelemede ve şifre çözme işlemlerinde kullanılacak olan modül
import json #? Veritabanını yönetmeyi kolaylaştıran, ayrıca JSON dilindeki veriyi Python diline çeviren modül

"""
? Sunucu burada yapılandırılır.
? Burada ayrıca sunucunun asenkron modda çalışacağı ve aiohttp üzerinden ağa yayın yapacağı belirtilir.
? Burada asenkron modu kullanmamızın sebebi ağa yayın yapan aiohttp modülünün asenkron bir yapıda olmasıdır.
"""
sio = socketio.AsyncServer(async_mode="aiohttp")

app = web.Application() #? Ağa yayın yapacak sunucu bileşeni hazırlanır.
sio.attach(app) #? Sunucumuz yayın bileşenine bağlanır ve böylece sunucu istek gönderebilir veya alabilir.

ADMINPASSWORD = "ADMIN"

@sio.on("newMessage")
async def newMessage(sid, data):
    """
    ? Kullanıcı yeni mesaj gönderdiğinde bu fonksiyon tetiklenir.
    """
    try:
        owner = data["username"]
    except:
        owner = "[KULLANICI ADI HATASI]"
        data["username"] = "[KULLANICI ADI HATASI]"
        print("[UYARI]: Bir istemcinin gönderdiği mesaj isteğinde kullanıcı adı bulunamadı.")
    print(data["message"], "şifreli")

    """
    ? Mesajın şifresi bu bölümde çözülür.
    ? Eğer istemciye başka bir şifreleme metodu eklendiyse çözücü modeli aşağıdaki hiyerarşiye uygun eklenmelidir.
    """
    if data["encryptType"] == "cheaser":
        message = decrypt(data["message"], data["number"])
    elif data["encryptType"] == "rsa":
        print(data["n"], "n")
        print(data["e"], "e")
        print(data["d"], "d")
        message = rsa.SifreCoz(data["message"], data["n"], data["e"], data["d"])

    print("{0} adlı kullanıcı yeni bir mesaj gönderdi. Kullanıcı SID'si: {1}".format(owner, sid))
    print("Mesaj:", message)

    splittedMessage = message.split(" ")

    if splittedMessage[0] == "!temizle": #? Yeni mesajın geçmiş temizleme komutu olup olmadığı kontrol edilir.
        try:
            if splittedMessage[1] == ADMINPASSWORD: #? Komutun yanında verilen şifrenin doğru olup olmadığı kontrol edilir.
                await clearHistory() #? Geçmiş temizleme komutu çağırılır.
        except:
            pass
    else:
        finalMessage = "<font color=\"{0}\">{1}:</font> {2}<br>".format(data["color"], owner, message)

        with open("./database.json", "r+", encoding="utf-8") as f: #? Veritabanından veriler alınır...
            cache = json.load(f)
            cache["messageHistory"].append(finalMessage)
            f.close()
        with open("./database.json", "w", encoding="utf-8") as f: #? ...ve içine yeni mesaj konularak veritabanı kaydedilir.
            json.dump(cache, f, indent=4)
            f.close()
        await sendHistory(username=owner) #? Şifreli mesajı gönderecek fonksiyon tetiklenir.

async def sendHistory(username=""):
    """
    ? Yeni mesaj bu fonksiyon aracılığı ile tüm kullanıcılara gönderilir.
    """
    with open("./database.json", "r+", encoding="utf-8") as f:
        cache = json.load(f)
        f.close()
    
    """
    ? Mesajın gövenliği için bu kısımda mesajımız RSA yöntemi ile şifrelenir.

    ! ÖNEMLİ NOT: RSA yöntemindeki d anahtarının açık bir şekilde verilmesi kesinlikle güvenli değildir.
    ! Sadece öğrenme ortamında modülün nasıl çalıştığının rahat görülebilmesi için böyle bir kullanım yapılmıştır.
    ! d anahtarını bir yetkilendirme yoluyla şifreli olarak vermeniz tavsiye edilir.
    """
    encryptedText, n, e, d = rsa.Sifrele(cache["messageHistory"][-1])
    await sio.emit("messageHistoryChanged", {"messageHistory": encryptedText, "n": n, "e": e, "d": d, "username": username})

@sio.on("newUser")
async def newUser(sid, data):
    """
    ? Yeni kullanıcı sunucuya giriş yaptığında kullanıcıya karşılama metni bu fonksiyon ile hazırlanır.
    """
    with open("./database.json", "r+", encoding="utf-8") as f:
        cache = json.load(f)
        cache["messageHistory"].append("<font color=\"#F44242\">[SUNUCU]:</font> <font color=\"{0}\">{1}</font> adlı kullanıcı odaya giriş yaptı.<br>Not: Beğenmediyseniz kullanıcı renginizi <i><u>!renkdeğiştir [RENK]</i></u> komutuyla değiştirebilirsiniz.<br>".format(data["color"], data["username"]))
        f.close()
    with open("./database.json", "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=4)
        f.close()
    await sendHistory(username=data["username"])

async def clearHistory():
    """
    ? Geçmiş temizleme komutunu gönderen fonksiyondur.
    """
    print("SUNUCU: Geçmiş temizleniyor...")
    with open("./database.json", "r+", encoding="utf-8") as f:
        cache = json.load(f)
        cache["messageHistory"].append("!clearHistory")
        f.close()
    with open("./database.json", "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=4)
        f.close()
    await sendHistory(username="SUNUCU")

if __name__ == "__main__":
    web.run_app(app) #? Uygulamanın yerel ağa yayın yapması sağlanır.
