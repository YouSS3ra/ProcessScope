
import csv
import os
import subprocess
import sys
import threading
import time
import queue

from datetime import datetime
import tkinter as tk
import customtkinter as ctk
import psutil

from paths import IMAGES_DIR, CSV_PATH


# ============================================================
# 1. COLLECTE DES DONNÉES RÉELLES
# ============================================================

def collect_system_data():
    """
    Collecte les informations réelles du système et des processus.

    Deux mesures CPU espacées d'une seconde permettent d'obtenir
    des valeurs CPU par processus plus pertinentes.
    """

    processes = []

    # Préparer les compteurs CPU des processus.
    for process in psutil.process_iter(["pid", "name"]):
        try:
            process.cpu_percent(interval=None)
            processes.append(process)

        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
            psutil.ZombieProcess
        ):
            continue

    # Initialiser le compteur CPU global.
    psutil.cpu_percent(interval=None)

    # Attendre une seconde pour mesurer l'activité CPU.
    time.sleep(1)

    # Date et heure de la collecte.
    collection_time = datetime.now().astimezone().isoformat(
        timespec="seconds"
    )

    # Informations globales du système.
    system_cpu = psutil.cpu_percent(interval=None)
    system_memory = psutil.virtual_memory()

    process_data = []

    # Deuxième mesure : informations de chaque processus.
    for process in processes:

        try:
            cpu_percent = process.cpu_percent(interval=None)

            memory_info = process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)
            memory_percent = process.memory_percent()

            process_data.append({
                "timestamp": collection_time,
                "pid": process.pid,
                "process_name": process.name(),
                "cpu_percent": round(cpu_percent, 2),
                "memory_mb": round(memory_mb, 2),
                "memory_percent": round(memory_percent, 2),
                "system_cpu_percent": round(system_cpu, 2),
                "system_memory_percent": round(
                    system_memory.percent, 2
                ),
                "system_memory_used_gb": round(
                    system_memory.used / (1024 ** 3), 2
                ),
                "system_memory_total_gb": round(
                    system_memory.total / (1024 ** 3), 2
                )
            })

        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
            psutil.ZombieProcess
        ):
            continue

    # Trier les processus par utilisation CPU décroissante.
    process_data.sort(
        key=lambda item: item["cpu_percent"],
        reverse=True
    )

    return process_data


# ============================================================
# 2. GÉNÉRATION DU FICHIER CSV
# ============================================================

def generate_csv_report():
    """
    Génère un rapport CSV contenant les données collectées
    réellement sur la machine.
    """

    process_data = collect_system_data()

    # Vérifier que le dossier de destination existe.
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "timestamp",
        "pid",
        "process_name",
        "cpu_percent",
        "memory_mb",
        "memory_percent",
        "system_cpu_percent",
        "system_memory_percent",
        "system_memory_used_gb",
        "system_memory_total_gb"
    ]

    # utf-8-sig facilite l'ouverture du CSV avec Excel.
    # Le séparateur ; est adapté aux configurations Excel françaises.
    with open(
        CSV_PATH,
        mode="w",
        newline="",
        encoding="utf-8-sig"
    ) as csv_file:

        writer = csv.DictWriter(
            csv_file,
            fieldnames=fieldnames,
            delimiter=";"
        )

        writer.writeheader()
        writer.writerows(process_data)

    return len(process_data)


# ============================================================
# 3. OUVERTURE DU RAPPORT
# ============================================================

def open_csv_file():
    """
    Ouvre le rapport CSV avec l'application par défaut du système.
    """

    if not CSV_PATH.exists():
        raise FileNotFoundError(
            f"Le fichier {CSV_PATH.name} n'existe pas."
        )

    if os.name == "nt":
        os.startfile(str(CSV_PATH))

    elif sys.platform == "darwin":
        subprocess.run(
            ["open", str(CSV_PATH)],
            check=True
        )

    else:
        subprocess.run(
            ["xdg-open", str(CSV_PATH)],
            check=True
        )


# ============================================================
# 4. INTERFACE GRAPHIQUE
# ============================================================

