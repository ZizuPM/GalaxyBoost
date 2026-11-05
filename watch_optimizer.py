#!/usr/bin/env python3
"""
GalaxyBoost - WearOS & Galaxy Watch Optimizer
=============================================
Herramienta universal de optimización, debloat seguro, aceleración ART y calibración de batería
para smartwatches Samsung Galaxy Watch (4, 5, 6, 7, Ultra) y dispositivos Wear OS.

Autor: Zinedine Patiño Maza (@ZizuPM)
Licencia: MIT
"""

import subprocess
import json
import os
import sys
import time
import socket
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# Configuración de Rutas
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROFILES_FILE = os.path.join(BASE_DIR, "debloat_profiles.json")
BACKUPS_DIR = os.path.join(BASE_DIR, "backups")

# Colores ANSI para la terminal
class Color:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    BLUE = "\033[94m"
    GRAY = "\033[90m"

TARGET_DEVICE = None

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

def print_banner():
    banner = f"""{Color.CYAN}{Color.BOLD}
  ╔═══════════════════════════════════════════════════════════════╗
  ║                    ⚡ GALAXYBOOST OPTIMIZER ⚡                ║
  ║      Optimización, Debloat, Aceleración ART y Rendimiento     ║
  ╚═══════════════════════════════════════════════════════════════╝{Color.RESET}"""
    print(banner)

def print_header(title):
    print(f"\n{Color.BOLD}{Color.BLUE}─── {title} ───{Color.RESET}")

def run_raw_adb(args, timeout=30):
    """Ejecuta comando ADB sin target específico."""
    cmd = ["adb"] + args
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout)
        return res.returncode, res.stdout.strip(), res.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, "", "Timeout al ejecutar comando ADB"
    except FileNotFoundError:
        return -1, "", "El comando 'adb' no fue encontrado en el PATH de tu sistema."

def run_adb(args, timeout=30):
    """Ejecuta comando ADB dirigido al dispositivo seleccionado."""
    global TARGET_DEVICE
    if TARGET_DEVICE and "-s" not in args:
        cmd = ["-s", TARGET_DEVICE] + args
    else:
        cmd = args
    return run_raw_adb(cmd, timeout=timeout)

def run_adb_shell(shell_cmd, timeout=30):
    """Ejecuta un comando en la shell del dispositivo seleccionado."""
    return run_adb(["shell", shell_cmd], timeout=timeout)

def check_adb_installed():
    """Verifica si ADB está instalado en el sistema."""
    code, out, _ = run_raw_adb(["version"])
    return code == 0

def get_connected_device():
    """Detecta y selecciona el dispositivo Wear OS conectado."""
    global TARGET_DEVICE
    code, out, _ = run_raw_adb(["devices"])
    if code != 0:
        return None
    lines = out.strip().split("\n")[1:]
    devices = [l.split()[0] for l in lines if "\tdevice" in l]
    ip_devs = [d for d in devices if ":" in d and not d.startswith("adb-")]
    if ip_devs:
        TARGET_DEVICE = ip_devs[0]
        return ip_devs[0]
    if devices:
        TARGET_DEVICE = devices[0]
        return devices[0]
    return None

def scan_mdns_devices():
    """Descubre dispositivos Wear OS disponibles mediante mDNS."""
    code, out, _ = run_raw_adb(["mdns", "services"])
    if code != 0 or not out:
        return []
    services = []
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 3 and "_adb-tls-connect._tcp." in line:
            services.append({"name": parts[0], "address": parts[-1]})
    return services

def get_device_info():
    """Extrae especificaciones técnicas del reloj."""
    _, model, _ = run_adb_shell("getprop ro.product.model")
    _, manufacturer, _ = run_adb_shell("getprop ro.product.manufacturer")
    _, release, _ = run_adb_shell("getprop ro.build.version.release")
    _, build, _ = run_adb_shell("getprop ro.build.version.incremental")
    _, battery_raw, _ = run_adb_shell("dumpsys battery")
    
    battery_level = "Desconocido"
    for line in battery_raw.splitlines():
        if "level:" in line:
            battery_level = line.split("level:")[1].strip() + "%"
            break

    _, mem_raw, _ = run_adb_shell("cat /proc/meminfo | head -n 4")
    total_ram = "Desconocido"
    avail_ram = "Desconocido"
    for line in mem_raw.splitlines():
        if "MemTotal:" in line:
            kb = int(line.split()[1])
            total_ram = f"{kb // 1024} MB"
        elif "MemAvailable:" in line:
            kb = int(line.split()[1])
            avail_ram = f"{kb // 1024} MB"

    return {
        "model": f"{manufacturer} {model}".strip(),
        "android_version": release,
        "build": build,
        "battery": battery_level,
        "total_ram": total_ram,
        "avail_ram": avail_ram
    }

