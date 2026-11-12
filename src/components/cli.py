
import argparse
import json
import os
import subprocess
import sys
import time

from pathlib import Path

import psutil

from paths import PROJECT_ROOT

from monitor_service import (
    MonitoringConfig,
    monitor_processes,
    validate_interval,
    validate_settings,
    resolve_sound
)


# ============================================================
# 1. FICHIERS DE GESTION DU SERVICE
# ============================================================

SERVICE_DIR = PROJECT_ROOT / ".processscope"

CONFIG_FILE = SERVICE_DIR / "config.json"
PID_FILE = SERVICE_DIR / "service.json"
STOP_FILE = SERVICE_DIR / "stop.signal"
LOG_FILE = SERVICE_DIR / "service.log"


# ============================================================
# 2. OUTIL DE COMMUNICATION AVEC LE PROCESSUS
# ============================================================

class FileStopEvent:
    """
    Reproduit l'interface minimale d'un événement d'arrêt
    à l'aide d'un fichier partagé entre plusieurs processus.

    Le moteur utilise :
        is_set()
        wait(timeout)

    Cela lui permet de fonctionner sans connaître le CLI.
    """

    def is_set(self):
        return STOP_FILE.exists()

    def wait(self, timeout=None):
        """
        Attend jusqu'à timeout secondes.

        Retourne True si un arrêt a été demandé.
        Retourne False si le délai est écoulé.
        """

        if timeout is None:
            timeout = 0.2

        deadline = time.monotonic() + timeout

        while time.monotonic() < deadline:

            if self.is_set():
                return True

            remaining = deadline - time.monotonic()

            time.sleep(min(0.2, max(0, remaining)))

        return self.is_set()


# ============================================================
# 3. GESTION DE LA CONFIGURATION
# ============================================================

def save_config(config):
    """
    Enregistre la configuration dans un fichier JSON.
    """

    SERVICE_DIR.mkdir(parents=True, exist_ok=True)

    data = {
        "inactive_threshold": config.inactive_threshold,
        "cpu_usage_threshold": config.cpu_usage_threshold,
        "memory_usage_threshold": config.memory_usage_threshold,
        "monitoring_interval": config.monitoring_interval,
        "alert_sound": config.alert_sound
    }

    with CONFIG_FILE.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)


def load_config():
    """
    Charge la configuration depuis le fichier JSON.
    """

    if not CONFIG_FILE.exists():
        return MonitoringConfig()

    with CONFIG_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    config = MonitoringConfig(
        inactive_threshold=data["inactive_threshold"],
        cpu_usage_threshold=data["cpu_usage_threshold"],
        memory_usage_threshold=data["memory_usage_threshold"],
        monitoring_interval=data["monitoring_interval"],
        alert_sound=data["alert_sound"]
    )

    # Vérification des paramètres chargés.
    validate_interval(config.monitoring_interval)

    validate_settings(
        config.inactive_threshold,
        config.cpu_usage_threshold,
        config.memory_usage_threshold
    )

    resolve_sound(config.alert_sound)

    return config


# ============================================================
# 4. IDENTIFICATION DU PROCESSUS
# ============================================================

def get_service_process():
    """
    Vérifie si le processus ProcessScope existe réellement.

    Le PID seul n'est pas suffisant : Windows peut le réutiliser.
    On vérifie donc aussi la date de création.
    """

    if not PID_FILE.exists():
        return None

    try:

        with PID_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)

        pid = int(data["pid"])
        expected_creation_time = float(data["create_time"])

        process = psutil.Process(pid)

        actual_creation_time = process.create_time()

        if abs(actual_creation_time - expected_creation_time) > 0.1:
            return None

        if not process.is_running():
            return None

        return process

    except (
        FileNotFoundError,
        ProcessLookupError,
        psutil.NoSuchProcess,
        psutil.AccessDenied,
        ValueError,
        TypeError,
        KeyError,
        json.JSONDecodeError
    ):
        return None


