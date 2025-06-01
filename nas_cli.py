import socket
import time
import requests
import argparse
import sys

# ========== KONFIGURATION ==========
MAC_ADDRESS = "00:11:22:33:44:55"
BROADCAST_IP = "192.168.178.255"

READY_ENDPOINT = "https://nas.xyz.de/api/v2.0/system/ready"
STATE_ENDPOINT = "https://nas.xyz.de/api/v2.0/system/state"
INFO_ENDPOINT = "https://nas.xyz.de/api/v2.0/system/info"
SHUTDOWN_ENDPOINT = "https://nas.xyz.de/api/v2.0/system/shutdown"

BEARER_TOKEN = "DEIN_BEARER_TOKEN_HIER"
# ===================================
def get_headers(json_type=True):
    headers = {
        "accept": "application/json" if json_type else "*/*",
        "Authorization": f"Bearer {BEARER_TOKEN}"
    }
    if json_type:
        headers["Content-Type"] = "application/json"
    return headers

def check_nas_status(url, token):
    try:
        r = requests.get(url, headers=get_headers(), timeout=2)
        return r.status_code == 200
    except requests.exceptions.RequestException:
        return False

def print_nas_info():
    try:
        r = requests.get(INFO_ENDPOINT, headers=get_headers(), timeout=5)
        if r.status_code == 200:
            data = r.json()
            # Liste der gewünschten Felder in der Reihenfolge
            fields = [
                ("version", "Version"),
                ("hostname", "Hostname"),
                ("model", "Modell"),
                ("cores", "CPU Kerne"),
                ("uptime", "Laufzeit"),
                ("system_serial", "Seriennummer"),
                ("system_product", "Produkt"),
                ("timezone", "Zeitzone"),
            ]

            print("\n📊 NAS-Informationen:")
            for key, label in fields:
                value = data.get(key, None)
                # Falls der Wert ein dict mit $date ist, kann man das noch umwandeln (optional)
                if isinstance(value, dict) and "$date" in value:
                    # Timestamp in lesbares Datum konvertieren
                    try:
                        timestamp = int(value["$date"]) / 1000
                        value = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))
                    except Exception:
                        pass
                if key == "uptime" and value is not None:
                    value = format_uptime(value)
                if value is not None:
                    print(f"  {label}: {value}")

        else:
            print(f"[INFO] NAS-Infos konnten nicht geladen werden (HTTP {r.status_code})")
    except requests.exceptions.RequestException as e:
        print(f"[INFO] NAS-Infos nicht abrufbar: {e}")

def format_uptime(uptime_str):
    # Erwartet Format "H:MM:SS.micro"
    try:
        parts = uptime_str.split(":")
        if len(parts) == 3:
            h = int(parts[0])
            m = int(parts[1])
            s = float(parts[2])
            sec = int(s)
            # Mikrosekunden ignorieren
            return f"{h}h {m}m {sec}s"
    except Exception:
        pass
    return uptime_str  # fallback: original zurückgeben

def wake_on_lan(mac_address, broadcast_ip):
    mac = mac_address.replace(":", "").replace("-", "")
    if len(mac) != 12:
        raise ValueError("Ungültige MAC-Adresse")
    packet = bytes.fromhex("FF" * 6 + mac * 16)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(packet, (broadcast_ip, 9))
    print("[INFO] Wake-on-LAN-Paket gesendet.")

def wait_for_ready(url, token, timeout=300, interval=5):
    headers = get_headers()
    print("[INFO] Warte auf NAS-Bereitschaft...")
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            r = requests.get(url, headers=headers, timeout=5)
            if r.status_code == 200:
                elapsed = time.time() - start_time
                print(f"[✓] NAS ist bereit nach {round(elapsed, 2)} Sekunden.")
                return
        except requests.exceptions.RequestException:
            pass
        time.sleep(interval)
    print("[X] Timeout: NAS ist nicht bereit.")
    sys.exit(1)

def shutdown_nas(url, token):
    try:
        r = requests.post(url, headers=get_headers(), json={})
        if r.status_code == 200:
            print("[✓] NAS fährt herunter.")
        else:
            print(f"[X] Fehler beim Herunterfahren: HTTP {r.status_code}")
            print(r.text)
            sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"[X] Netzwerkfehler: {e}")
        sys.exit(1)

def interactive_menu():
    status = check_nas_status(READY_ENDPOINT, BEARER_TOKEN)
    print("\n📦 NAS Control CLI")
    print("====================")
    print(f"NAS-Status: {'🟢 erreichbar' if status else '🔴 nicht erreichbar'}")
    if status:
        print_nas_info()

    print("\n1) NAS starten (Wake-on-LAN)")
    print("2) NAS herunterfahren")
    print("0) Beenden")

    choice = input("Bitte Auswahl eingeben (0–2): ").strip()
    if choice == "1":
        wake_on_lan(MAC_ADDRESS, BROADCAST_IP)
        wait_for_ready(READY_ENDPOINT, BEARER_TOKEN)
    elif choice == "2":
        shutdown_nas(SHUTDOWN_ENDPOINT, BEARER_TOKEN)
    elif choice == "0":
        print("Beende...")
        sys.exit(0)
    else:
        print("Ungültige Eingabe.")
        interactive_menu()
    input("\n[ENTER] drücken zum Beenden...")

def main():
    parser = argparse.ArgumentParser(description="NAS Control CLI")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("wake", help="NAS starten (Wake-on-LAN)")
    subparsers.add_parser("shutdown", help="NAS herunterfahren")

    args = parser.parse_args()

    if args.command == "wake":
        online = check_nas_status(READY_ENDPOINT, BEARER_TOKEN)
        print("[INFO] NAS-Status:", "🟢 erreichbar" if online else "🔴 nicht erreichbar")
        if online:
            print_nas_info()
        wake_on_lan(MAC_ADDRESS, BROADCAST_IP)
        wait_for_ready(READY_ENDPOINT, BEARER_TOKEN)

    elif args.command == "shutdown":
        online = check_nas_status(READY_ENDPOINT, BEARER_TOKEN)
        print("[INFO] NAS-Status:", "🟢 erreichbar" if online else "🔴 nicht erreichbar")
        if online:
            print_nas_info()
        shutdown_nas(SHUTDOWN_ENDPOINT, BEARER_TOKEN)

    else:
        interactive_menu()
        input("\n[ENTER] drücken zum Beenden...")

if __name__ == "__main__":
    main()
