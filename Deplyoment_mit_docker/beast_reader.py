#!/usr/bin/env python3
import socket
import time

def read_beast_data():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('localhost', 30105))
        print("🛩️ Verbunden mit Beast Port 30105")
        print("Warte auf ADS-B Nachrichten...\n")
        
        message_count = 0
        while True:
            data = sock.recv(1024)
            if not data:
                break
                
            # Suche Beast Messages (beginnen mit 0x1A)
            i = 0
            while i < len(data):
                if data[i] == 0x1A and i + 1 < len(data):
                    message_count += 1
                    msg_type = data[i + 1]
                    
                    # Message Types dekodieren
                    types = {
                        0x31: "Mode A/C",
                        0x32: "Mode S Short", 
                        0x33: "Mode S Long (ADS-B)",
                        0x34: "Signal Level"
                    }
                    
                    type_name = types.get(msg_type, f"Unknown (0x{msg_type:02x})")
                    
                    print(f"Message #{message_count}: {type_name}")
                    
                    # Zeige erste 20 Bytes
                    end = min(i + 20, len(data))
                    hex_data = data[i:end].hex().upper()
                    print(f"  Hex: {hex_data}")
                    
                    # Wenn Mode S Long, zeige ICAO
                    if msg_type == 0x33 and i + 5 < len(data):
                        icao = data[i+2:i+5].hex().upper()
                        print(f"  ICAO: {icao}")
                    
                    print()
                i += 1
                
    except KeyboardInterrupt:
        print(f"\n✅ {message_count} Nachrichten empfangen")
    except Exception as e:
        print(f"❌ Fehler: {e}")
    finally:
        sock.close()

if __name__ == "__main__":
    read_beast_data()