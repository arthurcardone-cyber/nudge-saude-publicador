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

def main():
    agenda = []
    for quando, iid, tipo, origem, grid in ITENS:
        dest = AQUI / "midia" / iid
        if dest.exists():
            shutil.rmtree(dest)
        dest.mkdir(parents=True)
        it = {"id": iid, "quando": quando, "tipo": tipo, "grid": grid}
        if tipo in ("carrossel", "imagem"):
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