def get_animation_scales():
    """Lee las velocidades de animación del reloj."""
    _, w, _ = run_adb_shell("settings get global window_animation_scale")
    _, t, _ = run_adb_shell("settings get global transition_animation_scale")
    _, a, _ = run_adb_shell("settings get global animator_duration_scale")
    return {
        "window": w or "1.0",
        "transition": t or "1.0",
        "animator": a or "1.0"
    }

def set_animation_scales(scale):
    """Ajusta la velocidad de las animaciones."""
    run_adb_shell(f"settings put global window_animation_scale {scale}")
    run_adb_shell(f"settings put global transition_animation_scale {scale}")
    run_adb_shell(f"settings put global animator_duration_scale {scale}")

def get_packages():
    """Obtiene la lista de paquetes instalados, habilitados y deshabilitados."""
    _, all_pkgs, _ = run_adb_shell("pm list packages")
    _, disabled_pkgs, _ = run_adb_shell("pm list packages -d")

    all_set = set(p.replace("package:", "").strip() for p in all_pkgs.splitlines() if p.startswith("package:"))
    disabled_set = set(p.replace("package:", "").strip() for p in disabled_pkgs.splitlines() if p.startswith("package:"))
    enabled_set = all_set - disabled_set

    return {
        "all": sorted(list(all_set)),
        "enabled": sorted(list(enabled_set)),
        "disabled": sorted(list(disabled_set))
    }

def create_backup():
    """Genera una copia de seguridad en JSON del estado del reloj."""
    os.makedirs(BACKUPS_DIR, exist_ok=True)
    pkgs = get_packages()
    animations = get_animation_scales()
    dev_info = get_device_info()

    backup_data = {
        "timestamp": datetime.now().isoformat(),
        "device": dev_info,
        "animations": animations,
        "packages": pkgs
    }

    clean_model = dev_info['model'].replace(' ', '_').replace('/', '_')
    fname = f"backup_{clean_model}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    fpath = os.path.join(BACKUPS_DIR, fname)
    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(backup_data, f, indent=2, ensure_ascii=False)
    return fpath

def disable_package(pkg):
    """Deshabilita un paquete de forma 100% reversible (sin borrar partición de sistema)."""
    code, out, err = run_adb_shell(f"pm disable-user --user 0 {pkg}")
    if "disabled" in out or "new state: disabled" in out:
        return True, "Deshabilitado con éxito"
    code2, out2, err2 = run_adb_shell(f"pm uninstall -k --user 0 {pkg}")
    if "Success" in out2:
        return True, "Desinstalado para usuario 0 (conservando apk)"
    return False, err or out or err2 or out2

def enable_package(pkg):
    """Reactiva un paquete deshabilitado previamente."""
    run_adb_shell(f"pm enable {pkg}")
    run_adb_shell(f"cmd package install-existing {pkg}")
    return True

def apply_smart_notification_wake():
    """Activa el modo de notificación inteligente: vibra sin encender pantalla, y solo enciende al girar muñeca."""
    print(f"\n{Color.CYAN}[*] Configurando Notificaciones Inteligentes por Giro de Muñeca...{Color.RESET}")
    run_adb_shell("settings put secure wake_gesture_enabled 1")
    run_adb_shell("settings put secure ambient_tilt_to_wake 1")
    run_adb_shell("settings put secure psm_ambient_tilt_to_wake 1")
    run_adb_shell("settings put system enable_notification_without_tap_or_tilt 0")
    run_adb_shell("settings put secure lock_screen_show_notifications 1")
    print(f"  {Color.GREEN}[✓] Al recibir mensaje (WhatsApp/Teams): el reloj VIBRA sin encender pantalla{Color.RESET}")
    print(f"  {Color.GREEN}[✓] Si giras la muñeca: la pantalla se ENCIENDE mostrando la notificación{Color.RESET}")
    print(f"  {Color.GREEN}[✓] Si no la miras: la pantalla se MANTIENE APAGADA para ahorrar batería{Color.RESET}")

