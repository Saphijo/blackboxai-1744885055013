import json
import time
import sys
from gpiozero import DigitalOutputDevice, GPIOZeroError

# --- Konfiguration ---
CONFIG_FILE = 'pumpen.json'  # Name deiner JSON-Konfigurationsdatei
TEST_DURATION_SECONDS = 1.0  # Dauer für jede Richtung (vorwärts/rückwärts)
DELAY_BETWEEN_DIRECTIONS = 0.5 # Kurze Pause zwischen Richtungswechsel
DELAY_BETWEEN_PUMPS = 1.0      # Pause zwischen dem Testen verschiedener Pumpen

# --- Annahme zur Pin-Logik (kann je nach Verkabelung angepasst werden) ---
# Wir gehen davon aus, dass:
# - 'gpio_pin' den Motor EIN/AUS schaltet (HIGH = EIN, LOW = AUS)
# - 'direction_pin' die Richtung steuert (LOW = Vorwärts, HIGH = Rückwärts)
# Wenn deine Pumpen andersherum laufen, tausche die Logik in den Funktionen
# run_forward und run_backward oder passe die Zuweisung von LOW/HIGH an.
FORWARD_LEVEL = 0 # Pegel am direction_pin für Vorwärtslauf (0 = LOW)
BACKWARD_LEVEL = 1 # Pegel am direction_pin für Rückwärtslauf (1 = HIGH)

# --- Globale Variable für initialisierte Geräte ---
# Wird benötigt, um im Fehlerfall auf alle Geräte zugreifen zu können
pump_gpio_devices = {}

# --- Hilfsfunktionen ---
def load_config(filename):
    """Lädt die Pumpenkonfiguration aus einer JSON-Datei."""
    try:
        with open(filename, 'r') as f:
            config = json.load(f)
        if 'pumps' not in config or not isinstance(config['pumps'], list):
            print(f"Fehler: '{filename}' enthält keinen gültigen 'pumps'-Array.")
            return None # Signalisiert einen Fehler
        return config['pumps']
    except FileNotFoundError:
        print(f"Fehler: Konfigurationsdatei '{filename}' nicht gefunden.")
        return None
    except json.JSONDecodeError:
        print(f"Fehler: Konfigurationsdatei '{filename}' ist kein gültiges JSON.")
        return None
    except Exception as e:
        print(f"Ein unerwarteter Fehler beim Laden der Konfiguration ist aufgetreten: {e}")
        return None

def setup_pump_gpio(pump_config):
    """Initialisiert die GPIO-Geräte für eine Pumpe. Gibt bei Erfolg (power_pin, direction_pin) zurück, sonst None."""
    global pump_gpio_devices # Zugriff auf das globale Dictionary
    pump_id = pump_config.get("id", f"Pin{pump_config.get('gpio_pin')}") # Fallback falls ID fehlt

    try:
        print(f"- Initialisiere Pumpe {pump_id} (Power: GPIO{pump_config.get('gpio_pin')}, Direction: GPIO{config.get('direction_pin')})")
        power_pin = DigitalOutputDevice(pump_config['gpio_pin'], initial_value=False)
        direction_pin = DigitalOutputDevice(pump_config['direction_pin'], initial_value=False)
        # Erfolgreich initialisiert, füge zum globalen Dictionary hinzu
        pump_gpio_devices[pump_id] = (power_pin, direction_pin)
        return True # Erfolg signalisieren
    except GPIOZeroError as e:
        print(f"  ! GPIO Fehler beim Initialisieren für Pumpe {pump_id} "
              f"(Pins: {pump_config.get('gpio_pin')}, {pump_config.get('direction_pin')}): {e}")
        print("  ! Stelle sicher, dass die Pins nicht bereits verwendet werden und die GPIO-Bibliothek korrekt funktioniert.")
        return False # Fehler signalisieren
    except KeyError as e:
        print(f"  ! Fehler: Fehlender Schlüssel '{e}' in der Konfiguration für Pumpe {pump_id}.")
        return False # Fehler signalisieren
    except Exception as e:
        print(f"  ! Unerwarteter Fehler bei Initialisierung von Pumpe {pump_id}: {e}")
        return False # Fehler signalisieren


def run_forward(power_pin, direction_pin, duration):
    """Lässt die Pumpe für eine bestimmte Dauer vorwärts laufen."""
    print(f"  -> Vorwärts ({duration}s)...")
    direction_pin.value = FORWARD_LEVEL  # Richtung setzen
    time.sleep(0.1) # Kurze Pause, damit die Richtung sicher gesetzt ist
    power_pin.on()       # Pumpe einschalten
    time.sleep(duration) # Laufen lassen
    power_pin.off()      # Pumpe ausschalten
    print("     Stopp.")

def run_backward(power_pin, direction_pin, duration):
    """Lässt die Pumpe für eine bestimmte Dauer rückwärts laufen."""
    print(f"  -> Rückwärts ({duration}s)...")
    direction_pin.value = BACKWARD_LEVEL # Richtung setzen
    time.sleep(0.1) # Kurze Pause
    power_pin.on()        # Pumpe einschalten
    time.sleep(duration)  # Laufen lassen
    power_pin.off()       # Pumpe ausschalten
    print("     Stopp.")

