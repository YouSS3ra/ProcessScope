
from dataclasses import dataclass
import time

import psutil
from winotify import Notification, audio


# ============================================================
# 1. CONFIGURATION DU MOTEUR
# ============================================================

@dataclass
class MonitoringConfig:
    """
    Contient les paramètres utilisés par le moteur
    de surveillance des processus.
    """

    inactive_threshold: int = 300
    cpu_usage_threshold: float = 5.0
    memory_usage_threshold: float = 50.0
    monitoring_interval: int = 5
    alert_sound: str = "default"


# ============================================================
# 2. VALIDATION DES PARAMÈTRES
# ============================================================

def validate_interval(value):
    """
    Vérifie que l'intervalle de surveillance est
    un entier strictement positif.
    """

    try:
        interval = int(value)
    except (TypeError, ValueError):
        raise ValueError(
            "L'intervalle doit être un nombre entier."
        )

    if interval < 1:
        raise ValueError(
            "L'intervalle doit être supérieur ou égal à 1 seconde."
        )

    return interval


def validate_settings(inactive_duration, cpu_threshold, memory_threshold):
    """
    Valide les trois paramètres de détection.

    Retourne :
        (durée_inactivité, seuil_CPU, seuil_RAM)
    """

    try:
        duration = int(inactive_duration)

        cpu = float(
            str(cpu_threshold).replace(",", ".")
        )

        memory = float(
            str(memory_threshold).replace(",", ".")
        )

    except (TypeError, ValueError):
        raise ValueError(
            "Les paramètres doivent être des valeurs numériques valides."
        )

    if duration < 1:
        raise ValueError(
            "La durée d'inactivité doit être supérieure ou égale à 1 seconde."
        )

    if not 0 <= cpu <= 100:
        raise ValueError(
            "Le seuil CPU doit être compris entre 0 et 100 %."
        )

    if memory < 0:
        raise ValueError(
            "Le seuil RAM doit être positif ou nul."
        )

    return duration, cpu, memory


# ============================================================
# 3. GESTION DES SONS
# ============================================================

SOUND_OPTIONS = {
    "default": audio.Default,
    "critical": audio.SMS,
    "reminder": audio.Reminder,
}


def resolve_sound(sound_choice):
    """
    Retourne le son Windows correspondant au choix.
    """

    if sound_choice not in SOUND_OPTIONS:
        raise ValueError(
            "Son inconnu. Choix disponibles : default, critical, reminder."
        )

    return SOUND_OPTIONS[sound_choice]


# ============================================================
# 4. NOTIFICATION WINDOWS
# ============================================================

def notify_user(process_name, pid, inactive_duration, alert_sound="default"):
    """
    Envoie une notification Windows lorsqu'un processus
    répond aux critères de surveillance.

    Retourne True si la notification a été envoyée,
    False en cas d'échec.
    """

    try:
        selected_sound = resolve_sound(alert_sound)

        notification = Notification(
            app_id="ProcessScope",
            title="Alerte : faible activité du processus",
            msg=(
                f"Processus : {process_name}\n"
                f"PID : {pid}\n"
                f"Inactivité : {int(inactive_duration)} secondes"
            ),
            duration="short"
        )

        notification.set_audio(selected_sound, loop=False)
        notification.show()

        print(
            f"[ALERTE] {process_name} (PID: {pid}) "
            f"- Inactivité : {int(inactive_duration)} s"
        )

        return True

    except Exception as error:
        print(
            f"[ERREUR NOTIFICATION] "
            f"Impossible de notifier le processus {pid} : {error}"
        )

        return False


# ============================================================
# 5. MOTEUR PRINCIPAL DE SURVEILLANCE
# ============================================================

def monitor_processes(stop_event, config):
    """
    Surveille les processus Windows.

    Paramètres :
        stop_event :
            Objet compatible avec is_set() et wait().
            Il permet d'interrompre la surveillance.

        config :
            Instance de MonitoringConfig contenant
            les paramètres de surveillance.

    Cette fonction ne dépend d'aucune interface graphique.
    Elle pourra donc être utilisée par le GUI et le CLI.
    """

    process_states = {}

    print("[ProcessScope] Surveillance démarrée.")

    try:

        while not stop_event.is_set():

            active_processes = set()

            for process in psutil.process_iter(
                ["pid", "name", "create_time"]
            ):

                try:

                    pid = process.info["pid"]
                    process_name = process.info["name"] or "Inconnu"
                    creation_time = process.info["create_time"]

                    if creation_time is None:
                        continue

                    process_key = (pid, creation_time)
                    active_processes.add(process_key)

                    # ------------------------------------------------
                    # Première observation du processus
                    # ------------------------------------------------

                    if process_key not in process_states:

                        process.cpu_percent(interval=None)

                        process_states[process_key] = {
                            "idle_since": None,
                            "notified": False
                        }

                        continue

                    # ------------------------------------------------
                    # Mesure CPU et mémoire
                    # ------------------------------------------------

                    cpu_usage = process.cpu_percent(interval=None)

                    memory_info = process.memory_info()
                    memory_mb = memory_info.rss / (1024 * 1024)

                    state = process_states[process_key]

                    # ------------------------------------------------
                    # Détection de l'activité
                    # ------------------------------------------------

                    if cpu_usage >= config.cpu_usage_threshold:

                        # Le processus est actif.
                        # On réinitialise sa période d'inactivité.

                        state["idle_since"] = None
                        state["notified"] = False

                    else:

                        # Le processus est considéré comme peu actif.

                        if state["idle_since"] is None:

                            state["idle_since"] = time.monotonic()

                        inactive_duration = (
                            time.monotonic() - state["idle_since"]
                        )

                        # ------------------------------------------------
                        # Vérification des conditions d'alerte
                        # ------------------------------------------------

                        if (
                            inactive_duration >= config.inactive_threshold
                            and memory_mb >= config.memory_usage_threshold
                            and not state["notified"]
                        ):

                            notification_sent = notify_user(
                                process_name=process_name,
                                pid=pid,
                                inactive_duration=inactive_duration,
                                alert_sound=config.alert_sound
                            )

                            if notification_sent:
                                state["notified"] = True

                except (
                    psutil.NoSuchProcess,
                    psutil.AccessDenied,
                    psutil.ZombieProcess,
                    ProcessLookupError
                ):
                    continue

                except Exception as error:
                    print(
                        f"[ERREUR] Processus {process.info.get('pid')} : {error}"
                    )

            # --------------------------------------------------------
            # Nettoyage des processus terminés
            # --------------------------------------------------------

            terminated_processes = (
                set(process_states.keys()) - active_processes
            )

            for process_key in terminated_processes:
                del process_states[process_key]

            # --------------------------------------------------------
            # Attente avant le prochain cycle
            # --------------------------------------------------------

            stop_event.wait(config.monitoring_interval)

    except Exception as error:

        print(
            f"[ERREUR MOTEUR] La surveillance a rencontré un problème : {error}"
        )

        raise

    finally:

        print("[ProcessScope] Surveillance arrêtée.")