def create_report_page(parent):

    report_frame = ctk.CTkFrame(
        parent,
        corner_radius=15,
        fg_color="#2E2E2E"
    )

    # File d'attente pour transmettre le résultat du thread
    # de collecte vers le thread principal de Tkinter.
    result_queue = queue.Queue()

    # --------------------------------------------------------
    # En-tête
    # --------------------------------------------------------

    header_frame = ctk.CTkFrame(
        report_frame,
        height=80,
        fg_color="#3C3F41",
        corner_radius=15
    )

    header_frame.pack(
        fill="x",
        padx=20,
        pady=20
    )

    header_label = ctk.CTkLabel(
        header_frame,
        text="Rapport d'Utilisation",
        font=("Forte", 30, "bold"),
        text_color="#FFFFFF"
    )

    header_label.pack(
        pady=10,
        padx=10
    )

    # --------------------------------------------------------
    # Séparateur
    # --------------------------------------------------------

    separator = ctk.CTkFrame(
        report_frame,
        height=2,
        fg_color="#4caf50",
        corner_radius=0
    )

    separator.pack(
        fill="x",
        padx=20
    )

    # --------------------------------------------------------
    # Contenu principal
    # --------------------------------------------------------

    main_content_frame = ctk.CTkFrame(
        report_frame,
        fg_color="#2E2E2E"
    )

    main_content_frame.pack(
        fill="both",
        expand=True,
        padx=20,
        pady=20
    )

    central_frame = ctk.CTkFrame(
        main_content_frame,
        corner_radius=10,
        fg_color="#3C3F41"
    )

    central_frame.pack(expand=True)

    # --------------------------------------------------------
    # Image
    # --------------------------------------------------------

    image_path = IMAGES_DIR / "excel2.png"

    try:
        photo = tk.PhotoImage(file=str(image_path))

        image_label = ctk.CTkLabel(
            central_frame,
            image=photo,
            text=""
        )

        image_label.image = photo

        image_label.pack(
            pady=(20, 10)
        )

    except Exception as e:
        print(f"Erreur lors du chargement de l'image : {e}")

    # --------------------------------------------------------
    # Description
    # --------------------------------------------------------

    description_label = ctk.CTkLabel(
        central_frame,
        text=(
            "Générez un rapport contenant les mesures réelles "
            "des ressources système et des processus."
        ),
        font=("Arial", 13),
        text_color="#D0D0D0",
        wraplength=400,
        justify="center"
    )

    description_label.pack(
        padx=20,
        pady=10
    )

    # --------------------------------------------------------
    # Statut de génération
    # --------------------------------------------------------

    status_label = ctk.CTkLabel(
        central_frame,
        text="Aucun rapport généré.",
        font=("Arial", 12),
        text_color="#A9A9A9"
    )

    status_label.pack(
        padx=15,
        pady=10
    )

    # --------------------------------------------------------
    # Vérification du résultat du thread
    # --------------------------------------------------------

    def check_report_result():

        try:
            result = result_queue.get_nowait()

        except queue.Empty:
            if report_frame.winfo_exists():
                report_frame.after(
                    200,
                    check_report_result
                )
            return

        generate_button.configure(
            state="normal",
            text="Générer le rapport CSV"
        )

        if result["success"]:

            count = result["count"]

            status_label.configure(
                text=(
                    f"Rapport généré avec succès : "
                    f"{count} processus enregistrés."
                ),
                text_color="#4CAF50"
            )

            print(
                f"Rapport CSV généré : {CSV_PATH}"
            )

            try:
                open_csv_file()

            except Exception as e:
                status_label.configure(
                    text="Rapport généré, mais impossible de l'ouvrir.",
                    text_color="#F5B041"
                )

                print(f"Erreur lors de l'ouverture du CSV : {e}")

        else:

            status_label.configure(
                text="Erreur lors de la génération du rapport.",
                text_color="#F44336"
            )

            print(
                f"Erreur de génération CSV : {result['error']}"
            )

    # --------------------------------------------------------
    # Génération dans un thread séparé
    # --------------------------------------------------------

    def start_csv_generation():

        generate_button.configure(
            state="disabled",
            text="Génération en cours..."
        )

        status_label.configure(
            text="Collecte des données réelles en cours...",
            text_color="#F5B041"
        )

        def worker():

            try:
                count = generate_csv_report()

                result_queue.put({
                    "success": True,
                    "count": count
                })

            except Exception as e:

                result_queue.put({
                    "success": False,
                    "error": str(e)
                })

        threading.Thread(
            target=worker,
            daemon=True,
            name="ProcessScope-CSV"
        ).start()

        report_frame.after(
            200,
            check_report_result
        )

    # --------------------------------------------------------
    # Bouton de génération
    # --------------------------------------------------------

    generate_button = ctk.CTkButton(
        central_frame,
        text="Générer le rapport CSV",
        command=start_csv_generation,
        fg_color="#4caf50",
        hover_color="#81c784",
        text_color="#FFFFFF",
        font=("Arial", 14, "bold"),
        corner_radius=10,
        height=50,
        width=230
    )

    generate_button.pack(
        pady=(10, 20)
    )

    # --------------------------------------------------------
    # Pied de page
    # --------------------------------------------------------

    footer_frame = ctk.CTkFrame(
        report_frame,
        height=50,
        fg_color="#3C3F41"
    )

    footer_frame.pack(
        side="bottom",
        fill="x"
    )

    footer_label = ctk.CTkLabel(
        footer_frame,
        text="ProcessScope - Rapport système",
        font=("Arial", 12, "italic"),
        text_color="#A9A9A9"
    )

    footer_label.pack(
        side="right",
        padx=10,
        pady=10
    )

    return report_frame