# ============================================================
# 5. PROCESSUS DE SURVEILLANCE EN ARRIÈRE-PLAN
# ============================================================

def run_worker():
    """
    Fonction exécutée dans le processus indépendant.

    Elle charge la configuration puis lance le moteur.
    """

    SERVICE_DIR.mkdir(parents=True, exist_ok=True)

    # Enregistrement de l'identité du processus.
    current_process = psutil.Process(os.getpid())

    process_data = {
        "pid": os.getpid(),
        "create_time": current_process.create_time()
    }

    with PID_FILE.open("w", encoding="utf-8") as file:
        json.dump(process_data, file, indent=4)

    print("ProcessScope : service démarré.")
    print(f"PID : {os.getpid()}")

    stop_event = FileStopEvent()

    try:

        config = load_config()

        monitor_processes(
            stop_event=stop_event,
            config=config
        )

    except Exception as error:

        print(f"Erreur du service : {error}")

        raise

    finally:

        # Ne supprimer le fichier que si ce PID est toujours le nôtre.
        active_process = get_service_process()

        if active_process is not None and active_process.pid == os.getpid():

            try:
                PID_FILE.unlink(missing_ok=True)
            except OSError:
                pass

        STOP_FILE.unlink(missing_ok=True)

        print("ProcessScope : service terminé.")


# ============================================================
# 6. DÉMARRER LE SERVICE
# ============================================================

def start_service(args):
    """
    Prépare la configuration et démarre un processus indépendant.
    """

    SERVICE_DIR.mkdir(parents=True, exist_ok=True)

    existing_process = get_service_process()

    if existing_process is not None:

        print(
            f"ProcessScope fonctionne déjà. "
            f"PID : {existing_process.pid}"
        )

        return

    # Construction de la configuration.
    config = MonitoringConfig()

    try:

        config.monitoring_interval = validate_interval(
            args.interval if args.interval is not None
            else config.monitoring_interval
        )

        if any(
            value is not None
            for value in (args.duration, args.cpu, args.memory)
        ):

            duration, cpu, memory = validate_settings(
                args.duration if args.duration is not None
                else config.inactive_threshold,

                args.cpu if args.cpu is not None
                else config.cpu_usage_threshold,

                args.memory if args.memory is not None
                else config.memory_usage_threshold
            )

            config.inactive_threshold = duration
            config.cpu_usage_threshold = cpu
            config.memory_usage_threshold = memory

        if args.sound is not None:
            resolve_sound(args.sound)
            config.alert_sound = args.sound

        # Sauvegarder les paramètres avant le démarrage.
        save_config(config)

    except ValueError as error:

        print(f"Erreur de configuration : {error}")
        return

    # Nettoyer un ancien signal d'arrêt.
    STOP_FILE.unlink(missing_ok=True)

    # Lancer un nouveau processus Python indépendant.
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--_worker"
    ]

    try:

        log_file = LOG_FILE.open("a", encoding="utf-8")

        if os.name == "nt":

            creation_flags = (
                subprocess.DETACHED_PROCESS
                | subprocess.CREATE_NEW_PROCESS_GROUP
            )

            subprocess.Popen(
                command,
                cwd=str(Path(__file__).resolve().parent),
                stdin=subprocess.DEVNULL,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                creationflags=creation_flags,
                close_fds=True
            )

        else:

            subprocess.Popen(
                command,
                cwd=str(Path(__file__).resolve().parent),
                stdin=subprocess.DEVNULL,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                start_new_session=True
            )

        log_file.close()

        # Attendre que le processus enregistre son identité.
        for _ in range(30):

            time.sleep(0.2)

            process = get_service_process()

            if process is not None:

                print("ProcessScope démarré avec succès.")
                print(f"PID : {process.pid}")
                print(f"Intervalle : {config.monitoring_interval} s")
                print(f"Journal : {LOG_FILE}")

                return

        print(
            "Le démarrage n'a pas été confirmé. "
            f"Consultez le journal : {LOG_FILE}"
        )

    except Exception as error:

        print(f"Impossible de démarrer ProcessScope : {error}")


