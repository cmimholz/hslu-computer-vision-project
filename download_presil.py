import time
from pathlib import Path
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# --- Zielordner (WSL). Für Windows nativ: Path(r"C:\datasets\gta")
DEST = Path("/mnt/c/datasets/gta")
DEST.mkdir(parents=True, exist_ok=True)

URLS = [
    "http://wiselab.uwaterloo.ca/OursObjectDet/images.zip.001",
    "http://wiselab.uwaterloo.ca/OursObjectDet/images.zip.002",
    "http://wiselab.uwaterloo.ca/OursObjectDet/images.zip.003"
]

CHUNK = 1024 * 1024 * 4  # 4 MiB
CONNECT_TIMEOUT = 15
READ_TIMEOUT = 300       # wichtiger als 60s bei langsamen Servern

# --- Session mit Retries (auch bei Read-Timeout)
session = requests.Session()
retry = Retry(
    total=None,            # unlimitiert, wir steuern selbst via Loop
    connect=5,
    read=5,
    backoff_factor=2.0,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=frozenset(["GET", "HEAD"])
)
session.mount("http://", HTTPAdapter(max_retries=retry))
session.mount("https://", HTTPAdapter(max_retries=retry))

def get_size(url: str) -> int | None:
    try:
        r = session.head(url, allow_redirects=True, timeout=(CONNECT_TIMEOUT, READ_TIMEOUT))
        r.raise_for_status()
        return int(r.headers.get("Content-Length", "0")) or None
    except Exception:
        return None

def download_with_resume(url: str, dest: Path) -> Path:
    local = dest / Path(url).name
    total = get_size(url)
    pos = local.stat().st_size if local.exists() else 0
    last_report = 0.0

    while True:
        headers = {"Range": f"bytes={pos}-"} if pos else {}
        try:
            with session.get(url, headers=headers, stream=True,
                             timeout=(CONNECT_TIMEOUT, READ_TIMEOUT)) as r:
                # 206 = Partial Content (Range), 200 = kompletter Download
                if r.status_code not in (200, 206):
                    print(f"\nHTTP {r.status_code} für {url}. Warte 10s und versuche erneut …")
                    time.sleep(10)
                    continue

                mode = "ab" if pos else "wb"
                with open(local, mode) as f:
                    for chunk in r.iter_content(CHUNK):
                        if not chunk:
                            continue
                        f.write(chunk)
                        pos += len(chunk)

                        # Fortschritt alle ~5s ausgeben
                        now = time.time()
                        if now - last_report > 5:
                            if total:
                                pct = pos * 100 / total
                                print(f"\r{local.name}: {pos/1e9:.1f}/{total/1e9:.1f} GB ({pct:.1f}%)", end="")
                            else:
                                print(f"\r{local.name}: {pos/1e9:.1f} GB", end="")
                            last_report = now

                # fertig?
                if total is None or pos >= total:
                    print()
                    return local

                # Server hat Verbindung vorher geschlossen -> weiter im Loop (Resume)
                print("\nVerbindung beendet, setze Download fort …")
                time.sleep(5)

        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as e:
            print(f"\n{type(e).__name__}: {e}. Setze in 10s fort …")
            time.sleep(10)

if __name__ == "__main__":
    for u in URLS:
        print(f"Downloading → {u}")
        p = download_with_resume(u, DEST)
        print(f"OK: {p}  ({p.stat().st_size/1e9:.2f} GB)")
