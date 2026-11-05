# ⚡ GalaxyBoost

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![Wear OS](https://img.shields.io/badge/Platform-Wear%20OS%20%7C%20One%20UI%20Watch-green.svg)](https://wearos.google.com/)
[![Zero Dependencies](https://img.shields.io/badge/Dependencies-Standard%20Library%20Only-brightgreen.svg)]()

> **GalaxyBoost es la suite definitiva de optimización, debloat seguro, aceleración de aplicaciones (AOT ARM64) y calibración de batería para Samsung Galaxy Watch y smartwatches Wear OS.**

Sin instalaciones complejas ni librerías externas. Funciona directamente en **Windows, macOS y Linux** a través de la librería estándar de Python y ADB inalámbrico.

---

## 📋 Tabla de Contenidos

* [Características Principales](#-características-principales)
* [Dispositivos Compatibles](#-dispositivos-compatibles)
* [Requisitos Previos](#-requisitos-previos)
* [Instalación Rápida](#-instalación-rápida)
* [Guía de Preparación del Reloj](#-guía-de-preparación-del-reloj)
* [Uso de la Herramienta](#-uso-de-la-herramienta)
* [Módulos de Optimización](#-módulos-de-optimización)
* [Respaldo y Reversibilidad (Rollback)](#-respaldo-y-reversibilidad-rollback)
* [Preguntas Frecuentes (FAQ)](#-preguntas-frecuentes-faq)
* [Licencia](#-licencia)

---

## 🚀 Características Principales

* **Cero Dependencias Externas:** Corre directamente con `python3` (sin necesidad de `pip install`).
* **Conexión Guiada Inalámbrica:** Asistente integrado para emparejar y conectar tu reloj vía Wi-Fi por ADB sin cables.
* **Aceleración de Interfaz:** Ajuste de animaciones a `0.75x (Sweet Spot)` o `0.5x` para eliminar tirones sin perder suavidad visual.
* **Compilación Nativa ARM64 (AOT con `-m speed`):** Pre-compila aplicaciones pesadas (WhatsApp, Spotify, Google Wallet, Samsung Health) para que abran al instante sin compilación en tiempo real.
* **Congelador de Kernel (Linux cgroups v2):** Activa el *Cached Apps Freezer* para reducir a 0% el uso de CPU de aplicaciones en segundo plano.
* **Debloat Seguro y 100% Reversible:** Desactiva Bixby completo, Samsung Pay (para usuarios de Google Wallet), 8 daemons de telemetría oculta, navegador web, reproductor de video y carátulas animadas pesadas.
* **Notificación Inteligente:** Vibra al recibir un mensaje sin encender la pantalla; solo la enciende si giras la muñeca para verla.
* **Mantenimiento Flash Storage:** Ejecución de `sm fstrim` para sanear bloques de almacenamiento y purga de cachés infladas.
* **Calibración de Batería y Red:** Apagado de escaneo continuo Wi-Fi/BLE y priorización de enlace Bluetooth de bajo consumo.
* **Sistema de Respaldo Automático:** Genera un snapshot en formato JSON con la configuración exacta antes de realizar cualquier cambio.

---

## ⌚ Dispositivos Compatibles

| Familia de Smartwatch | Nivel de Compatibilidad | Notas |
| :--- | :---: | :--- |
| **Samsung Galaxy Watch 7 / Ultra** | 100% | Wear OS 5 / One UI 6 Watch |
| **Samsung Galaxy Watch 6 / 6 Classic** | 100% | Wear OS 4 & 5 / One UI Watch |
| **Samsung Galaxy Watch 5 / 5 Pro** | 100% | Wear OS 3.5, 4 y 5 |
| **Samsung Galaxy Watch 4 / 4 Classic** | 100% | Wear OS 3.5 & 4 |
| **Google Pixel Watch 1, 2 y 3** | 95% | AOT, Animaciones, Kernel y TRIM compatibles |
| **OnePlus Watch 2 / 2R** | 95% | AOT, Animaciones, Kernel y TRIM compatibles |
| **Xiaomi Watch 2 / Pro** | 95% | AOT, Animaciones, Kernel y TRIM compatibles |

---

## 🛠️ Requisitos Previos

Tener instalado **Python 3.8+** y **ADB (Android Debug Bridge)** en tu computadora:

* **macOS:**
  ```bash
  brew install --cask android-platform-tools
  ```
* **Windows:**
  ```powershell
  winget install Google.PlatformTools
  # O con Chocolatey:
  choco install adb
  ```
* **Linux (Ubuntu/Debian):**
  ```bash
  sudo apt install adb
  ```

---

## 📥 Instalación Rápida

1. Clona este repositorio o descárgalo como archivo ZIP:
   ```bash
   git clone https://github.com/ZizuPM/GalaxyBoost.git
   cd GalaxyBoost
   ```
2. Asegúrate de que el script tenga permisos de ejecución (en macOS/Linux):
   ```bash
   chmod +x watch_optimizer.py
   ```

---

## 📱 Guía de Preparación del Reloj

Ambos dispositivos (tu computadora y tu smartwatch) deben estar en la **misma red Wi-Fi**:

1. En tu reloj, ve a **Ajustes > Acerca del reloj > Información de software**.
2. Pulsa **7 veces seguidas** sobre **Versión de software** hasta ver el mensaje: *"El modo de desarrollador está activado"*.
3. Vuelve a **Ajustes** y entra en la nueva sección **Opciones de desarrollador**.
4. Activa **Depuración de ADB**.
5. Baja un poco y activa **Depuración inalámbrica**.
6. Entra en **Vincular nuevo dispositivo** (*Pair new device*):
   * Anota la **Dirección IP y puerto de vinculación** (ej. `192.168.1.50:38491`).
   * Anota el **Código de vinculación de 6 dígitos** (ej. `123456`).

---

## 💻 Uso de la Herramienta

Inicia GalaxyBoost:

```bash
python3 watch_optimizer.py
```

Verás el menú interactivo con detección automática del reloj:

```text
  ╔═══════════════════════════════════════════════════════════════╗
  ║                   ⚡ GALAXYBOOST OPTIMIZER ⚡                 ║
  ║      Optimización, Debloat, Aceleración ART y Rendimiento     ║
  ╚═══════════════════════════════════════════════════════════════╝

● Dispositivo Conectado: 192.168.1.50:41235 (samsung SM-R920)
  Batería: 85% | Wear OS / Android: 16 | RAM Disponible: 285 MB de 1360 MB
  Animaciones: 0.75x (Ventana) | 0.75x (Transición) | 0.75x (Animador)

─── Menú Principal ───
  1. [Conectar] Asistente de Conexión Wi-Fi / Vincular Reloj
  2. [Perfiles Rápidos] Aplicar perfil predefinido (Seguro / Equilibrado / Extremo)
  3. [Personalizado] Seleccionar qué optimizar de forma granular
  4. [Diagnóstico] Análisis en vivo de RAM, batería y procesos
  5. [Copia de Respaldo] Crear snapshot manual en JSON
  6. [Restaurar / Rollback] Reactivar paquetes y volver a valores de fábrica
  7. [Desconectar] Cerrar sesión ADB de forma limpia
  0. Salir
```

---

## ⚙️ Módulos de Optimización

El menú personalizado te permite seleccionar exactamente qué aplicar:

### 1. Perfiles de Debloat
* **Seguro (Zero-Risk):** Desactiva telemetría oculta (`dqagent`, `selfdiagnostics`, `runestone`, `retailattractloop`, `knox`, etc.). Cero impacto en apps de usuario.
* **Equilibrado (Recomendado):** Desactiva Bixby completo (ahorra ~100MB de RAM y libera el micrófono), Samsung Pay (para usuarios de Google Wallet), navegador web y carátulas animadas.
* **Extremo:** Desactiva utilidades redundantes secundarias para máxima duración de batería.

### 2. Aceleración ART Ahead-Of-Time (AOT)
Convierte el código bytecode de tus aplicaciones pesadas a instrucciones nativas ARM64:
* `WhatsApp`
* `Spotify`
* `Google Wallet`
* `Google Assistant`
* `Samsung Health`
* `SystemUI`

### 3. Ajustes de Sistema y Kernel
* **`cached_apps_freezer = enabled`**: Congela apps en caché para evitar consumo fantasma de CPU.
* **`wifi_scan_always_enabled = 0`**: Elimina búsquedas continuas de redes Wi-Fi en segundo plano.
* **`clockwork_wifi_setting = auto`**: Prioriza el Bluetooth de bajo consumo del teléfono y solo activa Wi-Fi cuando te alejas del celular.
* **Notificación Inteligente:** Vibra con pantalla apagada; solo enciende al girar muñeca.
* **Pantalla a 20s y Vibración Suave:** Desactiva vibración del teclado numérico y deja solo alertas de llamadas y mensajes reales.

---

## 🛡️ Respaldo y Reversibilidad (Rollback)

Todo cambio realizado es **100% reversible** y no altera particiones protegidas de sistema (`/system`):
* Antes de aplicar cualquier perfil, el script guarda un archivo JSON en la carpeta `backups/` con el modelo del reloj y la fecha.
* En cualquier momento puedes seleccionar la opción **[Restaurar / Rollback]** para reactivar todos los paquetes o restaurar las animaciones a `1.0x` de fábrica con un solo clic.

---

## ❓ Preguntas Frecuentes (FAQ)

#### ¿Esto anula la garantía o activa Knox (0x1)?
**No.** No se utiliza root, no se desbloquea el bootloader y no se modifica el firmware. Todo se realiza mediante comandos estándar de usuario de Android (`pm disable-user`).

#### ¿Se borran mis datos de salud, pasos o entrenamientos?
**No.** Las aplicaciones de salud como **Samsung Health** y **Google Fit** se mantienen intactas.

#### ¿Por qué la batería puede parecer que baja más rápido al principio?
1. **Verifica haber apagado la Depuración Inalámbrica:** Si dejas la depuración activa en *Opciones de desarrollador*, el daemon de ADB se queda escuchando por Wi-Fi y no deja dormir al reloj.
2. **Always On Display (AOD):** Si activaste AOD, la pantalla está encendida todo el día, lo cual gasta entre un 20% y 30% más de batería que tenerla apagada.

---

## 📄 Licencia

Distribuido bajo la Licencia **MIT**. Consulta el archivo [`LICENSE`](LICENSE) para más detalles.

Desarrollado por **Zinedine Patiño Maza (@ZizuPM)**. ¡Contribuciones y PRs son bienvenidos!