def stop_all_pumps():
    """Stoppt alle bisher erfolgreich initialisierten Pumpen sofort."""
    print("\nNOT-STOPP: Stoppe alle initialisierten Pumpen...")
    global pump_gpio_devices
    stopped_count = 0
    for pump_id, devices in pump_gpio_devices.items():
        power_pin, _ = devices # Direction Pin ist hier egal
        if power_pin:
            try:
                power_pin.off()
                stopped_count += 1
            except Exception as e:
                # Fehler beim Stoppen einer einzelnen Pumpe protokollieren, aber weitermachen
                print(f"  ! Fehler beim Stoppen von Pumpe {pump_id}: {e}")
    print(f"{stopped_count} Pumpe(n) gestoppt.")


def cleanup_gpio():
    """Gibt alle verwendeten GPIO-Ressourcen frei."""
    print("\nAufräumen der GPIO-Pins...")
    global pump_gpio_devices
    closed_count = 0
    for pump_id, devices in pump_gpio_devices.items():
        power_pin, direction_pin = devices
        try:
            if power_pin:
                power_pin.close()
            if direction_pin:
                direction_pin.close()
            closed_count += 1
        except Exception as e:
             # Fehler beim Schließen einer einzelnen Pumpe protokollieren, aber weitermachen
            print(f"  ! Fehler beim Schließen der Pins für Pumpe {pump_id}: {e}")
    print(f"{closed_count} Pumpen-GPIO-Paare freigegeben.")
    # Wichtig: Dictionary leeren, falls das Skript theoretisch weiterlaufen würde
    pump_gpio_devices.clear()


# --- Hauptskript ---
if __name__ == "__main__":
    initialization_error_occurred = False
    try:
        print("Lade Konfiguration...")
        pump_configs = load_config(CONFIG_FILE)
        if pump_configs is None:
            # Fehler wurde bereits in load_config ausgegeben
             sys.exit(1) # Beenden, da Konfiguration fehlt/fehlerhaft

        print("\nInitialisiere GPIO-Pins für die Pumpen...")
        # Fehlerbehandlung für die gesamte Initialisierungsphase
        for config in pump_configs:
            if not setup_pump_gpio(config):
                 # setup_pump_gpio hat den Fehler schon gemeldet
                 print("  ! Initialisierung fehlgeschlagen.")
                 initialization_error_occurred = True
                 break # Schleife abbrechen bei erstem Fehler

        if initialization_error_occurred:
            print("\nFehler während der Initialisierung aufgetreten.")
            # Stoppe alle bis hierhin erfolgreich initialisierten Pumpen
            stop_all_pumps()
            # Räume die erfolgreich initialisierten Pins auf
            cleanup_gpio()
            print("Programm aufgrund Initialisierungsfehler beendet.")
            sys.exit(1) # Mit Fehlercode beenden

        if not pump_gpio_devices:
           print("\nKeine Pumpen konnten erfolgreich initialisiert werden. Skript wird beendet.")
           sys.exit(1)

        print(f"\nStarte Pumpentest (jede Pumpe {TEST_DURATION_SECONDS}s vorwärts, dann {TEST_DURATION_SECONDS}s rückwärts)...")

        # Haupt-Testschleife mit Fehlerbehandlung
        for pump_id, (power_pin, direction_pin) in pump_gpio_devices.items():
            # Finde den zugewiesenen Liquid-Namen für die Ausgabe
            pump_label = f"Pumpe {pump_id}"
            assigned_liquid = next((p.get('assigned_liquid', 'N/A') for p in pump_configs if p.get('id') == pump_id), 'Unbekannt')
            if assigned_liquid != 'N/A':
                pump_label += f" ({assigned_liquid})"

            print(f"\nTeste {pump_label}...")

            # Vorwärtslauf
            run_forward(power_pin, direction_pin, TEST_DURATION_SECONDS)

            time.sleep(DELAY_BETWEEN_DIRECTIONS)

            # Rückwärtslauf
            run_backward(power_pin, direction_pin, TEST_DURATION_SECONDS)

            print(f"Test für {pump_label} abgeschlossen.")
            time.sleep(DELAY_BETWEEN_PUMPS)

        print("\nAlle Pumpentests erfolgreich abgeschlossen.")

    except KeyboardInterrupt:
        print("\nNOT-STOPP: Test durch Benutzer abgebrochen (Strg+C).")
        # Stoppe alle Pumpen sofort
        stop_all_pumps()
    except Exception as e:
        print(f"\nNOT-STOPP: Ein unerwarteter Fehler während des Tests ist aufgetreten: {e}")
        # Stoppe alle Pumpen sofort
        stop_all_pumps()
    finally:
        # Sicherstellen, dass die Pins *immer* aufgeräumt werden,
        # egal ob Erfolg, Abbruch oder Fehler.
        cleanup_gpio()
        print("Programm beendet.")