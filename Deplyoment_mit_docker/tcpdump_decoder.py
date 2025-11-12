#!/usr/bin/env python3
"""
TCP Dump Hex Decoder für ADS-B Beast-Format
Dekodiert die Hex-Ausgabe von tcpdump -X
"""

def decode_hex_line(hex_line):
    """Dekodiert eine Hex-Zeile aus tcpdump"""
    # Entferne Adresse und ASCII-Teil, behalte nur Hex
    parts = hex_line.strip().split(':')
    if len(parts) < 2:
        return None
    
    hex_part = parts[1].strip()
    # Entferne ASCII-Teil (nach zwei oder mehr Leerzeichen)
    hex_part = hex_part.split('  ')[0]
    
    # Entferne Leerzeichen und konvertiere zu Bytes
    hex_clean = hex_part.replace(' ', '')
    if len(hex_clean) % 2 != 0:
        return None
        
    try:
        return bytes.fromhex(hex_clean)
    except ValueError:
        return None

def find_beast_messages(data):
    """Sucht Beast-Nachrichten in den Daten (beginnen mit 0x1A)"""
    messages = []
    i = 0
    while i < len(data):
        if data[i] == 0x1A and i + 1 < len(data):
            msg_type = data[i + 1]
            
            # Bestimme Message-Länge
            lengths = {
                0x31: 8,   # Mode A/C
                0x32: 14,  # Mode S Short
                0x33: 23,  # Mode S Long
                0x34: 10,  # Signal Level
                0x35: 9    # ID
            }
            
            expected_len = lengths.get(msg_type, 23)
            if i + expected_len <= len(data):
                message = data[i:i + expected_len]
                messages.append(decode_beast_message(message))
                i += expected_len
            else:
                i += 1
        else:
            i += 1
    
    return messages

def decode_beast_message(data):
    """Dekodiert eine Beast-Nachricht"""
    if len(data) < 2 or data[0] != 0x1A:
        return None
    
    msg_type = data[1]
    
    types = {
        0x31: "Mode A/C",
        0x32: "Mode S Short", 
        0x33: "Mode S Long (ADS-B)",
        0x34: "Signal Level",
        0x35: "ID"
    }
    
    result = {
        'type': types.get(msg_type, f"Unknown (0x{msg_type:02x})"),
        'raw_hex': data.hex().upper(),
        'length': len(data)
    }
    
    if msg_type == 0x33 and len(data) >= 16:  # Mode S Long
        # ICAO Adresse (Bytes 2-4 nach Beast-Header)
        icao = data[2:5].hex().upper()
        result['icao'] = icao
        
        # Message Payload (ab Byte 8)
        if len(data) >= 21:
            message = data[8:21]
            result['message'] = message.hex().upper()
            
            # DF (Downlink Format)
            df = (message[0] >> 3) & 0x1F
            result['df'] = df
            
            if df == 17:  # ADS-B Extended Squitter
                type_code = (message[4] >> 3) & 0x1F
                result['type_code'] = type_code
                result['ads_b_type'] = get_adsb_type(type_code)
                
                # Callsign extrahieren (Type Code 1-4)
                if 1 <= type_code <= 4:
                    callsign = decode_callsign(message[5:11])
                    if callsign:
                        result['callsign'] = callsign
    
    elif msg_type == 0x31 and len(data) >= 8:  # Mode A/C
        # Mode A/C Squawk Code
        if len(data) >= 6:
            squawk_data = data[4:6]
            result['squawk_hex'] = squawk_data.hex().upper()
    
    return result

def decode_callsign(data):
    """Dekodiert Callsign aus ADS-B Nachricht"""
    if len(data) < 6:
        return None
    
    charset = "ABCDEFGHIJKLMNOPQRSTUVWXYZ      0123456789      "
    callsign = ""
    
    try:
        # 6 Zeichen à 6 Bit
        chars = []
        chars.append((data[0] >> 2) & 0x3F)
        chars.append(((data[0] & 0x03) << 4) | ((data[1] >> 4) & 0x0F))
        chars.append(((data[1] & 0x0F) << 2) | ((data[2] >> 6) & 0x03))
        chars.append(data[2] & 0x3F)
        chars.append((data[3] >> 2) & 0x3F)
        chars.append(((data[3] & 0x03) << 4) | ((data[4] >> 4) & 0x0F))
        chars.append(((data[4] & 0x0F) << 2) | ((data[5] >> 6) & 0x03))
        chars.append(data[5] & 0x3F)
        
        for char_code in chars:
            if char_code < len(charset):
                callsign += charset[char_code]
        
        return callsign.strip()
    except:
        return None

def get_adsb_type(type_code):
    """ADS-B Message Type"""
    if 1 <= type_code <= 4:
        return "Aircraft Identification"
    elif 9 <= type_code <= 18:
        return "Airborne Position" 
    elif type_code == 19:
        return "Airborne Velocity"
    elif 20 <= type_code <= 22:
        return "Airborne Position"
    else:
        return f"Type {type_code}"

def main():
    print("🔍 TCP Dump Hex Decoder für ADS-B")
    print("Fügen Sie Ihre tcpdump -X Hex-Zeilen ein:")
    print("Beispiel: 0x0010:  1a33 4840 d620 2cc3 71c3 2ce0 5760 98ab")
    print("Drücken Sie Ctrl+D wenn fertig\n")
    
    all_data = b''
    
    try:
        while True:
            line = input()
            if line.strip().startswith('0x'):
                # Hex-Zeile aus tcpdump
                decoded = decode_hex_line(line)
                if decoded:
                    all_data += decoded
                    print(f"📥 Hex-Daten: {decoded.hex().upper()}")
    except EOFError:
        pass
    
    if all_data:
        print(f"\n📊 Gesamte Daten ({len(all_data)} bytes): {all_data.hex().upper()}")
        
        # Suche Beast-Nachrichten
        messages = find_beast_messages(all_data)
        
        if messages:
            print(f"\n🛩️ {len(messages)} Beast-Nachricht(en) gefunden:")
            for i, msg in enumerate(messages, 1):
                if msg:
                    print(f"\n--- Nachricht #{i} ---")
                    print(f"Typ: {msg['type']}")
                    if 'icao' in msg:
                        print(f"ICAO: {msg['icao']}")
                    if 'callsign' in msg:
                        print(f"Callsign: {msg['callsign']}")
                    if 'ads_b_type' in msg:
                        print(f"ADS-B: {msg['ads_b_type']}")
                    if 'squawk_hex' in msg:
                        print(f"Squawk: {msg['squawk_hex']}")
                    print(f"Raw: {msg['raw_hex']}")
        else:
            print("\n❌ Keine Beast-Nachrichten gefunden")
            print("💡 Tipp: Beast-Nachrichten beginnen mit 1A")
    else:
        print("❌ Keine gültigen Hex-Daten gefunden")

if __name__ == "__main__":
    main()