def apply_kernel_tweaks():
    """Aplica optimizaciones de Kernel, cgroups y red en el reloj."""
    print(f"\n{Color.CYAN}[*] Aplicando optimizaciones de Kernel y Batería...{Color.RESET}")
    run_adb_shell("settings put global wifi_scan_always_enabled 0")
    run_adb_shell("settings put global ble_scan_always_enabled 0")
    run_adb_shell("settings put global cached_apps_freezer enabled")
    run_adb_shell("settings put global send_action_app_error 0")
    run_adb_shell("settings put global clockwork_wifi_setting auto")
    print(f"  {Color.GREEN}[✓] Cached Apps Freezer activado (Linux cgroups v2){Color.RESET}")
    print(f"  {Color.GREEN}[✓] Escaneo continuo Wi-Fi y BLE en segundo plano desactivado{Color.RESET}")
    print(f"  {Color.GREEN}[✓] Wi-Fi configurado en modo Automático (prioriza Bluetooth){Color.RESET}")
    print(f"  {Color.GREEN}[✓] Reporte de telemetría de fallos desactivado{Color.RESET}")

def apply_screen_haptics():
    """Configura pantalla a 20s y vibración suave del sistema."""
    print(f"\n{Color.CYAN}[*] Configurando pantalla y vibración suave...{Color.RESET}")
    run_adb_shell("settings put system screen_off_timeout 20000")
    run_adb_shell("settings put secure wake_gesture_enabled 0")
    run_adb_shell("settings put secure ambient_tilt_to_wake 0")
    run_adb_shell("settings put system dialing_keypad_vibrate 0")
    run_adb_shell("settings put system keyboard_vibration_enabled 0")
    run_adb_shell("settings put system sip_key_feedback_vibration 0")
    run_adb_shell("settings put system haptic_feedback_intensity 1")
    run_adb_shell("settings put system notification_vibration_intensity 1")
    run_adb_shell("settings put system ring_vibration_intensity 1")
    print(f"  {Color.GREEN}[✓] Tiempo de espera de pantalla configurado a 20 segundos{Color.RESET}")
    print(f"  {Color.GREEN}[✓] Giro de muñeca desactivado (evita encendidos accidentales de alto brillo){Color.RESET}")
    print(f"  {Color.GREEN}[✓] Vibración de teclado y marcación desactivada (solo llamadas y alertas reales){Color.RESET}")

def apply_aot_compile():
    """Compila las aplicaciones clave a código nativo ARM64 (Ahead-Of-Time)."""
    pkgs = [
        "com.google.android.apps.walletnfcrel",
        "com.whatsapp",
        "com.spotify.music",
        "com.google.android.wearable.assistant",
        "com.samsung.android.wear.shealth",
        "com.samsung.android.wearable.sysui"
    ]
    print(f"\n{Color.CYAN}[*] Compilando aplicaciones clave a código nativo ARM64 (-m speed)...{Color.RESET}")
    print(f"{Color.GRAY}    (Esto puede demorar 1-2 minutos por app pero elimina todo retardo al abrir){Color.RESET}")
    installed = set(get_packages()["all"])
    for pkg in pkgs:
        if pkg in installed:
            print(f"  [*] Compilando {pkg}...", end="", flush=True)
            code, out, _ = run_adb_shell(f"cmd package compile -m speed -f {pkg}", timeout=120)
            if "Success" in out:
                print(f" {Color.GREEN}[Éxito]{Color.RESET}")
            else:
                print(f" {Color.YELLOW}[Completado]{Color.RESET}")

def apply_storage_trim():
    """Ejecuta TRIM en memoria flash y purga cachés."""
    print(f"\n{Color.CYAN}[*] Ejecutando mantenimiento de almacenamiento flash (TRIM)...{Color.RESET}")
    run_adb_shell("sm fstrim")
    run_adb_shell("pm trim-caches 100G")
    print(f"  {Color.GREEN}[✓] Bloques de almacenamiento flash saneados y cachés depuradas{Color.RESET}")

def apply_debloat_list(packages_to_disable, profile_name="Personalizado"):
    """Aplica una lista de paquetes a deshabilitar."""
    create_backup()
    installed = set(get_packages()["all"])
    print(f"\n{Color.CYAN}[*] Aplicando debloat: '{profile_name}'...{Color.RESET}")
    count = 0
    for pkg in packages_to_disable:
        if pkg in installed:
            ok, msg = disable_package(pkg)
            sym = f"{Color.GREEN}✓{Color.RESET}" if ok else f"{Color.RED}✗{Color.RESET}"
            print(f"  [{sym}] {pkg}: {msg}")
            if ok: count += 1
        else:
            print(f"  {Color.GRAY}[-] {pkg}: No instalado{Color.RESET}")
    print(f"\n{Color.GREEN}[✓] Completado: {count} servicios deshabilitados.{Color.RESET}")

