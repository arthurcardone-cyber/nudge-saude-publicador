"""Robô de publicação da @nudge.saude (Instagram API com login do Instagram).

Roda no GitHub Actions a cada 20 minutos. Para cada item de agenda.json cujo horário já chegou
(e que não está em publicados.json), cria o conteúdo no Instagram e publica.

Tipos:
  imagem     1 JPEG no grid
  carrossel  2 a 10 JPEGs no grid
  reel       1 vídeo; "grid": true mostra no grid (com "capa"), false só na aba de reels

Segredos (GitHub > Settings > Secrets):
  IG_TOKEN      token de acesso gerado no painel da Meta (só na primeira vez)
  IG_TOKEN_KEY  senha que cifra o token renovado em token.enc
Uso local:
  python publicar.py --conferir    mostra o que está agendado e testa se os arquivos estão no ar (não publica)
"""
import json, os, subprocess, sys, time, urllib.parse, urllib.request
from datetime import datetime, timedelta, timezone

API = "https://graph.instagram.com/v23.0"   # trocado em detecta() se a chave for do tipo Facebook
IG_USER_ID = os.environ.get("IG_USER_ID", "17841473088119766")  # @nudge.saude
TIPO = "instagram"
BASE = os.environ.get("MIDIA_BASE", "https://arthurcardone-cyber.github.io/nudge-saude-publicador/")
AQUI = os.path.dirname(os.path.abspath(__file__))
ATRASO_MAX = timedelta(hours=12)  # não publica nada que passou do horário há mais de 12 h (evita enxurrada)


def req(metodo, url, dados=None):
    corpo = urllib.parse.urlencode(dados).encode() if dados else None
    r = urllib.request.Request(url, data=corpo, method=metodo)
    try:
        with urllib.request.urlopen(r, timeout=60) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"{metodo} {url.split('?')[0]} -> {e.code}: {e.read().decode(errors='ignore')[:500]}")


def token():
    chave = os.environ.get("IG_TOKEN_KEY")
    enc = os.path.join(AQUI, "token.enc")
    if chave and os.path.exists(enc):
        return subprocess.run(["openssl", "enc", "-d", "-aes-256-cbc", "-pbkdf2", "-in", enc, "-pass", "env:IG_TOKEN_KEY"],
                              capture_output=True, text=True, check=True).stdout.strip()
    return os.environ["IG_TOKEN"]


def renovar(tk):
    """O token dura 60 dias; renova e guarda cifrado em token.enc (o workflow faz o commit)."""
    novo = req("GET", "https://graph.instagram.com/refresh_access_token?" +
               urllib.parse.urlencode({"grant_type": "ig_refresh_token", "access_token": tk}))["access_token"]
    subprocess.run(["openssl", "enc", "-aes-256-cbc", "-pbkdf2", "-salt", "-out", os.path.join(AQUI, "token.enc"),
                    "-pass", "env:IG_TOKEN_KEY"], input=novo, text=True, check=True)
    print("token renovado")


def espera_pronto(cid, tk, limite=600):
    t0 = time.time()
    while time.time() - t0 < limite:
        st = req("GET", f"{API}/{cid}?" + urllib.parse.urlencode({"fields": "status_code,status", "access_token": tk}))
        if st.get("status_code") == "FINISHED":
            return
        if st.get("status_code") in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"container {cid}: {st}")
        time.sleep(10)
    raise RuntimeError(f"container {cid} não ficou pronto em {limite}s")


def url(arq):
    return BASE + urllib.parse.quote(arq)


def publica(item, uid, tk):
    tipo, leg = item["tipo"], item["legenda"]
    if tipo == "imagem":
        cid = req("POST", f"{API}/{uid}/media", {"image_url": url(item["arquivos"][0]), "caption": leg, "access_token": tk})["id"]
    elif tipo == "carrossel":
        filhos = [req("POST", f"{API}/{uid}/media", {"image_url": url(a), "is_carousel_item": "true", "access_token": tk})["id"]
                  for a in item["arquivos"]]
        for f in filhos:
            espera_pronto(f, tk)
        cid = req("POST", f"{API}/{uid}/media", {"media_type": "CAROUSEL", "children": ",".join(filhos),
                                                 "caption": leg, "access_token": tk})["id"]
    elif tipo == "reel":
        d = {"media_type": "REELS", "video_url": url(item["arquivos"][0]), "caption": leg,
             "share_to_feed": "true" if item.get("grid") else "false", "access_token": tk}
        if item.get("capa"):
            d["cover_url"] = url(item["capa"])
        cid = req("POST", f"{API}/{uid}/media", d)["id"]
    else:
        raise ValueError(tipo)
    espera_pronto(cid, tk)
    mid = req("POST", f"{API}/{uid}/media_publish", {"creation_id": cid, "access_token": tk})["id"]
    return mid


