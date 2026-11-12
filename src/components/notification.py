
import threading
import tkinter.messagebox as messagebox
from tkinter import PhotoImage

import customtkinter as ctk

from paths import IMAGES_DIR

from monitor_service import (
    MonitoringConfig,
    monitor_processes,
    validate_interval,
    validate_settings,
    resolve_sound
)


# ============================================================
# 1. CONFIGURATION ET ÉTAT DE L'INTERFACE
# ============================================================

# Configuration partagée avec le moteur de surveillance.
config = MonitoringConfig()

# État du thread de surveillance.
is_monitoring = False
monitoring_thread = None

# Événement permettant de demander l'arrêt du moteur.
stop_event = threading.Event()
stop_event.set()

# Correspondance entre les noms affichés dans l'interface
# et les identifiants utilisés par monitor_service.py.
SOUND_OPTIONS = {
    "Par défaut": "default",
    "Critique": "critical",
    "Rappel": "reminder",
}


# ============================================================
# 2. CONFIGURATION DES PARAMÈTRES
# ============================================================

def set_monitoring_interval(interval):
    """
    Met à jour l'intervalle entre deux vérifications.
    """

    try:
        new_interval = validate_interval(interval)

        config.monitoring_interval = new_interval

        print(
            f"Intervalle de surveillance : "
            f"{config.monitoring_interval} seconde(s)."
        )

        return True

    except ValueError as error:

        messagebox.showerror(
            "Paramètre invalide",
            str(error)
        )

        return False


def set_monitoring_settings(
    inactive_duration,
    cpu_threshold,
    memory_threshold
):
    """
    Met à jour les critères utilisés pour détecter
    une faible activité.
    """

    try:

        (
            new_duration,
            new_cpu,
            new_memory
        ) = validate_settings(
            inactive_duration,
            cpu_threshold,
            memory_threshold
        )

        config.inactive_threshold = new_duration
        config.cpu_usage_threshold = new_cpu
        config.memory_usage_threshold = new_memory

        print("Critères de surveillance mis à jour :")
        print(
            f"- Durée : {config.inactive_threshold} seconde(s)"
        )
        print(
            f"- Seuil CPU : {config.cpu_usage_threshold} %"
        )
        print(
            f"- Seuil mémoire : {config.memory_usage_threshold} Mo"
        )

        messagebox.showinfo(
            "Configuration",
            "Les critères de surveillance ont été mis à jour."
        )

        return True

    except ValueError as error:

        messagebox.showerror(
            "Paramètres invalides",
            f"Vérifiez les valeurs saisies.\n\nDétail : {error}"
        )

        return False


def set_alert_sound(sound_choice):
    """
    Sélectionne un son système pris en charge par winotify.
    """

    if sound_choice not in SOUND_OPTIONS:

        messagebox.showerror(
            "Son invalide",
            "Veuillez sélectionner un son proposé dans la liste."
        )

        return False

    selected_sound = SOUND_OPTIONS[sound_choice]

    try:
        # Vérifie que le moteur reconnaît ce son.
        resolve_sound(selected_sound)

        config.alert_sound = selected_sound

        print(
            f"Son de notification sélectionné : {sound_choice}"
        )

        return True

    except ValueError as error:

        messagebox.showerror(
            "Son invalide",
            str(error)
        )

        return False


# ============================================================
# 3. EXÉCUTION DU MOTEUR DANS UN THREAD
# ============================================================

def _monitoring_worker():
    """
    Exécute le moteur de surveillance dans un thread.

    Cette fonction sert d'adaptateur entre l'interface
    graphique et le moteur indépendant.
    """

    global is_monitoring

    try:

        monitor_processes(
            stop_event=stop_event,
            config=config
        )

    except Exception as error:

        print(
            f"Erreur pendant l'exécution de la surveillance : {error}"
        )

    finally:

        is_monitoring = False


# ============================================================
# 4. DÉMARRAGE ET ARRÊT DE LA SURVEILLANCE
# ============================================================

def start_monitoring():
    """
    Démarre le thread de surveillance.
    """

    global is_monitoring
    global monitoring_thread

    if is_monitoring:

        messagebox.showinfo(
            "Surveillance",
            "La surveillance est déjà en cours."
        )

        return

    if (
        monitoring_thread is not None
        and monitoring_thread.is_alive()
    ):

        messagebox.showinfo(
            "Surveillance",
            "L'arrêt précédent est encore en cours. "
            "Réessayez dans un instant."
        )

        return

    stop_event.clear()
    is_monitoring = True

    monitoring_thread = threading.Thread(
        target=_monitoring_worker,
        daemon=True,
        name="ProcessScope-Monitor"
    )

    monitoring_thread.start()

    messagebox.showinfo(
        "Surveillance",
        "La surveillance des processus a démarré."
    )