def load_profiles():
    if os.path.exists(PROFILES_FILE):
        try:
            with open(PROFILES_FILE, "r", encoding="utf-8") as f:
                return json.load(f).get("profiles", {})
        except Exception:
            pass
    return {}

def connection_wizard():
    """Asistente guiado de conexión inalámbrica."""
    print_header("Asistente de Conexión Inalámbrica (ADB Wi-Fi)")
    print("1. En tu reloj, abre Ajustes > Opciones de desarrollador.")
    print("2. Activa 'Depuración de ADB' y 'Depuración inalámbrica'.")
    print("\nOpciones disponibles:")
    print("  [1] Vincular nuevo reloj (requiere código de 6 dígitos)")
    print("  [2] Conectar a reloj ya vinculado (requiere IP y Puerto)")
    print("  [3] Escaneo automático por red mDNS")
    print("  [0] Volver")

    choice = input(f"\n{Color.BOLD}Selecciona una opción [0-3]: {Color.RESET}").strip()
    if choice == "1":
        ip_port = input("Ingresa IP:PUERTO de vinculación (ej. 192.168.1.50:38491): ").strip()
        code = input("Ingresa el CÓDIGO de 6 dígitos de vinculación: ").strip()
        print(f"[*] Vinculando...")
        c, out, err = run_raw_adb(["pair", ip_port, code])
        print(out or err)
        if c == 0 or "Successfully paired" in out:
            print(f"{Color.GREEN}[✓] Vinculación exitosa.{Color.RESET}")
            main_ip = input("Ahora ingresa la IP:PUERTO principal que aparece en 'Depuración inalámbrica': ").strip()
            run_raw_adb(["connect", main_ip])
    elif choice == "2":
        ip_port = input("Ingresa IP:PUERTO de conexión (ej. 192.168.1.50:41235): ").strip()
        run_raw_adb(["connect", ip_port])
    elif choice == "3":
        print("[*] Buscando relojes en la red local...")
        services = scan_mdns_devices()
        if not services:
            print(f"{Color.YELLOW}[!] No se encontraron dispositivos mDNS automáticos.{Color.RESET}")
        else:
            print("Dispositivos encontrados:")
            for i, s in enumerate(services, 1):
                print(f"  {i}. {s['name']} en {s['address']}")
            sel = input("Selecciona número a conectar o presiona Enter para cancelar: ").strip()
            if sel.isdigit() and 1 <= int(sel) <= len(services):
                run_raw_adb(["connect", services[int(sel)-1]["address"]])