def detecta(tk):
    """A chave pode ser do login do Instagram (graph.instagram.com) ou do Facebook/usuário do sistema (graph.facebook.com)."""
    global API, TIPO
    try:
        me = req("GET", "https://graph.instagram.com/v23.0/me?" + urllib.parse.urlencode({"fields": "user_id,username", "access_token": tk}))
        API, TIPO = "https://graph.instagram.com/v23.0", "instagram"
        return me["user_id"], me.get("username")
    except Exception as e1:
        try:
            me = req("GET", f"https://graph.facebook.com/v23.0/{IG_USER_ID}?" + urllib.parse.urlencode({"fields": "username", "access_token": tk}))
            API, TIPO = "https://graph.facebook.com/v23.0", "facebook"
            return IG_USER_ID, me.get("username")
        except Exception as e2:
            raise RuntimeError(f"a chave não funcionou em nenhum dos dois endereços. instagram: {e1} | facebook: {e2}")


def main():
    agenda = json.load(open(os.path.join(AQUI, "agenda.json"), encoding="utf-8"))
    pub_path = os.path.join(AQUI, "publicados.json")
    pub = json.load(open(pub_path, encoding="utf-8")) if os.path.exists(pub_path) else {}
    agora = datetime.now(timezone.utc)

    if "--conferir" in sys.argv:
        for it in agenda:
            q = datetime.fromisoformat(it["quando"])
            falta = [a for a in it["arquivos"] + ([it["capa"]] if it.get("capa") else []) if not os.path.exists(os.path.join(AQUI, a))]
            st = "PUBLICADO" if it["id"] in pub else ("ARQUIVO FALTANDO " + str(falta) if falta else "ok")
            print(f"{q:%d/%m %H:%M}  {it['tipo']:9} {'grid' if it.get('grid', it['tipo'] != 'reel') else 'só reels'}  {it['id']:28} {len(it['legenda']):4} car.  {st}")
        return

    if not os.environ.get("IG_TOKEN") and not os.path.exists(os.path.join(AQUI, "token.enc")):
        print("aguardando o token da Meta (segredo IG_TOKEN); nada a fazer")
        return
    tk = token()
    uid, nome = detecta(tk)
    print(f"conta: @{nome}  (chave do tipo {TIPO})")
    if "--teste" in sys.argv:
        lim = req("GET", f"{API}/{uid}/content_publishing_limit?" + urllib.parse.urlencode({"fields": "config,quota_usage", "access_token": tk}))
        print("limite de publicações:", json.dumps(lim))
        print("TESTE OK: nada foi publicado")
        return

    erros = 0
    for it in sorted(agenda, key=lambda x: x["quando"]):
        q = datetime.fromisoformat(it["quando"])
        if it["id"] in pub or q > agora:
            continue
        if agora - q > ATRASO_MAX:
            print(f"pulado (passou do horário há mais de 12 h): {it['id']}")
            pub[it["id"]] = {"status": "pulado", "em": agora.isoformat()}
            continue
        try:
            mid = publica(it, uid, tk)
            pub[it["id"]] = {"status": "publicado", "media_id": mid, "em": agora.isoformat()}
            print("publicado:", it["id"], mid)
        except Exception as e:
            erros += 1
            print("ERRO:", it["id"], e)
        json.dump(pub, open(pub_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    # renova o token uma vez por semana (segunda-feira, na primeira rodada depois das 9h UTC)
    if TIPO == "instagram" and os.environ.get("IG_TOKEN_KEY") and agora.weekday() == 0 and 9 <= agora.hour < 10:
        renovar(tk)
    if "--renovar" in sys.argv and TIPO == "instagram" and os.environ.get("IG_TOKEN_KEY"):
        renovar(tk)
    sys.exit(1 if erros else 0)


if __name__ == "__main__":
    main()
