"""Monta agenda.json + midia/ a partir da pasta publicacoes (roda no computador, antes do push).

Cada linha de ITENS: (quando, id, tipo, pasta ou arquivo de origem, grid)
  - carrossel/imagem: pasta com tela-N.jpg e legenda.txt
  - reel do grid: pasta com video-do-grid.mp4 (ou reel-fora-do-grid.mp4), capa tela-1.jpg, legenda.txt
  - reel fora do grid: arquivo .mp4 com .txt de legenda ao lado
Uso: python montar_agenda.py
"""
import json, pathlib, shutil

AQUI = pathlib.Path(__file__).resolve().parent
PUB = AQUI.parent / "publicacoes" / "instagram"
FILA, REELS = PUB / "2-a-postar", PUB / "3-reels"

def pasta(nome):
    return next(FILA.glob(f"* {nome}"))

ITENS = [
    ("2026-11-12T12:00:00-03:00", "2026-11-12-check-up", "carrossel", pasta("26 check-up"), True),
    ("2026-11-11T15:46:00-03:00", "2026-11-11-reel-folego-teste", "reel", REELS / "09 folego.mp4", False),
    ("2026-11-12T19:00:00-03:00", "2026-11-12-reel-cafe", "reel", REELS / "05 cafe.mp4", False),
    ("2026-11-13T12:00:00-03:00", "2026-11-13-natureza", "carrossel", pasta("25 natureza"), True),
    ("2026-11-13T19:00:00-03:00", "2026-11-13-reel-ultraprocessados", "reel", REELS / "08 ultraprocessados.mp4", False),
    ("2026-11-14T12:00:00-03:00", "2026-11-14-reel-sentar", "reel", pasta("24 reel-sentar"), True),
    ("2026-11-14T19:00:00-03:00", "2026-11-14-reel-sono", "reel", REELS / "04 sono.mp4", False),
    ("2026-11-15T12:00:00-03:00", "2026-11-15-predimed", "carrossel", pasta("27 predimed"), True),
    ("2026-11-15T19:00:00-03:00", "2026-11-15-reel-forca-mao", "reel", REELS / "10 forca-mao.mp4", False),
    ("2026-11-16T12:00:00-03:00", "2026-11-16-reel-plano-idade", "reel", pasta("28 reel-plano-idade"), True),
    ("2026-11-16T19:00:00-03:00", "2026-11-16-reel-otimismo", "reel", REELS / "12 otimismo.mp4", False),
    ("2026-11-17T12:00:00-03:00", "2026-11-17-ikigai", "carrossel", pasta("21 ikigai"), True),
    ("2026-11-17T19:00:00-03:00", "2026-11-17-reel-55-horas", "reel", REELS / "11 55-horas.mp4", False),
    ("2026-11-18T12:00:00-03:00", "2026-11-18-sentado", "imagem", pasta("20 sentado"), True),
    ("2026-11-18T19:00:00-03:00", "2026-11-18-reel-relacoes", "reel", REELS / "06 relacoes.mp4", False),
]

# Lote 2 (19/11 a 02/12): post do grid às 12h; às 19h o reel do próprio post, fora do grid.
# Nos dias em que o post do meio-dia já é reel no grid, o reel das 19h vem da fila antiga.
LOTE2 = [  # (data, nº slug, tipo do meio-dia, reel das 19h: None = o do próprio post)
    ("2026-11-19", "29 treino-horario", "carrossel", None),
    ("2026-11-20", "30 pausas", "imagem", None),
    ("2026-11-21", "31 um-pe", "reel", "19 caminhada"),
    ("2026-11-22", "32 alcool", "carrossel", None),
    ("2026-11-23", "33 inah", "carrossel", None),
    ("2026-11-24", "34 quatro-testes", "carrossel", None),
    ("2026-11-25", "35 fim-de-semana", "carrossel", None),
    ("2026-11-26", "36 anos-que-restam", "reel", "26 check-up"),
    ("2026-11-27", "37 pausa-trabalho", "carrossel", None),
    ("2026-11-28", "38 escada", "reel", "27 predimed"),
    ("2026-11-29", "39 sono-fds", "carrossel", None),
    ("2026-11-30", "40 voluntariado", "imagem", None),
    ("2026-12-01", "41 marchand", "carrossel", None),
    ("2026-12-02", "42 plano-cada-idade", "carrossel", None),
]
for data, nome, tipo, reel19 in LOTE2:
    slug = nome.split(" ", 1)[1]
    ITENS.append((f"{data}T12:00:00-03:00", f"{data}-{slug}", tipo, pasta(nome), True))
    if reel19:
        ITENS.append((f"{data}T19:00:00-03:00", f"{data}-reel-{reel19.split(' ', 1)[1]}", "reel-pasta", pasta(reel19), False))
    else:
        ITENS.append((f"{data}T19:00:00-03:00", f"{data}-reel-{slug}", "reel-pasta", pasta(nome), False))

def main():
    agenda = []
    for quando, iid, tipo, origem, grid in ITENS:
        dest = AQUI / "midia" / iid
        if dest.exists():
            shutil.rmtree(dest)
        dest.mkdir(parents=True)
        it = {"id": iid, "quando": quando, "tipo": "reel" if tipo == "reel-pasta" else tipo, "grid": grid}
        if tipo == "reel-pasta":  # reel fora do grid tirado da pasta de um post (vídeo + capa + legenda do post)
            shutil.copyfile(origem / "reel-fora-do-grid.mp4", dest / "video.mp4"); shutil.copyfile(origem / "tela-1.jpg", dest / "capa.jpg")
            it["arquivos"], it["capa"] = [f"midia/{iid}/video.mp4"], f"midia/{iid}/capa.jpg"
            leg = (origem / "legenda.txt").read_text(encoding="utf-8")
        elif tipo in ("carrossel", "imagem"):
            telas = sorted(origem.glob("tela-*.jpg"), key=lambda p: int(p.stem.split("-")[1]))
            if tipo == "imagem":
                telas = telas[:1]
            for t in telas:
                shutil.copyfile(t, dest / t.name)
            it["arquivos"] = [f"midia/{iid}/{t.name}" for t in telas]
            leg = (origem / "legenda.txt").read_text(encoding="utf-8")
        elif origem.is_dir():  # reel do grid
            v = origem / "video-do-grid.mp4"
            if not v.exists():
                v = origem / "reel-fora-do-grid.mp4"
            shutil.copyfile(v, dest / "video.mp4"); shutil.copyfile(origem / "tela-1.jpg", dest / "capa.jpg")
            it["arquivos"], it["capa"] = [f"midia/{iid}/video.mp4"], f"midia/{iid}/capa.jpg"
            leg = (origem / "legenda.txt").read_text(encoding="utf-8")
        else:  # reel fora do grid
            shutil.copyfile(origem, dest / "video.mp4")
            it["arquivos"] = [f"midia/{iid}/video.mp4"]
            leg = origem.with_suffix(".txt").read_text(encoding="utf-8")
        it["legenda"] = leg.strip()
        assert len(it["legenda"]) <= 2200, f"legenda longa demais: {iid}"
        agenda.append(it)
    (AQUI / "agenda.json").write_text(json.dumps(agenda, ensure_ascii=False, indent=1), encoding="utf-8")
    print(len(agenda), "itens em agenda.json")

if __name__ == "__main__":
    main()
