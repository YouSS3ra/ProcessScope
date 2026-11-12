import tkinter as tk
from tkinter import ttk
from tkinter import PhotoImage 
import customtkinter as ctk
from paths import IMAGES_DIR

def create_command_page(parent):
    """
    Crée une page avec des icônes dessinées directement dans le code.
    """
    # Couleur de fond principale
    background_color = "#282C34"
    frame_background = "#3C4047"
    text_color = "#FFFFFF"
    subtext_color = "#CCCCCC"

    # Titre principal
    title_label = tk.Label(
        parent,
        text="Commandes Personnalisées",
        font=("Helvetica", 24, "bold"),
        bg=background_color,
        fg=text_color
    )
    title_label.pack(pady=20)

    # Conteneur pour les commandes
    container = tk.Frame(parent, bg=background_color)
    container.pack(fill="both", expand=True, padx=20, pady=10)

    # Style des frames
    frame_style = {
        "bg": frame_background,
        "bd": 2,
        "relief": "groove",
        "highlightbackground": "#444",
        "highlightthickness": 1
    }

    # Liste des commandes avec des icônes dessinées
    commandes = [
        {"icone": "start", "commande": "--start", "description": "Démarrer la surveillance."},
        {"icone": "stop", "commande": "--stop", "description": "Arrêter la surveillance."},
        {"icone": "interval", "commande": "--interval <n>", "description": "Changer l'intervalle de surveillance (en secondes)."},
        {"icone": "help", "commande": "--help", "description": "Afficher l'aide pour les commandes disponibles."},
        {"icone": "sound", "commande": "--sound <son>", "description": "Définir un son personnalisé pour les alertes."}
    ]

    # Ajouter des frames pour chaque commande
    for cmd in commandes:
        frame = tk.Frame(container, **frame_style)
        frame.pack(fill="x", pady=10, padx=10)

        # Canvas pour dessiner l'icône
        icon_canvas = tk.Canvas(frame, width=50, height=50, bg=frame_background, highlightthickness=0)
        icon_canvas.pack(side="left", padx=10, pady=10)

        # Dessiner l'icône en fonction du type
        if cmd["icone"] == "start":
            icon_canvas.create_polygon(10, 10, 40, 25, 10, 40, fill="#4CAF50", outline="")
        elif cmd["icone"] == "stop":
            icon_canvas.create_rectangle(10, 10, 40, 40, fill="#F44336", outline="")
        elif cmd["icone"] == "interval":
            icon_canvas.create_line(10, 25, 40, 25, fill="#2196F3", width=3)
            icon_canvas.create_oval(15, 20, 20, 30, fill="#2196F3", outline="")
            icon_canvas.create_oval(30, 20, 35, 30, fill="#2196F3", outline="")
        elif cmd["icone"] == "help":
            icon_canvas.create_oval(10, 10, 40, 40, fill="#FFC107", outline="")
            icon_canvas.create_text(25, 25, text="?", fill="black", font=("Helvetica", 20, "bold"))
        elif cmd["icone"] == "sound":
            icon_canvas.create_rectangle(10, 15, 20, 35, fill="#9C27B0", outline="")
            icon_canvas.create_polygon(20, 15, 40, 25, 20, 35, fill="#9C27B0", outline="")

        # Texte descriptif
        text_frame = tk.Frame(frame, bg=frame_background)
        text_frame.pack(side="left", fill="both", expand=True, padx=10)

        command_label = tk.Label(
            text_frame,
            text=cmd["commande"],
            font=("Helvetica", 14, "bold"),
            bg=frame_background,
            fg=text_color
        )
        command_label.pack(anchor="w")

        description_label = tk.Label(
            text_frame,
            text=cmd["description"],
            font=("Helvetica", 12),
            bg=frame_background,
            fg=subtext_color
        )
        description_label.pack(anchor="w")

    
    
    image_path = IMAGES_DIR / "c5.png"
    try:
        photo = tk.PhotoImage(file=str(image_path))
        image_label = ctk.CTkLabel(container, image=photo, text="")
        image_label.image = photo  # Référence pour éviter le garbage collection
        image_label.pack(pady=(20, 10))  # Ajout d'un padding
    except Exception as e:
        print(f"Erreur lors du chargement de l'image : {e}")
   
# Tester la page
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Icônes Dessinées")
    root.geometry("800x600")
    root.configure(bg="#282C34")
    create_command_page(root)
    root.mainloop()
