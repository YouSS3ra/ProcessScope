
import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import psutil
import time
import csv

from paths import ICONS_DIR
from tkinter import PhotoImage


def create_visualisation_page(parent):
    """
    Crée une page de visualisation avec :
    - Un chronomètre de fonctionnement
    - Des indicateurs CPU et RAM
    - Les consommations maximales
    - Le nombre de processus actifs
    - Des graphiques CPU et RAM en temps réel
    """

    visualisation_frame = ctk.CTkFrame(
        parent,
        corner_radius=15
    )

    # =====================================================
    # 1. TITRE DE LA PAGE
    # =====================================================

    header_frame = ctk.CTkFrame(
        visualisation_frame,
        height=80,
        fg_color="#444444"
    )
    header_frame.pack(
        fill="x",
        padx=10,
        pady=10
    )

    header_label = ctk.CTkLabel(
        header_frame,
        text="Visualisation Avancée",
        font=("Forte", 35, "bold"),
        text_color="white"
    )
    header_label.pack(
        pady=10,
        padx=10
    )

    # =====================================================
    # 2. SECTION PRINCIPALE
    # =====================================================

    main_frame = ctk.CTkFrame(
        visualisation_frame,
        fg_color="#333333",
        corner_radius=15
    )
    main_frame.pack(
        fill="both",
        expand=True,
        padx=20,
        pady=20
    )

    # =====================================================
    # 3. INDICATEURS CPU ET RAM
    # =====================================================

    progress_frame = ctk.CTkFrame(
        main_frame,
        fg_color="#2b2b2b",
        corner_radius=15
    )
    progress_frame.pack(
        fill="x",
        pady=10
    )

    # Barre CPU
    cpu_progress = ctk.CTkProgressBar(
        progress_frame,
        orientation="vertical",
        width=20,
        height=150
    )
    cpu_progress.set(0)
    cpu_progress.pack(
        side="left",
        padx=20,
        pady=10
    )

    # Barre RAM
    ram_progress = ctk.CTkProgressBar(
        progress_frame,
        orientation="vertical",
        width=20,
        height=150,
        progress_color="green"
    )
    ram_progress.set(0)
    ram_progress.pack(
        side="left",
        padx=20,
        pady=10
    )

    # Labels CPU et RAM
    cpu_label = ctk.CTkLabel(
        progress_frame,
        text="CPU Usage",
        font=("Arial", 14)
    )
    cpu_label.pack(
        side="left",
        padx=10
    )

    ram_label = ctk.CTkLabel(
        progress_frame,
        text="RAM Usage",
        font=("Arial", 14)
    )
    ram_label.pack(
        side="left",
        padx=10
    )

    # =====================================================
    # 4. CHRONOMETRE
    # =====================================================

    clock_icon = PhotoImage(
        file=str(ICONS_DIR / "clock.png")
    )

    clock_label = ctk.CTkLabel(
        progress_frame,
        text="00:00:00",
        font=("Arial", 14),
        image=clock_icon,
        compound="left",
        text_color="white"
    )

    # Conserver une référence à l'image
    clock_label.image = clock_icon

    clock_label.pack(
        side="left",
        padx=20
    )

    # =====================================================
    # 5. STATISTIQUES RAPIDES
    # =====================================================

    stats_frame = ctk.CTkFrame(
        main_frame,
        fg_color="#2b2b2b",
        corner_radius=15
    )
    stats_frame.pack(
        fill="x",
        pady=10
    )

    cpu_max_label = ctk.CTkLabel(
        stats_frame,
        text="Max CPU: 0%",
        font=("Arial", 14, "bold")
    )
    cpu_max_label.pack(
        side="left",
        padx=20,
        pady=10
    )

    ram_max_label = ctk.CTkLabel(
        stats_frame,
        text="Max RAM: 0%",
        font=("Arial", 14, "bold")
    )
    ram_max_label.pack(
        side="left",
        padx=20,
        pady=10
    )

    process_count_label = ctk.CTkLabel(
        stats_frame,
        text="Active Processes: 0",
        font=("Arial", 14, "bold")
    )
    process_count_label.pack(
        side="left",
        padx=20,
        pady=10
    )

    # =====================================================
    # 6. ZONE DES GRAPHIQUES
    # =====================================================

    graph_frame = ctk.CTkFrame(
        main_frame,
        fg_color="#333333"
    )
    graph_frame.pack(
        fill="both",
        expand=True,
        padx=20,
        pady=20
    )

    # Création des deux graphiques
    fig, (cpu_ax, ram_ax) = plt.subplots(
        2,
        1,
        figsize=(8, 6)
    )

    fig.tight_layout(pad=3)

    # Couleurs de fond
    fig.patch.set_facecolor("#2b2b2b")
    cpu_ax.set_facecolor("#2b2b2b")
    ram_ax.set_facecolor("#2b2b2b")

    # Graphique CPU
    cpu_ax.set_title(
        "Utilisation de la CPU (%)",
        fontsize=12,
        color="white"
    )

    cpu_ax.set_xlim(0, 50)
    cpu_ax.set_ylim(0, 100)

    cpu_line, = cpu_ax.plot(
        [],
        [],
        label="CPU",
        color="#ff6347"
    )

    cpu_ax.legend(
        loc="upper left",
        fontsize=10,
        facecolor="white"
    )

    # Graphique RAM
    ram_ax.set_title(
        "Utilisation de la RAM (%)",
        fontsize=12,
        color="white"
    )

    ram_ax.set_xlim(0, 50)
    ram_ax.set_ylim(0, 100)

    ram_line, = ram_ax.plot(
        [],
        [],
        label="RAM",
        color="#1e90ff"
    )

    ram_ax.legend(
        loc="upper left",
        fontsize=10,
        facecolor="white"
    )

    # Couleur des axes et des graduations
    for ax in (cpu_ax, ram_ax):
        ax.tick_params(
            axis="both",
            colors="white"
        )

        for spine in ax.spines.values():
            spine.set_color("white")

    # Intégration dans CustomTkinter
    canvas = FigureCanvasTkAgg(
        fig,
        master=graph_frame
    )

    canvas.get_tk_widget().pack(
        fill="both",
        expand=True
    )

    # =====================================================
    # 7. VARIABLES DE SUPERVISION
    # =====================================================

    cpu_data = []
    ram_data = []
    time_data = []

    max_cpu = 0
    max_ram = 0

    # Début de la session de supervision
    start_time = time.time()

    # Compteur des points du graphique
    x = 0

    # Initialiser la mesure CPU globale
    # pour disposer d'une première mesure exploitable
    psutil.cpu_percent(interval=None)

    # =====================================================
    # 8. ACTUALISATION DU CHRONOMETRE
    # =====================================================

    def update_time():
        """
        Calcule le temps écoulé depuis
        le début de la supervision.
        """

        elapsed_time = int(
            time.time() - start_time
        )

        hours, remainder = divmod(
            elapsed_time,
            3600
        )

        minutes, seconds = divmod(
            remainder,
            60
        )

        formatted_time = (
            f"{hours:02}:{minutes:02}:{seconds:02}"
        )

        clock_label.configure(
            text=formatted_time
        )

        # Programmer la prochaine actualisation
        visualisation_frame.after(
            1000,
            update_time
        )

    # =====================================================
    # 9. ACTUALISATION DES GRAPHIQUES ET STATISTIQUES
    # =====================================================

    def update_graph():
        nonlocal max_cpu, max_ram, x

        try:
            # ---------------------------------------------
            # Récupération des données système
            # ---------------------------------------------

            cpu_usage = psutil.cpu_percent(
                interval=None
            )

            ram_usage = psutil.virtual_memory().percent

            active_processes = len(psutil.pids())

            # ---------------------------------------------
            # Enregistrement des données
            # ---------------------------------------------

            cpu_data.append(cpu_usage)
            ram_data.append(ram_usage)
            time_data.append(x)

            # ---------------------------------------------
            # Calcul des valeurs maximales
            # ---------------------------------------------

            max_cpu = max(
                max_cpu,
                cpu_usage
            )

            max_ram = max(
                max_ram,
                ram_usage
            )

            # ---------------------------------------------
            # Mise à jour des indicateurs
            # ---------------------------------------------

            cpu_progress.set(
                cpu_usage / 100
            )

            ram_progress.set(
                ram_usage / 100
            )

            cpu_max_label.configure(
                text=f"Max CPU: {max_cpu:.1f}%"
            )

            ram_max_label.configure(
                text=f"Max RAM: {max_ram:.1f}%"
            )

            process_count_label.configure(
                text=f"Active Processes: {active_processes}"
            )

            # ---------------------------------------------
            # Limiter l'historique à 50 points
            # ---------------------------------------------

            if len(time_data) > 50:
                time_data.pop(0)
                cpu_data.pop(0)
                ram_data.pop(0)

            # ---------------------------------------------
            # Actualisation des courbes
            # ---------------------------------------------

            cpu_line.set_data(
                time_data,
                cpu_data
            )

            ram_line.set_data(
                time_data,
                ram_data
            )

            # Déplacement de la fenêtre temporelle
            cpu_ax.set_xlim(
                max(0, x - 49),
                max(50, x)
            )

            ram_ax.set_xlim(
                max(0, x - 49),
                max(50, x)
            )

            # Redessiner le graphique
            canvas.draw_idle()

            # Incrémenter le compteur
            x += 1

        except Exception as e:
            print(
                f"Erreur de visualisation : {e}"
            )

        finally:
            # Programmer la prochaine actualisation
            visualisation_frame.after(
                1000,
                update_graph
            )

    # =====================================================
    # 10. DEMARRAGE DE LA SUPERVISION
    # =====================================================

    # Démarrage du chronomètre
    visualisation_frame.after(
        0,
        update_time
    )

    # Démarrage des graphiques
    visualisation_frame.after(
        1000,
        update_graph
    )

    return visualisation_frame


# =========================================================
# 11. EXPORTATION DES DONNEES CSV
# =========================================================

def export_to_csv(cpu_data, ram_data, time_data):
    """
    Exporte les données CPU et RAM vers un fichier CSV.
    """

    filename = "data_export.csv"

    if cpu_data and ram_data and time_data:

        with open(
            filename,
            mode="w",
            newline=""
        ) as file:

            writer = csv.writer(file)

            # En-têtes des colonnes
            writer.writerow([
                "CPU Usage (%)",
                "RAM Usage (%)",
                "Time"
            ])

            for cpu, ram, t in zip(
                cpu_data,
                ram_data,
                time_data
            ):
                writer.writerow([
                    cpu,
                    ram,
                    t
                ])

        print(
            "Exportation Réussie",
            f"Données exportées vers {filename}."
        )

    else:
        print(
            "Exportation Échouée",
            "Aucune donnée à exporter."
        )