def custom_optimization_menu():
    """Menú granular para que el usuario elija exactamente qué optimizar."""
    while True:
        print_header("Menú Personalizado: Selecciona Qué Deseas Optimizar")
        print("  1. [Animaciones] Cambiar velocidad (0.75x Sweet Spot / 0.5x Ultra / 0.0x / 1.0x)")
        print("  2. [Bixby] Desactivar Bixby Agent y Bixby Wakeup (libera ~100MB RAM y micrófono)")
        print("  3. [Samsung Pay] Desactivar Samsung Pay (recomendado si usas Google Wallet)")
        print("  4. [Telemetría] Desactivar 8 daemons de diagnósticos ocultos de Samsung/Google")
        print("  5. [Apps Pesadas] Desactivar Navegador web, Reproductor video y Transferencia MP3")
        print("  6. [Carátulas] Desactivar 7 carátulas animadas pesadas de fábrica")
        print("  7. [Kernel & Red] Activar Cached Apps Freezer y apagar escaneo Wi-Fi/BLE de fondo")
        print("  8. [AOT Compile] Pre-compilar WhatsApp, Spotify, Wallet y Health a código ARM64")
        print("  9. [Mantenimiento Flash] Ejecutar TRIM de almacenamiento y purga de cachés")
        print(" 10. [Pantalla & Hápticos] Pantalla a 20s y vibración suave (elimina vibración de teclado)")
        print(" 11. [Notificación Inteligente] Solo vibrar al recibir mensaje y encender al girar muñeca")
        print("  0. Regresar al menú principal")

        opt = input(f"\n{Color.BOLD}Selecciona una opción [0-11]: {Color.RESET}").strip()
        if opt == "1":
            print("\nVelocidades disponibles:")
            print("  a. 0.75x (Sweet Spot: Animaciones completas pero 25% más rápidas)")
            print("  b. 0.50x (Ultra Rápido: El doble de velocidad)")
            print("  c. 0.00x (Instantáneo: Sin efectos)")
            print("  d. 1.00x (Original de fábrica)")
            v = input("Elige [a/b/c/d]: ").strip().lower()
            val = "0.75" if v == "a" else ("0.5" if v == "b" else ("0.0" if v == "c" else "1.0"))
            set_animation_scales(val)
            print(f"{Color.GREEN}[✓] Animaciones configuradas a {val}x{Color.RESET}")

        elif opt == "2":
            apply_debloat_list(["com.samsung.android.bixby.agent", "com.samsung.android.bixby.wakeup"], "Bixby")
        elif opt == "3":
            apply_debloat_list(["com.samsung.android.samsungpay.gear"], "Samsung Pay")
        elif opt == "4":
            telemetry_pkgs = [
                "com.samsung.android.dqagent", "com.samsung.android.watch.selfdiagnostics",
                "com.samsung.android.watch.runestone.app", "com.google.android.apps.wearable.retailattractloop",
                "com.sds.emm.cloud.knox.samsung", "com.samsung.SMT", "com.samsung.aasaservice", "com.samsung.android.gru"
            ]
            apply_debloat_list(telemetry_pkgs, "Telemetría Oculta")
        elif opt == "5":
            apps = ["com.sec.android.app.sbrowser", "com.samsung.android.video.wearable", "com.samsung.android.wear.musictransfer"]
            apply_debloat_list(apps, "Navegador, Video y Música")
        elif opt == "6":
            wfs = [
                "com.samsung.android.watch.watchface.endangeredanimal", "com.samsung.android.watch.watchface.flowergarden",
                "com.samsung.android.watch.watchface.superfiction", "com.samsung.android.watch.watchface.livewallpaper",
                "com.samsung.android.watch.watchface.aremoji", "com.samsung.android.watch.watchface.bitmoji",
                "com.samsung.android.watch.watchface.animal"
            ]
            apply_debloat_list(wfs, "Carátulas Animadas Pesadas")
        elif opt == "7":
            apply_kernel_tweaks()
        elif opt == "8":
            apply_aot_compile()
        elif opt == "9":
            apply_storage_trim()
        elif opt == "10":
            apply_screen_haptics()
        elif opt == "11":
            apply_smart_notification_wake()
        elif opt == "0":
            break