# ============================================================
# 7. ARRÊTER LE SERVICE
# ============================================================

def stop_service():
    """
    Demande au moteur indépendant de s'arrêter.
    """

    process = get_service_process()

    if process is None:

        print("ProcessScope n'est pas en cours d'exécution.")

        return

    STOP_FILE.touch()

    print(
        f"Demande d'arrêt envoyée au service "
        f"(PID : {process.pid})."
    )

    # Attendre la fin du processus.
    for _ in range(50):

        time.sleep(0.2)

        if get_service_process() is None:

            print("ProcessScope arrêté avec succès.")

            return

    print(
        "L'arrêt n'a pas été confirmé dans le délai prévu. "
        "Consultez le journal du service."
    )


# ============================================================
# 8. ÉTAT DU SERVICE
# ============================================================

def show_status():
    """
    Affiche l'état actuel du service.
    """

    process = get_service_process()

    if process is None:

        print("État : ARRÊTÉ")

        return

    print("État : EN COURS D'EXÉCUTION")
    print(f"PID : {process.pid}")
    print(f"Nom : {process.name()}")
    print(f"Création : {time.ctime(process.create_time())}")

    try:

        config = load_config()

        print("\nConfiguration :")
        print(
            f"- Intervalle : {config.monitoring_interval} seconde(s)"
        )
        print(
            f"- Durée d'inactivité : {config.inactive_threshold} seconde(s)"
        )
        print(
            f"- Seuil CPU : {config.cpu_usage_threshold} %"
        )
        print(
            f"- Seuil mémoire : {config.memory_usage_threshold} Mo"
        )
        print(
            f"- Son : {config.alert_sound}"
        )

    except Exception as error:

        print(f"Impossible de lire la configuration : {error}")


# ============================================================
# 9. INTERFACE EN LIGNE DE COMMANDE
# ============================================================

def create_parser():

    parser = argparse.ArgumentParser(
        prog="ProcessScope",
        description=(
            "Surveillance des processus Windows "
            "depuis la ligne de commande."
        ),
        epilog=(
            "Exemple : python cli.py --start --interval 2 "
            "--duration 15 --cpu 5 --memory 50"
        )
    )

    actions = parser.add_mutually_exclusive_group(required=False)

    actions.add_argument(
        "--start",
        action="store_true",
        help="Démarrer la surveillance en arrière-plan."
    )

    actions.add_argument(
        "--stop",
        action="store_true",
        help="Arrêter la surveillance."
    )

    actions.add_argument(
        "--status",
        action="store_true",
        help="Afficher l'état de la surveillance."
    )

    parser.add_argument(
        "--interval",
        type=int,
        help="Intervalle entre deux vérifications, en secondes."
    )

    parser.add_argument(
        "--duration",
        type=int,
        help="Durée minimale de faible activité, en secondes."
    )

    parser.add_argument(
        "--cpu",
        type=float,
        help="Seuil d'activité CPU, entre 0 et 100."
    )

    parser.add_argument(
        "--memory",
        type=float,
        help="Seuil mémoire en Mo."
    )

    parser.add_argument(
        "--sound",
        choices=["default", "critical", "reminder"],
        help="Son de notification."
    )

    # Argument interne utilisé uniquement par le processus enfant.
    parser.add_argument(
        "--_worker",
        action="store_true",
        help=argparse.SUPPRESS
    )

    return parser


# ============================================================
# 10. POINT D'ENTRÉE
# ============================================================

def main():
    parser = create_parser()
    args = parser.parse_args()

    # Le processus interne de surveillance
    if args._worker:
        run_worker()
        return

    # Une action publique est obligatoire
    if not any((args.start, args.stop, args.status)):
        parser.error("une action --start, --stop ou --status est requise")

    if args.start:
        start_service(args)
    elif args.stop:
        stop_service()
    elif args.status:
        show_status()




if __name__ == "__main__":
    main()