def stop_monitoring():
    """
    Demande l'arrêt du thread de surveillance.
    """

    if not is_monitoring:

        messagebox.showinfo(
            "Surveillance",
            "La surveillance n'est pas en cours."
        )

        return

    stop_event.set()

    messagebox.showinfo(
        "Surveillance",
        "L'arrêt de la surveillance a été demandé."
    )


# ============================================================
# 5. INTERFACE GRAPHIQUE
# ============================================================

def create_notification_page(parent_frame):

    notification_frame = ctk.CTkFrame(
        parent_frame,
        corner_radius=15,
        fg_color="#1C1C1C",
        width=600,
        height=450
    )

    notification_frame.grid_columnconfigure(0, weight=1)
    notification_frame.grid_columnconfigure(1, weight=1)

    title_label = ctk.CTkLabel(
        notification_frame,
        text="Gestion des Notifications",
        font=("Forte", 36, "bold"),
        text_color="#ECF0F1"
    )

    title_label.grid(
        row=0,
        column=0,
        columnspan=2,
        pady=(20, 10)
    )

    # --------------------------------------------------------
    # Zone de configuration
    # --------------------------------------------------------

    central_frame = ctk.CTkFrame(
        notification_frame,
        fg_color="#2B2B2B"
    )

    central_frame.grid(
        row=1,
        column=0,
        padx=15,
        pady=15,
        sticky="nsew"
    )

    central_frame.grid_columnconfigure(0, weight=1)
    central_frame.grid_columnconfigure(1, weight=1)

    start_button = ctk.CTkButton(
        central_frame,
        text="Démarrer la surveillance",
        command=start_monitoring,
        fg_color="#387F39"
    )

    start_button.grid(
        row=0,
        column=0,
        padx=8,
        pady=10,
        sticky="ew"
    )

    stop_button = ctk.CTkButton(
        central_frame,
        text="Arrêter la surveillance",
        command=stop_monitoring,
        fg_color="#AF1740"
    )

    stop_button.grid(
        row=0,
        column=1,
        padx=8,
        pady=10,
        sticky="ew"
    )

    # --------------------------------------------------------
    # Intervalle de surveillance
    # --------------------------------------------------------

    interval_label = ctk.CTkLabel(
        central_frame,
        text="Intervalle (secondes) :",
        text_color="white"
    )

    interval_label.grid(
        row=1,
        column=0,
        padx=8,
        pady=5,
        sticky="w"
    )

    interval_entry = ctk.CTkEntry(
        central_frame,
        width=130
    )

    interval_entry.insert(
        0,
        str(config.monitoring_interval)
    )

    interval_entry.grid(
        row=1,
        column=1,
        padx=8,
        pady=5
    )

    update_interval_button = ctk.CTkButton(
        central_frame,
        text="Mettre à jour l'intervalle",
        command=lambda: set_monitoring_interval(
            interval_entry.get()
        ),
        fg_color="#2457A6"
    )

    update_interval_button.grid(
        row=2,
        column=0,
        columnspan=2,
        padx=8,
        pady=8,
        sticky="ew"
    )

    # --------------------------------------------------------
    # Son des notifications
    # --------------------------------------------------------

    sound_label = ctk.CTkLabel(
        central_frame,
        text="Son des notifications :",
        text_color="white"
    )

    sound_label.grid(
        row=3,
        column=0,
        padx=8,
        pady=5,
        sticky="w"
    )

    sound_combobox = ctk.CTkComboBox(
        central_frame,
        values=list(SOUND_OPTIONS.keys()),
        state="readonly",
        width=130
    )

    sound_combobox.set("Par défaut")

    sound_combobox.grid(
        row=3,
        column=1,
        padx=8,
        pady=5
    )

    update_sound_button = ctk.CTkButton(
        central_frame,
        text="Mettre à jour le son",
        command=lambda: set_alert_sound(
            sound_combobox.get()
        ),
        fg_color="#2457A6"
    )

    update_sound_button.grid(
        row=4,
        column=0,
        columnspan=2,
        padx=8,
        pady=8,
        sticky="ew"
    )

    # --------------------------------------------------------
    # Critères de détection
    # --------------------------------------------------------

    settings_title = ctk.CTkLabel(
        central_frame,
        text="Critères de détection",
        font=("Arial", 15, "bold"),
        text_color="#F5B041"
    )

    settings_title.grid(
        row=5,
        column=0,
        columnspan=2,
        pady=(12, 5)
    )

    duration_label = ctk.CTkLabel(
        central_frame,
        text="Durée d'inactivité (s) :",
        text_color="white"
    )

    duration_label.grid(
        row=6,
        column=0,
        padx=8,
        pady=4,
        sticky="w"
    )

    duration_entry = ctk.CTkEntry(
        central_frame,
        width=130
    )

    duration_entry.insert(
        0,
        str(config.inactive_threshold)
    )

    duration_entry.grid(
        row=6,
        column=1,
        padx=8,
        pady=4
    )

    cpu_label = ctk.CTkLabel(
        central_frame,
        text="Seuil CPU (%) :",
        text_color="white"
    )

    cpu_label.grid(
        row=7,
        column=0,
        padx=8,
        pady=4,
        sticky="w"
    )

    cpu_entry = ctk.CTkEntry(
        central_frame,
        width=130
    )

    cpu_entry.insert(
        0,
        str(config.cpu_usage_threshold)
    )

    cpu_entry.grid(
        row=7,
        column=1,
        padx=8,
        pady=4
    )

    memory_label = ctk.CTkLabel(
        central_frame,
        text="Seuil mémoire (Mo) :",
        text_color="white"
    )

    memory_label.grid(
        row=8,
        column=0,
        padx=8,
        pady=4,
        sticky="w"
    )

    memory_entry = ctk.CTkEntry(
        central_frame,
        width=130
    )

    memory_entry.insert(
        0,
        str(config.memory_usage_threshold)
    )

    memory_entry.grid(
        row=8,
        column=1,
        padx=8,
        pady=4
    )

    update_settings_button = ctk.CTkButton(
        central_frame,
        text="Mettre à jour les critères",
        command=lambda: set_monitoring_settings(
            duration_entry.get(),
            cpu_entry.get(),
            memory_entry.get()
        ),
        fg_color="#2457A6"
    )

    update_settings_button.grid(
        row=9,
        column=0,
        columnspan=2,
        padx=8,
        pady=10,
        sticky="ew"
    )

    # --------------------------------------------------------
    # Image décorative
    # --------------------------------------------------------

    image_path = IMAGES_DIR / "micro.png"

    try:

        photo = PhotoImage(file=str(image_path))

        image_label = ctk.CTkLabel(
            central_frame,
            image=photo,
            text=""
        )

        image_label.image = photo

        image_label.grid(
            row=10,
            column=0,
            columnspan=2,
            pady=(5, 10)
        )

    except Exception as error:

        print(
            f"Erreur lors du chargement de l'image : {error}"
        )

    # --------------------------------------------------------
    # Zone des remarques
    # --------------------------------------------------------

    right_frame = ctk.CTkFrame(
        notification_frame,
        width=250,
        height=300,
        fg_color="#2B2B2B"
    )

    right_frame.grid(
        row=1,
        column=1,
        padx=15,
        pady=15,
        sticky="nsew"
    )

    remark_title = ctk.CTkLabel(
        right_frame,
        text="Remarques",
        font=("Forte", 30, "bold"),
        text_color="#F5B041"
    )

    remark_title.pack(pady=(10, 5))

    warnings = [
        "Une faible activité CPU ne signifie pas forcément qu'un processus est inutile.",
        "La durée d'inactivité est calculée à partir des observations CPU.",
        "Le seuil mémoire sert à filtrer les processus à surveiller.",
        "Une alerte est envoyée une seule fois par période d'inactivité.",
        "Une activité CPU détectée réinitialise la période d'inactivité.",
        "Les notifications Windows doivent être autorisées dans les paramètres système.",
        "L'arrêt d'un processus n'est pas automatique."
    ]

    for warning in warnings:

        warning_frame = ctk.CTkFrame(
            right_frame,
            fg_color="#1C1C1C",
            corner_radius=10
        )

        warning_frame.pack(
            pady=5,
            padx=10,
            fill="x"
        )

        bullet_label = ctk.CTkLabel(
            warning_frame,
            text="⚠",
            font=("Arial", 16),
            text_color="#F5B041"
        )

        bullet_label.pack(
            side="left",
            padx=5
        )

        warning_label = ctk.CTkLabel(
            warning_frame,
            text=warning,
            font=("Arial", 12),
            text_color="white",
            anchor="w",
            justify="left",
            wraplength=200
        )

        warning_label.pack(
            side="left",
            padx=5,
            pady=5,
            expand=True,
            fill="x"
        )

    return notification_frame