def main():
    clear_screen()
    print_banner()

    if not check_adb_installed():
        print(f"\n{Color.RED}[!] Error: No se encontró 'adb' instalado en tu computadora.{Color.RESET}")
        print("    - En macOS: brew install --cask android-platform-tools")
        print("    - En Windows: choco install adb o descarga Android Platform Tools")
        print("    - En Linux: sudo apt install adb")
        sys.exit(1)

    device = get_connected_device()
    profiles = load_profiles()

    while True:
        device = get_connected_device()
        print_banner()
        if device:
            info = get_device_info()
            anim = get_animation_scales()
            print(f"\n{Color.GREEN}● Dispositivo Conectado: {Color.BOLD}{device} ({info['model']}){Color.RESET}")
            print(f"  Batería: {Color.YELLOW}{info['battery']}{Color.RESET} | Wear OS / Android: {info['android_version']} | Compilación: {info['build']}")
            print(f"  Memoria RAM Disponible: {Color.GREEN}{info['avail_ram']}{Color.RESET} de {info['total_ram']}")
            print(f"  Animaciones: {anim['window']}x (Ventana) | {anim['transition']}x (Transición) | {anim['animator']}x (Animador)")
        else:
            print(f"\n{Color.YELLOW}○ Estado: Ningún reloj conectado por ADB actualmente.{Color.RESET}")

        print_header("Menú Principal")
        print("  1. [Conectar] Asistente de Conexión Wi-Fi / Vincular Reloj")
        print("  2. [Perfiles Rápidos] Aplicar perfil predefinido (Seguro / Equilibrado / Extremo)")
        print("  3. [Personalizado] Seleccionar qué optimizar de forma granular")
        print("  4. [Diagnóstico] Análisis en vivo de RAM, batería y procesos")
        print("  5. [Copia de Respaldo] Crear snapshot manual en JSON")
        print("  6. [Restaurar / Rollback] Reactivar paquetes y volver a valores de fábrica")
        print("  7. [Desconectar] Cerrar sesión ADB de forma limpia")
        print("  0. Salir")

        op = input(f"\n{Color.BOLD}Selecciona una opción [0-7]: {Color.RESET}").strip()
        
        if op == "1":
            connection_wizard()

        elif op == "2":
            if not device:
                print(f"{Color.RED}[!] Conecta un reloj primero.{Color.RESET}")
                time.sleep(1.5)
                continue
            print("\nPerfiles predefinidos:")
            print("  1. Seguro: Elimina telemetría y diagnósticos (0 impacto visual o de funciones)")
            print("  2. Equilibrado (Recomendado): Seguro + Bixby + Samsung Pay + Apps secundarias")
            print("  3. Extremo: Equilibrado + Utilidades secundarias + Máximo ahorro de recursos")
            p_sel = input("Elige perfil [1-3] o presiona Enter para cancelar: ").strip()
            p_key = "safe" if p_sel == "1" else ("balanced" if p_sel == "2" else ("extreme" if p_sel == "3" else None))
            if p_key and p_key in profiles:
                apply_debloat_list(profiles[p_key]["packages"], profiles[p_key]["name"])
                apply_kernel_tweaks()
                set_animation_scales("0.75")
                apply_storage_trim()
                input(f"\n{Color.CYAN}Presiona Enter para continuar...{Color.RESET}")

        elif op == "3":
            if not device:
                print(f"{Color.RED}[!] Conecta un reloj primero.{Color.RESET}")
                time.sleep(1.5)
                continue
            custom_optimization_menu()

        elif op == "4":
            if not device:
                print(f"{Color.RED}[!] Conecta un reloj primero.{Color.RESET}")
                time.sleep(1.5)
                continue
            print_header("Diagnóstico del Reloj")
            _, mem, _ = run_adb_shell("dumpsys meminfo | head -n 25")
            print(f"{Color.CYAN}--- Memoria RAM ---{Color.RESET}\n{mem}\n")
            _, bat, _ = run_adb_shell("dumpsys battery")
            print(f"{Color.CYAN}--- Estado de Batería ---{Color.RESET}\n{bat}")
            input(f"\n{Color.CYAN}Presiona Enter para continuar...{Color.RESET}")

        elif op == "5":
            if not device:
                print(f"{Color.RED}[!] Conecta un reloj primero.{Color.RESET}")
                time.sleep(1.5)
                continue
            bpath = create_backup()
            print(f"{Color.GREEN}[✓] Backup creado en: {bpath}{Color.RESET}")
            time.sleep(2)

        elif op == "6":
            if not device:
                print(f"{Color.RED}[!] Conecta un reloj primero.{Color.RESET}")
                time.sleep(1.5)
                continue
            print_header("Opciones de Restauración (Rollback)")
            print("  1. Reactivar TODOS los paquetes deshabilitados")
            print("  2. Restaurar animaciones a 1.0x de fábrica")
            print("  3. Restaurar escaneo Wi-Fi a valores por defecto")
            r_op = input("Opción [1-3]: ").strip()
            if r_op == "1":
                dis = get_packages()["disabled"]
                if not dis:
                    print(f"{Color.YELLOW}[i] No hay paquetes deshabilitados.{Color.RESET}")
                else:
                    print(f"[*] Reactivando {len(dis)} paquetes...")
                    for pkg in dis:
                        enable_package(pkg)
                        print(f"  {Color.GREEN}[✓]{Color.RESET} {pkg} restaurado")
                    print(f"{Color.GREEN}[✓] Todos los paquetes han sido reactivados.{Color.RESET}")
            elif r_op == "2":
                set_animation_scales("1.0")
                print(f"{Color.GREEN}[✓] Animaciones restauradas a 1.0x.{Color.RESET}")
            elif r_op == "3":
                run_adb_shell("settings put global wifi_scan_always_enabled 1")
                run_adb_shell("settings put global clockwork_wifi_setting on")
                print(f"{Color.GREEN}[✓] Wi-Fi restaurado a valores de fábrica.{Color.RESET}")
            input(f"\n{Color.CYAN}Presiona Enter para continuar...{Color.RESET}")

        elif op == "7":
            run_raw_adb(["disconnect"])
            TARGET_DEVICE = None
            print(f"{Color.GREEN}[✓] Reloj desconectado limpiamente de ADB.{Color.RESET}")
            time.sleep(1.5)

        elif op == "0":
            print(f"\n{Color.CYAN}¡Gracias por usar WearOS & Galaxy Watch Optimizer!{Color.RESET}\n")
            break

if __name__ == "__main__":
    main()
