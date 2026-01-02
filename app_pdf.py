import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import fitz  # PyMuPDF
import os

# Configuration de l'apparence
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class PdfConverterApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Convertisseur Image vers PDF")
        self.geometry("600x500")
        
        self.image_paths = []
        self.thumbnails = []

        # --- UI ---
        self.label_title = ctk.CTkLabel(self, text="Convertisseur d'Images en PDF", font=("Arial", 20, "bold"))
        self.label_title.pack(pady=15)

        self.btn_select = ctk.CTkButton(self, text="➕ Ajouter des Images", command=self.select_images)
        self.btn_select.pack(pady=10)

        # Zone défilante pour les images
        self.scroll_frame = ctk.CTkScrollableFrame(self, width=550, height=150)
        self.scroll_frame.pack(pady=10, padx=20, fill="both", expand=True)

        self.name_entry = ctk.CTkEntry(self, placeholder_text="Nom du fichier PDF (ex: mon_document)", width=300)
        self.name_entry.pack(pady=15)

        self.btn_convert = ctk.CTkButton(self, text="Générer & Compresser le PDF", 
                                          command=self.process_pdf, 
                                          fg_color="green", hover_color="darkgreen",
                                          state="disabled")
        self.btn_convert.pack(pady=20)

    def select_images(self):
        new_files = filedialog.askopenfilenames(filetypes=[("Images", "*.jpg *.jpeg *.png")])
        if new_files:
            self.image_paths.extend(list(new_files))
            self.refresh_preview()

    def refresh_preview(self):
        # Nettoyer la zone de prévisualisation
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        
        self.thumbnails = [] # Garder les références pour éviter le garbage collection

        for i, path in enumerate(self.image_paths):
            # Créer une ligne pour chaque image
            row = ctk.CTkFrame(self.scroll_frame)
            row.pack(fill="x", pady=5, padx=5)

            # Miniature
            img = Image.open(path)
            img.thumbnail((80, 80))
            photo = ImageTk.PhotoImage(img)
            self.thumbnails.append(photo)

            img_label = ctk.CTkLabel(row, image=photo, text="")
            img_label.pack(side="left", padx=10)

            # Nom du fichier (tronqué si trop long)
            name = os.path.basename(path)
            if len(name) > 20: name = name[:17] + "..."
            name_label = ctk.CTkLabel(row, text=name, width=120)
            name_label.pack(side="left", padx=5)

            # Boutons de contrôle
            btn_up = ctk.CTkButton(row, text="↑", width=30, command=lambda idx=i: self.move_image(idx, -1))
            btn_up.pack(side="left", padx=2)

            btn_down = ctk.CTkButton(row, text="↓", width=30, command=lambda idx=i: self.move_image(idx, 1))
            btn_down.pack(side="left", padx=2)

            btn_del = ctk.CTkButton(row, text="X", width=30, fg_color="red", hover_color="darkred", 
                                    command=lambda idx=i: self.remove_image(idx))
            btn_del.pack(side="right", padx=10)

        # Activer le bouton si on a des images
        if len(self.image_paths) > 0:
            self.btn_convert.configure(state="normal")
        else:
            self.btn_convert.configure(state="disabled")

    def move_image(self, index, direction):
        new_index = index + direction
        if 0 <= new_index < len(self.image_paths):
            self.image_paths[index], self.image_paths[new_index] = \
                self.image_paths[new_index], self.image_paths[index]
            self.refresh_preview()

    def remove_image(self, index):
        self.image_paths.pop(index)
        self.refresh_preview()

    def compress_pdf(self, input_path, output_path, target_size_mb=1.7):
        """ Compresse le PDF pour qu'il soit inférieur à la cible """
        doc = fitz.open(input_path)
        # Compression standard
        doc.save(output_path, garbage=4, deflate=True, clean=True)
        
        # Vérification de la taille
        if os.path.getsize(output_path) > (target_size_mb * 1024 * 1024):
            # Si encore trop lourd, on recompresse avec réduction de qualité image
            doc.save(output_path, garbage=4, deflate=True, image_quality=70, incremental=False)
        
        doc.close()

    def process_pdf(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("Attention", "Donnez un nom à votre fichier PDF.")
            return

        save_path = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile=name)
        
        if save_path:
            try:
                # Création du PDF brut en mémoire tampon
                temp_pdf = "temp_processing.pdf"
                pil_images = []
                for p in self.image_paths:
                    img = Image.open(p).convert("RGB")
                    pil_images.append(img)
                
                if pil_images:
                    pil_images[0].save(temp_pdf, save_all=True, append_images=pil_images[1:])
                    
                    # Compression et sauvegarde finale
                    self.compress_pdf(temp_pdf, save_path)
                    
                    if os.path.exists(temp_pdf):
                        os.remove(temp_pdf)
                    
                    messagebox.showinfo("Succès", f"PDF créé : {os.path.basename(save_path)}")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la création : {e}")

if __name__ == "__main__":
    app = PdfConverterApp()
    app.mainloop()
