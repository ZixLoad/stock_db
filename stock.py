import tkinter as tk
from tkinter import filedialog, messagebox, ttk, scrolledtext
import sqlite3
import os
import io
from PIL import Image, ImageTk
import fitz  


def initialize_db():
    conn = sqlite3.connect("documents.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS documents (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        type TEXT NOT NULL,
                        content BLOB NOT NULL)''')
    conn.commit()
    conn.close()


def insert_file(name, file_type, content):
    try:
        conn = sqlite3.connect("documents.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO documents (name, type, content) VALUES (?, ?, ?)", (name, file_type, content))
        conn.commit()
        conn.close()
        messagebox.showinfo("Succès", f"Fichier '{name}' ajouté à la base de données.")
    except Exception as e:
        messagebox.showerror("Erreur", f"Erreur lors de l'insertion : {e}")


def add_file():
    file_path = filedialog.askopenfilename(title="Choisir un fichier", filetypes=[("Tous les fichiers", "*.*")])
    if not file_path:
        return

    try:
        with open(file_path, "rb") as file:
            file_content = file.read()

        file_name = os.path.basename(file_path)
        file_type = os.path.splitext(file_name)[1][1:]

        insert_file(file_name, file_type, file_content)
        show_files()
    except Exception as e:
        messagebox.showerror("Erreur", f"Une erreur est survenue : {e}")


def fetch_files():
    try:
        conn = sqlite3.connect("documents.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, type, content FROM documents")
        files = cursor.fetchall()
        conn.close()
        return files
    except Exception as e:
        messagebox.showerror("Erreur", f"Erreur lors de la récupération des fichiers : {e}")
        return []


def download_file(file_id, file_name):
    try:
        conn = sqlite3.connect("documents.db")
        cursor = conn.cursor()
        cursor.execute("SELECT content FROM documents WHERE id = ?", (file_id,))
        file_content = cursor.fetchone()[0]
        conn.close()

        save_path = filedialog.asksaveasfilename(initialfile=file_name, title="Enregistrer sous",
                                                 filetypes=[("Tous les fichiers", "*.*")])
        if save_path:
            with open(save_path, "wb") as file:
                file.write(file_content)
            messagebox.showinfo("Succès", f"Fichier '{file_name}' enregistré à '{save_path}'.")
    except Exception as e:
        messagebox.showerror("Erreur", f"Erreur lors du téléchargement : {e}")


def delete_file(file_id):
    try:
        conn = sqlite3.connect("documents.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM documents WHERE id = ?", (file_id,))
        conn.commit()
        conn.close()
        messagebox.showinfo("Succès", "Fichier supprimé de la base de données.")
        show_files()
    except Exception as e:
        messagebox.showerror("Erreur", f"Erreur lors de la suppression : {e}")


def delete_selected_file():
    try:
        selected_item = file_table.selection()[0]
        file_id = file_table.item(selected_item, "values")[0]
        file_name = file_table.item(selected_item, "values")[1]
        if messagebox.askyesno("Confirmation", f"Êtes-vous sûr de vouloir supprimer le fichier '{file_name}' ?"):
            delete_file(file_id)
    except IndexError:
        messagebox.showwarning("Avertissement", "Veuillez sélectionner un fichier à supprimer.")


def display_file(file_id, file_type):
    try:
        conn = sqlite3.connect("documents.db")
        cursor = conn.cursor()
        cursor.execute("SELECT content FROM documents WHERE id = ?", (file_id,))
        file_content = cursor.fetchone()[0]
        conn.close()

        display_area.config(state=tk.NORMAL)
        display_area.delete(1.0, tk.END)

        if file_type.lower() in ("png", "jpg", "jpeg", "gif"):
            image = Image.open(io.BytesIO(file_content))
            image.thumbnail((400, 400))
            photo = ImageTk.PhotoImage(image)
            display_area.image_create(tk.END, image=photo)
            display_area.image = photo

        elif file_type.lower() == "pdf":
            try:
                doc = fitz.open(stream=file_content, filetype="pdf")
                page = doc[0]
                pix = page.get_pixmap(matrix=fitz.Matrix(0.5, 0.5))
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                photo = ImageTk.PhotoImage(img)
                display_area.image_create(tk.END, image=photo)
                display_area.image = photo
            except Exception as pdf_e:
                display_area.insert(tk.END, f"Erreur d'affichage PDF : {pdf_e}")
        else:
            display_area.insert(tk.END, "Type de fichier non visualisable.")
        display_area.config(state=tk.DISABLED)

    except Exception as e:
        messagebox.showerror("Erreur", f"Erreur lors de l'affichage du fichier : {e}")


def get_db_size():
    try:
        size = os.path.getsize("documents.db")
        return size
    except FileNotFoundError:
        return 0


def show_files():
    for row in file_table.get_children():
        file_table.delete(row)

    files = fetch_files()
    for file in files:
        file_size = len(file[3]) if file and len(file) >= 4 and file[3] else 0
        file_table.insert("", "end", values=(file[0], file[1], file[2], file_size))

    db_size = get_db_size()
    db_size_mb = db_size / (1024 * 1024)
    db_size_label.config(text=f"Taille de la base de données : {db_size_mb:.2f} Mo")


def file_selected(event):
    try:
        selected_item = file_table.selection()[0]
        file_id = file_table.item(selected_item, "values")[0]
        file_type = file_table.item(selected_item, "values")[2]
        display_file(file_id, file_type)
    except IndexError:
        pass


def download_selected_file():
    try:
        selected_item = file_table.selection()[0]
        file_id = file_table.item(selected_item, "values")[0]
        file_name = file_table.item(selected_item, "values")[1]
        download_file(file_id, file_name)
    except IndexError:
        messagebox.showwarning("Avertissement", "Veuillez sélectionner un fichier à télécharger.")
def import_database():
    
    file_path = filedialog.askopenfilename(title="Choisir une base de données", filetypes=[("Base de données SQLite", "*.db")])
    if not file_path:
        return 

    try:
        # Connexion à la base de données existante
        conn_current = sqlite3.connect("documents.db")
        cursor_current = conn_current.cursor()

        # Connexion à la nouvelle base de données
        conn_new = sqlite3.connect(file_path)
        cursor_new = conn_new.cursor()

       
        cursor_new.execute("PRAGMA table_info(documents)")
        columns_new = [col[1] for col in cursor_new.fetchall()]

        cursor_current.execute("PRAGMA table_info(documents)")
        columns_current = [col[1] for col in cursor_current.fetchall()]

        if columns_new != columns_current:
            messagebox.showerror("Erreur", "Les bases de données ne sont pas compatibles.")
            conn_new.close()
            conn_current.close()
            return

       
        cursor_new.execute("SELECT * FROM documents")
        rows = cursor_new.fetchall()

        for row in rows:
            try:
                cursor_current.execute(
                    "INSERT INTO documents (name, type, content) VALUES (?, ?, ?)",
                    (row[1], row[2], row[3])
                )
            except sqlite3.IntegrityError as e:
                
                print(f"Erreur lors de l'insertion : {e}")

        conn_current.commit()

        messagebox.showinfo("Succès", f"Données importées depuis {file_path}.")
        conn_new.close()
        conn_current.close()

        
        show_files()

    except Exception as e:
        messagebox.showerror("Erreur", f"Erreur lors de l'importation de la base de données : {e}")


window = tk.Tk()
window.title("Gestionnaire de fichiers")
window.geometry("800x600")

file_table = ttk.Treeview(window, columns=("ID", "Nom", "Type", "Taille"), show="headings")
file_table.heading("ID", text="ID")
file_table.heading("Nom", text="Nom")
file_table.heading("Type", text="Type")
file_table.heading("Taille", text="Taille (octets)")
file_table.pack(fill=tk.BOTH, expand=True)
file_table.bind("<<TreeviewSelect>>", file_selected)

display_frame = tk.Frame(window)
display_frame.pack(fill=tk.BOTH, expand=True, pady=10)  

display_area = scrolledtext.ScrolledText(display_frame, wrap=tk.WORD, height=10)
display_area.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)  # Espacement autour de la zone

db_size_label = tk.Label(window, text="Taille de la base de données : 0.00 Mo")
db_size_label.pack()

button_frame = tk.Frame(window)
button_frame.pack(side=tk.TOP, pady=10)  

btn_add = tk.Button(button_frame, text="Ajouter un fichier", command=add_file)
btn_add.pack(side=tk.LEFT, padx=5)  

btn_delete = tk.Button(button_frame, text="Supprimer le fichier", command=delete_selected_file)
btn_delete.pack(side=tk.LEFT, padx=5)

btn_download = tk.Button(button_frame, text="Télécharger le fichier", command=download_selected_file)
btn_download.pack(side=tk.LEFT, padx=5)

btn_import = tk.Button(button_frame, text="Importer une base de données", command=import_database)
btn_import.pack(side=tk.LEFT, padx=5) 


initialize_db()
show_files()
window.mainloop()
