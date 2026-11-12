
import customtkinter as ctk
from tkinter import ttk
import psutil


def create_real_time_process_display(parent):

    # Conteneur principal
    process_frame = ctk.CTkFrame(
        parent,
        fg_color="#2b2b2b",
        corner_radius=10
    )
    process_frame.pack(
        fill="both",
        expand=True,
        padx=10,
        pady=10
    )

    # Tableau des processus
    columns = ("ID", "Nom", "CPU (%)", "RAM (%)")

    process_table = ttk.Treeview(
        process_frame,
        columns=columns,
        show="headings",
        height=15
    )

    process_table.pack(
        fill="both",
        expand=True,
        padx=10,
        pady=(10, 5)
    )

    # Style du tableau
    style = ttk.Style()
    style.theme_use("clam")

    style.configure(
        "Treeview",
        background="#333333",
        foreground="white",
        fieldbackground="#333333",
        rowheight=25
    )

    style.configure(
        "Treeview.Heading",
        background="#444444",
        foreground="white",
        font=("Arial", 12, "bold")
    )

    for col in columns:
        process_table.heading(col, text=col)
        process_table.column(
            col,
            anchor="center",
            stretch=True
        )

    # Zone des statistiques CPU et RAM
    stats_frame = ctk.CTkFrame(
        process_frame,
        fg_color="#444444",
        corner_radius=10
    )
    stats_frame.pack(fill="x", pady=10)

    # Statistiques CPU
    cpu_frame = ctk.CTkFrame(
        stats_frame,
        width=400,
        height=100,
        fg_color="#222222",
        corner_radius=10
    )
    cpu_frame.pack(side="left", padx=20, pady=10)

    cpu_label = ctk.CTkLabel(
        cpu_frame,
        text="Consommation CPU",
        font=("Arial", 12, "bold")
    )
    cpu_label.pack(side="bottom", pady=5)

    cpu_usage_label = ctk.CTkLabel(
        cpu_frame,
        text="0%",
        font=("Forte", 25, "bold"),
        text_color="#41C8FF"
    )
    cpu_usage_label.pack(expand=True)

    # Statistiques RAM
    ram_frame = ctk.CTkFrame(
        stats_frame,
        width=400,
        height=100,
        fg_color="#222222",
        corner_radius=10
    )
    ram_frame.pack(side="left", padx=20, pady=10)

    ram_label = ctk.CTkLabel(
        ram_frame,
        text="Consommation RAM",
        font=("Arial", 12, "bold")
    )
    ram_label.pack(side="bottom", pady=5)

    ram_usage_label = ctk.CTkLabel(
        ram_frame,
        text="0%",
        font=("Forte", 25, "bold"),
        text_color="#58F0F9"
    )
    ram_usage_label.pack(expand=True)

    # Initialiser les compteurs CPU des processus existants
    for proc in psutil.process_iter():
        try:
            proc.cpu_percent(interval=None)
        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
            psutil.ZombieProcess
        ):
            continue

    # Actualisation du tableau et des statistiques
    def refresh_data():

        try:
            # 1. Récupération des processus
            processes = []

            for proc in psutil.process_iter(["pid", "name"]):
                try:
                    pid = proc.info["pid"]
                    name = proc.info.get("name") or "N/A"

                    with proc.oneshot():
                        cpu = proc.cpu_percent(interval=None)
                        ram = proc.memory_percent()

                    processes.append(
                        (
                            pid,
                            name,
                            f"{cpu:.1f}",
                            f"{ram:.1f}"
                        )
                    )

                except (
                    psutil.NoSuchProcess,
                    psutil.AccessDenied,
                    psutil.ZombieProcess
                ):
                    continue

            # 2. Actualisation du tableau
            process_table.delete(
                *process_table.get_children()
            )

            for process in processes:
                process_table.insert(
                    "",
                    "end",
                    values=process
                )

            # 3. Actualisation des statistiques globales
            cpu_usage = psutil.cpu_percent(interval=None)
            ram_usage = psutil.virtual_memory().percent

            cpu_usage_label.configure(
                text=f"{cpu_usage:.1f}%"
            )

            ram_usage_label.configure(
                text=f"{ram_usage:.1f}%"
            )

        except Exception as e:
            print(f"Erreur de supervision : {e}")

        finally:
            # Programmer la prochaine actualisation
            process_frame.after(1000, refresh_data)

    # Démarrer la supervision
    process_frame.after(1000, refresh_data)

    return process_frame
