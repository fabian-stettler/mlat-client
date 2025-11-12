#!/usr/bin/env python3
import socket
import time
import struct

def decode_beast_advanced():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1.0)  # 1 Sekunde Timeout
        sock.connect(('localhost', 30105))
        print("🛩️ Erweiterte Beast-Dekodierung gestartet")
        print("Verbunden mit Port 30105\n")
        
        message_count = 0
        real_aircraft_found = False
        
        start_time = time.time()
        
        while time.time() - start_time < 30:  # 30 Sekunden testen
            try:
                data = sock.recv(4096)
                if not data:
                    break
                    
                # Analysiere alle Beast Messages im Buffer
                i = 0
                while i < len(data) - 1:
                    if data[i] == 0x1A:  # Beast Sync
                        message_count += 1
                        msg_type = data[i + 1] if i + 1 < len(data) else 0
                        
                        # Bestimme Message-Länge
                        msg_lengths = {
                            0x31: 8,   # Mode A/C
                            0x32: 14,  # Mode S Short
                            0x33: 23,  # Mode S Long
                            0x34: 10,  # Signal Level
                            0x35: 9    # ID
                        }
                        
                        msg_len = msg_lengths.get(msg_type, 8)
                        
                        if i + msg_len <= len(data):
                            message = data[i:i + msg_len]
                            
                            # Analysiere Message
                            analysis = analyze_message(message, message_count)
                            
                            if analysis['is_real']:
                                real_aircraft_found = True
                                print("✈️  ECHTE FLUGZEUGDATEN GEFUNDEN!")
                                print(f"   {analysis}")
                                print()
                            elif message_count <= 10 or message_count % 50 == 0:
                                # Zeige erste 10 und dann jede 50ste Message
                                print(f"Message #{message_count}: {analysis['type']}")
                                if analysis['icao'] and analysis['icao'] != '000000':
                                    print(f"   ICAO: {analysis['icao']}")
                                if analysis['details']:
                                    print(f"   {analysis['details']}")
                                print(f"   Hex: {message.hex().upper()[:40]}...")
                                print()
                        
                        i += msg_len
                    else:
                        i += 1
                        
            except socket.timeout:
                print(".", end="", flush=True)
                continue
                
    except KeyboardInterrupt:
        print(f"\n\n📊 ZUSAMMENFASSUNG:")
        print(f"   Nachrichten empfangen: {message_count}")
        print(f"   Echte Flugzeuge gefunden: {'JA' if real_aircraft_found else 'NEIN'}")
        print(f"   Status: {'✅ ADS-B funktioniert!' if real_aircraft_found else '⚠️  Nur Test-/Null-Daten'}")
    except Exception as e:
        print(f"❌ Fehler: {e}")
    finally:
        sock.close()

def analyze_message(message, count):
    """Analysiert eine Beast Message detailliert"""
    if len(message) < 2:
        return {'type': 'Invalid', 'is_real': False, 'icao': None, 'details': None}
    
    msg_type = message[1]
    types = {
        0x31: "Mode A/C",
        0x32: "Mode S Short", 
        0x33: "Mode S Long (ADS-B)",
        0x34: "Signal Level",
        0x35: "ID"
    }
    
    type_name = types.get(msg_type, f"Unknown (0x{msg_type:02x})")
    icao = None
    details = None
    is_real = False
    
    # Prüfe auf echte Daten (nicht nur Nullen)
    data_bytes = message[2:] if len(message) > 2 else b''
    non_zero_bytes = sum(1 for b in data_bytes if b != 0)
    
    if msg_type == 0x33 and len(message) >= 23:  # Mode S Long
        # ICAO Address extrahieren
        icao = message[2:5].hex().upper()
        
        # Message extrahieren (ab Byte 8)
        if len(message) >= 21:
            adsb_msg = message[8:21]
            df = (adsb_msg[0] >> 3) & 0x1F
            
            if df == 17:  # ADS-B Extended Squitter
                type_code = (adsb_msg[4] >> 3) & 0x1F
                details = f"ADS-B DF={df}, TC={type_code}"
                
                # Prüfe auf echte ADS-B Daten
                if icao != "000000" and non_zero_bytes > 5:
                    is_real = True
                    
    elif msg_type == 0x32 and len(message) >= 14:  # Mode S Short
        icao = message[2:5].hex().upper()
        if icao != "000000" and non_zero_bytes > 3:
            is_real = True
            
    elif msg_type == 0x31:  # Mode A/C
        if non_zero_bytes > 2:
            is_real = True
            details = f"Non-zero bytes: {non_zero_bytes}"
    
    return {
        'type': type_name,
        'icao': icao,
        'details': details,
        'is_real': is_real,
        'non_zero_bytes': non_zero_bytes
    }

if __name__ == "__main__":
    decode_beast_advanced()