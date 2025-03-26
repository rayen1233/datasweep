import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import os
import shutil
import datetime
import hashlib
import threading
import asyncio
import concurrent.futures
import logging
from ttkthemes import ThemedTk
import time
import schedule
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
from file_scanner import FileScanner
from disk_monitor import DiskMonitor
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ModernFileManager:
    def __init__(self):
        self.r = ThemedTk(theme="arc")
        self.r.title("DataSweep")
        self.r.geometry("800x600")
        self.fs = FileScanner()
        self.dm = DiskMonitor()
        self.tasks = []
        self.load_tasks()
        self.setup_ui()
        self.setup_keyboard_shortcuts()

    def setup_ui(self):
        self.s = ttk.Style()
        self.s.configure("Modern.TButton", padding=10, font=('Helvetica', 10))
        self.s.configure("Title.TLabel", font=('Helvetica', 16, 'bold'))
        self.s.configure("Subtitle.TLabel", font=('Helvetica', 12))
        self.m = tk.BooleanVar(value=False)
        self.p = tk.DoubleVar()
        self.st = tk.StringVar(value="Prêt")
        self.c = ttk.Frame(self.r)
        self.c.pack(fill="both", expand=True, padx=20, pady=20)
        self.create_frames()
        self.create_menu()
        self.create_status_bar()
        self.t = concurrent.futures.ThreadPoolExecutor(max_workers=4)
        self.l = asyncio.new_event_loop()
        asyncio.set_event_loop(self.l)

    def setup_keyboard_shortcuts(self):
        self.r.bind('<Control-q>', lambda e: self.r.quit())
        self.r.bind('<Control-n>', lambda e: self.show_crit_frame())
        self.r.bind('<Control-d>', lambda e: self.show_doublons_frame())
        self.r.bind('<Control-a>', lambda e: self.show_analyse_frame())
        self.r.bind('<Control-p>', lambda e: self.show_planif_frame())
        self.r.bind('<Control-m>', lambda e: self.show_menu_frame())
        self.r.bind('<F5>', lambda e: self.refresh_dashboard())
        self.r.bind('<F1>', lambda e: self.show_manual())

    def refresh_dashboard(self, health_data=None):
        try:
            if hasattr(self, 'loading_label'):
                self.loading_label.pack_forget()

            if not health_data:
                health_data = self.dm.get_disk_health(os.getcwd())
            
            if not health_data:
                return
                
            self.update_stats_box("disk_usage", f"{health_data['percent']}%")
            self.update_stats_box("free_space", f"{health_data['free']/1024/1024/1024:.1f} GB")
            
            health_status = "Bon"
            if health_data['percent'] > 90:
                health_status = "Critique"
            elif health_data['percent'] > 80:
                health_status = "Attention"
            self.update_stats_box("health", health_status)
            
            io_rate = (health_data['read_bytes'] + health_data['write_bytes']) / 1024 / 1024
            self.update_stats_box("io", f"{io_rate:.1f} MB/s")
            
            self.p.set(health_data['percent'])
            self.st.set(f"Espace disque utilisé: {health_data['percent']}%")
            
            if hasattr(self, 'anal_fig') and self.fa.winfo_ismapped():
                if hasattr(self, 'loading_label'):
                    self.loading_label.pack()
                
                self.dm.plot_usage_history(self.anal_fig)
                self.anal_canvas.draw()
                
                path = self.ar.get() if self.ar.get() else os.getcwd()
                files, total_size = self.fs.parallel_scan(path)
                file_stats = self.fs.get_file_stats(files)
                
                for item in self.files_tree.get_children():
                    self.files_tree.delete(item)
                
                for stat in file_stats:
                    size_mb = stat['size'] / 1024 / 1024
                    percent = (stat['size'] / total_size) * 100 if total_size > 0 else 0
                    self.files_tree.insert("", "end", values=(
                        stat['type'],
                        stat['count'],
                        f"{size_mb:.1f} MB",
                        f"{percent:.1f}%"
                    ))
                
                if hasattr(self, 'loading_label'):
                    self.loading_label.pack_forget()
        except Exception as e:
            logging.error(f"Erreur lors de la mise à jour du tableau de bord: {e}")
            if hasattr(self, 'loading_label'):
                self.loading_label.pack_forget()

    def export_report(self, format='pdf'):
        try:
            path = os.getcwd()
            health_report = self.dm.generate_health_report(path)
            
            files, total_size = self.fs.parallel_scan(path)
            file_stats = self.fs.get_file_stats(files)
            
            report_data = {
                'Métrique': [
                    'État de santé',
                    'Espace utilisé',
                    'Espace libre',
                    'Tendance utilisation',
                    'Activité E/S',
                    'Température',
                    'Dernière mise à jour'
                ],
                'Valeur': [
                    health_report['status'],
                    f"{health_report['usage_percent']:.1f}%",
                    f"{health_report['free_space']/1024/1024/1024:.1f} GB",
                    f"{health_report['usage_trend']:.2f}%/heure",
                    f"{health_report['io_activity']/1024/1024:.1f} MB/s",
                    f"{health_report['temperature']}°C" if health_report['temperature'] else "N/A",
                    health_report['last_update']
                ]
            }
            
            df = pd.DataFrame(report_data)
            
            stats_data = {
                'Type': [stat['type'] for stat in file_stats],
                'Nombre': [stat['count'] for stat in file_stats],
                'Taille (MB)': [stat['size']/1024/1024 for stat in file_stats]
            }
            
            stats_df = pd.DataFrame(stats_data)
            
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            if format == 'pdf':
                from reportlab.lib import colors
                from reportlab.lib.pagesizes import letter
                from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
                from reportlab.lib.styles import getSampleStyleSheet
                
                filename = f"rapport_disque_{timestamp}.pdf"
                doc = SimpleDocTemplate(filename, pagesize=letter)
                elements = []
                
                styles = getSampleStyleSheet()
                elements.append(Paragraph("Rapport d'analyse du disque", styles['Title']))
                
                health_table = Table([df.columns.values.tolist()] + df.values.tolist())
                health_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 14),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(health_table)
                
                elements.append(Paragraph("Statistiques par type de fichier", styles['Heading1']))
                stats_table = Table([stats_df.columns.values.tolist()] + stats_df.values.tolist())
                stats_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 14),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(stats_table)
                
                doc.build(elements)
                
            elif format == 'csv':
                df.to_csv(f'rapport_sante_{timestamp}.csv', index=False)
                stats_df.to_csv(f'statistiques_fichiers_{timestamp}.csv', index=False)
                
            elif format == 'excel':
                try:
                    import openpyxl
                except ImportError:
                    messagebox.showerror("Erreur", "Le module openpyxl n'est pas installé. Veuillez l'installer avec la commande : pip install openpyxl")
                    return
                    
                with pd.ExcelWriter(f'rapport_complet_{timestamp}.xlsx') as writer:
                    df.to_excel(writer, sheet_name='Santé Disque', index=False)
                    stats_df.to_excel(writer, sheet_name='Statistiques Fichiers', index=False)
            
            messagebox.showinfo("Succès", f"Rapport exporté avec succès au format {format}")
            
        except Exception as e:
            logging.error(f"Erreur lors de l'export du rapport: {e}")
            messagebox.showerror("Erreur", f"Erreur lors de l'export: {str(e)}")

    def create_frames(self):
        self.fm = ttk.Frame(self.c)
        self.fm.pack(fill="both", expand=True)
        self.fc = ttk.Frame(self.c)
        self.fd = ttk.Frame(self.c)
        self.fa = ttk.Frame(self.c)
        self.fp = ttk.Frame(self.c)
        self.initialize_menu_frame()
        self.initialize_crit_frame()
        self.initialize_doublons_frame()
        self.initialize_analyse_frame()
        self.initialize_planif_frame()
        self.fc.pack_forget()
        self.fd.pack_forget()
        self.fa.pack_forget()
        self.fp.pack_forget()

    def create_menu(self):
        m = tk.Menu(self.r)
        self.r.config(menu=m)
        fm = tk.Menu(m, tearoff=0)
        m.add_cascade(label="Fichier", menu=fm)
        fm.add_command(label="Quitter", command=self.r.quit)
        vm = tk.Menu(m, tearoff=0)
        m.add_cascade(label="Affichage", menu=vm)
        vm.add_checkbutton(label="Mode Sombre", variable=self.m, command=self.toggle_mode_sombre)
        hm = tk.Menu(m, tearoff=0)
        m.add_cascade(label="Aide", menu=hm)
        hm.add_command(label="Manuel", command=self.show_manual)
        hm.add_command(label="À propos", command=self.show_about)

    def create_status_bar(self):
        self.sb = ttk.Frame(self.r)
        self.sb.pack(side="bottom", fill="x")
        self.sl = ttk.Label(self.sb, textvariable=self.st)
        self.sl.pack(side="left", padx=5, pady=2)
        self.pb = ttk.Progressbar(self.sb, variable=self.p, maximum=100)
        self.pb.pack(side="right", fill="x", padx=5, pady=2)

    def initialize_menu_frame(self):
        lf = ttk.Frame(self.fm)
        lf.pack(pady=10)
        
        try:
            i = Image.open("./source/logo.png")
            i = i.resize((500, 100), Image.Resampling.LANCZOS)
            p = ImageTk.PhotoImage(i)
            ll = ttk.Label(lf, image=p)
            ll.image = p
            ll.pack()
        except Exception as e:
            logger.error(f"Erreur lors du chargement du logo: {e}")
        
        b = [
            ("Effacer avec des critères", self.show_crit_frame),
            ("Supprimer les doublons", self.show_doublons_frame),
            ("Analyser l'espace disque", self.show_analyse_frame),
            ("Planifier une tâche", self.show_planif_frame)
        ]
        for t, c in b:
            btn = ttk.Button(self.fm, text=t, command=c, style="Modern.TButton")
            btn.pack(pady=5, padx=20, fill="x")

    def toggle_mode_sombre(self):
        if self.m.get():
            dark_bg = "#1e1e1e"
            dark_fg = "#ffffff"
            dark_button_bg = "#666666"
            dark_button_fg = "#ffffff"
            dark_entry_bg = "#404040"
            dark_entry_fg = "#ffffff"
            dark_tree_bg = "#404040"
            dark_tree_fg = "#ffffff"
            dark_accent = "#6200EE"
            
            self.s.configure(".", background=dark_bg, foreground=dark_fg)
            self.r.configure(bg=dark_bg)
            self.s.configure("TFrame", background=dark_bg)
            self.s.configure("TLabel", background=dark_bg, foreground=dark_fg)
            self.s.configure("TButton", background=dark_button_bg, foreground=dark_button_fg)
            self.s.configure("Modern.TButton", background=dark_button_bg, foreground=dark_button_fg)
            self.s.configure("TEntry", fieldbackground=dark_entry_bg, foreground=dark_entry_fg)
            self.s.configure("Treeview", background=dark_tree_bg, fieldbackground=dark_tree_bg, foreground=dark_tree_fg)
            self.s.configure("Treeview.Heading", background=dark_button_bg, foreground=dark_button_fg)
            self.s.configure("TProgressbar", background=dark_accent)
            self.s.configure("Title.TLabel", background=dark_bg, foreground=dark_fg)
            self.s.configure("Subtitle.TLabel", background=dark_bg, foreground=dark_fg)
            self.s.configure("Stats.TLabel", background=dark_bg, foreground=dark_accent)
            self.s.configure("TNotebook", background=dark_bg)
            self.s.configure("TNotebook.Tab", background=dark_button_bg, foreground=dark_button_fg)
            self.s.configure("TLabelframe", background=dark_bg)
            self.s.configure("TLabelframe.Label", background=dark_bg, foreground=dark_fg)
            
            self.r.option_add("*Menu.Background", dark_bg)
            self.r.option_add("*Menu.Foreground", dark_fg)
            
            for widget in self.r.winfo_children():
                self._update_widget_colors(widget, dark_bg, dark_fg)
            
        else:
            light_bg = "#ffffff"
            light_fg = "#000000"
            light_button_bg = "#f0f0f0"
            light_button_fg = "#000000"
            light_accent = "#6200EE"
            
            self.s.configure(".", background=light_bg, foreground=light_fg)
            self.r.configure(bg=light_bg)
            self.s.configure("TFrame", background=light_bg)
            self.s.configure("TLabel", background=light_bg, foreground=light_fg)
            self.s.configure("TButton", background=light_button_bg, foreground=light_button_fg)
            self.s.configure("Modern.TButton", background=light_button_bg, foreground=light_button_fg)
            self.s.configure("TEntry", fieldbackground=light_bg, foreground=light_fg)
            self.s.configure("Treeview", background=light_bg, fieldbackground=light_bg, foreground=light_fg)
            self.s.configure("Treeview.Heading", background=light_button_bg, foreground=light_fg)
            self.s.configure("TProgressbar", background=light_accent)
            self.s.configure("Title.TLabel", background=light_bg, foreground=light_fg)
            self.s.configure("Subtitle.TLabel", background=light_bg, foreground=light_fg)
            self.s.configure("Stats.TLabel", background=light_bg, foreground=light_accent)
            self.s.configure("TNotebook", background=light_bg)
            self.s.configure("TNotebook.Tab", background=light_button_bg, foreground=light_button_fg)
            self.s.configure("TLabelframe", background=light_bg)
            self.s.configure("TLabelframe.Label", background=light_bg, foreground=light_fg)
            
            self.r.option_add("*Menu.Background", light_bg)
            self.r.option_add("*Menu.Foreground", light_fg)
            
            for widget in self.r.winfo_children():
                self._update_widget_colors(widget, light_bg, light_fg)

    def _update_widget_colors(self, widget, bg, fg):
        try:
            if isinstance(widget, (ttk.Frame, ttk.LabelFrame)):
                widget.configure(style="TFrame")
            elif isinstance(widget, ttk.Label):
                if "Stats.TLabel" in str(widget.cget("style")):
                    widget.configure(style="Stats.TLabel")
                elif "Title.TLabel" in str(widget.cget("style")):
                    widget.configure(style="Title.TLabel")
                elif "Subtitle.TLabel" in str(widget.cget("style")):
                    widget.configure(style="Subtitle.TLabel")
                else:
                    widget.configure(style="TLabel")
            elif isinstance(widget, ttk.Button):
                widget.configure(style="TButton")
            elif isinstance(widget, ttk.Entry):
                widget.configure(style="TEntry")
            elif isinstance(widget, ttk.Treeview):
                widget.configure(style="Treeview")
                
            for child in widget.winfo_children():
                self._update_widget_colors(child, bg, fg)
        except:
            pass

    def show_frame(self, f):
        for frame in [self.fm, self.fc, self.fd, self.fa, self.fp]:
            frame.pack_forget()
        f.pack(fill="both", expand=True)

    def show_crit_frame(self):
        self.show_frame(self.fc)

    def show_doublons_frame(self):
        self.show_frame(self.fd)

    def show_analyse_frame(self):
        self.show_frame(self.fa)

    def show_planif_frame(self):
        self.show_frame(self.fp)

    def run(self):
        def run_scheduler():
            while True:
                schedule.run_pending()
                time.sleep(1)
        
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        
        self.r.mainloop()
        self.l.close()

    def initialize_crit_frame(self):
        t = ttk.Label(self.fc, text="Effacer avec des critères", style="Title.TLabel")
        t.pack(pady=10)
        ff = ttk.Frame(self.fc)
        ff.pack(fill="both", expand=True, padx=20, pady=10)
        df = ttk.LabelFrame(ff, text="Dossier cible", padding=10)
        df.pack(fill="x", pady=5)
        self.cr = ttk.Entry(df)
        self.cr.pack(side="left", fill="x", expand=True, padx=5)
        ttk.Button(df, text="Parcourir", command=lambda: self.choisir_rep(self.cr)).pack(side="right", padx=5)
        daf = ttk.LabelFrame(ff, text="Date", padding=10)
        daf.pack(fill="x", pady=5)
        self.cd = ttk.Entry(daf)
        self.cd.pack(side="left", fill="x", expand=True, padx=5)
        ttk.Label(daf, text="Format: AAAA-MM-JJ").pack(side="right", padx=5)
        of = ttk.LabelFrame(ff, text="Options", padding=10)
        of.pack(fill="x", pady=5)
        self.vo = tk.StringVar(value="avant")
        ttk.Radiobutton(of, text="Avant la date", variable=self.vo, value="avant").pack(anchor="w")
        ttk.Radiobutton(of, text="Après la date", variable=self.vo, value="apres").pack(anchor="w")
        ttk.Label(of, text="Extensions (ex: .pdf,.jpg)").pack(anchor="w")
        self.ce = ttk.Entry(of)
        self.ce.pack(fill="x", pady=5)
        ttk.Label(of, text="Taille minimale (MB)").pack(anchor="w")
        self.cm = ttk.Entry(of)
        self.cm.pack(fill="x", pady=5)
        ttk.Label(of, text="Exceptions (séparées par des virgules)").pack(anchor="w")
        self.cx = ttk.Entry(of)
        self.cx.pack(fill="x", pady=5)
        bf = ttk.Frame(ff)
        bf.pack(fill="x", pady=10)
        ttk.Button(bf, text="Prévisualiser", command=self.run_async_preview).pack(side="left", padx=5)
        ttk.Button(bf, text="Retour", command=self.show_menu_frame).pack(side="right", padx=5)

    def initialize_doublons_frame(self):
        t = ttk.Label(self.fd, text="Supprimer les doublons", style="Title.TLabel")
        t.pack(pady=10)
        df = ttk.LabelFrame(self.fd, text="Dossier cible", padding=10)
        df.pack(fill="x", padx=20, pady=10)
        self.dr = ttk.Entry(df)
        self.dr.pack(side="left", fill="x", expand=True, padx=5)
        ttk.Button(df, text="Parcourir", command=lambda: self.choisir_rep(self.dr)).pack(side="right", padx=5)
        bf = ttk.Frame(self.fd)
        bf.pack(fill="x", pady=10)
        ttk.Button(bf, text="Rechercher les doublons", command=self.run_async_doublons).pack(side="left", padx=5)
        ttk.Button(bf, text="Retour", command=self.show_menu_frame).pack(side="right", padx=5)

    def initialize_analyse_frame(self):
        t = ttk.Label(self.fa, text="Tableau de bord", style="Title.TLabel")
        t.pack(pady=10)

        retour_button = ttk.Button(self.fa, text="Retour au menu", command=self.show_menu_frame, style="Modern.TButton")
        retour_button.pack(anchor="ne", padx=20)

        main_container = ttk.Frame(self.fa)
        main_container.pack(fill="both", expand=True, padx=20, pady=10)

        folder_frame = ttk.LabelFrame(main_container, text="Sélection du dossier", padding=15)
        folder_frame.pack(fill="x", pady=10)
        
        folder_content = ttk.Frame(folder_frame)
        folder_content.pack(fill="x", expand=True)
        
        self.ar = ttk.Entry(folder_content)
        self.ar.pack(side="left", fill="x", expand=True, padx=5)
        ttk.Button(folder_content, text="Parcourir", command=lambda: self.choisir_rep(self.ar)).pack(side="left", padx=5)
        ttk.Button(folder_content, text="Analyser", command=self.run_async_analyse).pack(side="left", padx=5)

        stats_frame = ttk.Frame(main_container)
        stats_frame.pack(fill="x", pady=(0, 20))

        self.stats_boxes = []
        stats_data = [
            ("Espace utilisé", "0%", "disk_usage"),
            ("Espace libre", "0 GB", "free_space"),
            ("Santé disque", "Bon", "health"),
            ("Activité E/S", "0 MB/s", "io")
        ]

        for i, (title, initial_value, tag) in enumerate(stats_data):
            box_frame = ttk.Frame(stats_frame)
            box_frame.pack(side="left", expand=True, fill="both", padx=5)
            
            box = ttk.LabelFrame(box_frame, padding=15)
            box.pack(fill="both", expand=True)
            
            ttk.Label(box, text=title, style="Subtitle.TLabel").pack(anchor="w")
            value_label = ttk.Label(box, text=initial_value, style="Stats.TLabel")
            value_label.pack(anchor="e", pady=5)
            self.stats_boxes.append((tag, value_label))

        graphs_frame = ttk.LabelFrame(main_container, text="Utilisation du disque", padding=15)
        graphs_frame.pack(fill="both", expand=True, pady=10)

        self.loading_label = ttk.Label(graphs_frame, text="Chargement des graphiques...", style="Subtitle.TLabel")
        self.loading_label.pack(pady=10)

        self.anal_fig = plt.Figure(figsize=(10, 6), dpi=100)
        self.anal_canvas = FigureCanvasTkAgg(self.anal_fig, master=graphs_frame)
        self.anal_canvas.get_tk_widget().pack(fill="both", expand=True)

        files_frame = ttk.LabelFrame(main_container, text="Distribution des fichiers", padding=15)
        files_frame.pack(fill="both", expand=True, pady=10)

        self.files_tree = ttk.Treeview(files_frame, columns=("Type", "Count", "Size", "Percent"), 
                                      show="headings", height=5)
        self.files_tree.heading("Type", text="Type de fichier")
        self.files_tree.heading("Count", text="Nombre")
        self.files_tree.heading("Size", text="Taille")
        self.files_tree.heading("Percent", text="Pourcentage")
        
        self.files_tree.column("Type", width=150)
        self.files_tree.column("Count", width=100)
        self.files_tree.column("Size", width=100)
        self.files_tree.column("Percent", width=100)
        
        scrollbar = ttk.Scrollbar(files_frame, orient="vertical", command=self.files_tree.yview)
        self.files_tree.configure(yscrollcommand=scrollbar.set)
        
        self.files_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        button_frame = ttk.Frame(main_container)
        button_frame.pack(fill="x", pady=10)
        
        ttk.Button(button_frame, text="Exporter PDF", command=lambda: self.export_report('pdf')).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Exporter Excel", command=lambda: self.export_report('excel')).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Rafraîchir", command=self.refresh_dashboard).pack(side="left", padx=5)

        self.s.configure("Stats.TLabel", font=('Helvetica', 20, 'bold'))
        self.s.configure("Subtitle.TLabel", font=('Helvetica', 12))
        
        self.refresh_dashboard()

    def update_stats_box(self, tag, value):
        for box_tag, label in self.stats_boxes:
            if box_tag == tag:
                label.configure(text=value)
                break

    def show_menu_frame(self):
        self.show_frame(self.fm)

    def choisir_rep(self, ew):
        d = filedialog.askdirectory()
        if d:
            ew.delete(0, tk.END)
            ew.insert(0, d)

    def run_async_preview(self):
        threading.Thread(target=lambda: self.l.run_until_complete(self.preview_elements())).start()

    def run_async_doublons(self):
        threading.Thread(target=lambda: self.l.run_until_complete(self.supprimer_doublons())).start()

    def run_async_analyse(self):
        threading.Thread(target=lambda: self.l.run_until_complete(self.afficher_analyse())).start()

    async def preview_elements(self):
        try:
            self.st.set("Analyse en cours...")
            self.p.set(0)
            r = self.cr.get()
            ds = self.cd.get()
            o = self.vo.get()
            es = self.ce.get()
            ms = self.cm.get()
            ex = [e.strip() for e in self.cx.get().split(",") if e.strip()]
            
            if not os.path.exists(r):
                messagebox.showerror("Erreur", "Le répertoire spécifié n'existe pas.")
                return
                
            exts = [e.strip().lower() for e in es.split(",") if e.strip()] if es else []
            min_size = int(ms) * 1024 * 1024 if ms.isdigit() else 0
            dr = datetime.datetime.strptime(ds, "%Y-%m-%d")

     
            preview_window = tk.Toplevel(self.r)
            preview_window.title("Prévisualisation des fichiers")
            preview_window.geometry("800x600")

          
            preview_window.main_frame = ttk.Frame(preview_window)
            preview_window.main_frame.pack(fill="both", expand=True, padx=20, pady=10)

            preview_window.tree_frame = ttk.LabelFrame(preview_window.main_frame, text="Fichiers à supprimer", padding=15)
            preview_window.tree_frame.pack(fill="both", expand=True, pady=10)

            
            preview_window.tree = ttk.Treeview(preview_window.tree_frame, 
                                             columns=("Chemin", "Taille", "Date"), 
                                             show="headings")
            preview_window.tree.heading("Chemin", text="Chemin")
            preview_window.tree.heading("Taille", text="Taille")
            preview_window.tree.heading("Date", text="Date")
            
            preview_window.tree.column("Chemin", width=400)
            preview_window.tree.column("Taille", width=100)
            preview_window.tree.column("Date", width=150)

      
            preview_window.scrollbar = ttk.Scrollbar(preview_window.tree_frame, 
                                                   orient="vertical", 
                                                   command=preview_window.tree.yview)
            preview_window.tree.configure(yscrollcommand=preview_window.scrollbar.set)

            preview_window.tree.pack(side="left", fill="both", expand=True)
            preview_window.scrollbar.pack(side="right", fill="y")

            tf = sum([len(files) for _, _, files in os.walk(r)])
            pf = 0
            files_to_delete = []

            for root, _, files in os.walk(r):
                for file in files:
                    path = os.path.join(root, file)
                    if self.suppr_crit(path, dr, o, exts, min_size, ex):
                        try:
                            size = os.path.getsize(path)
                            date = datetime.datetime.fromtimestamp(os.path.getctime(path))
                            preview_window.tree.insert("", "end", values=(
                                path,
                                f"{size/1024/1024:.2f} MB",
                                date.strftime("%Y-%m-%d %H:%M")
                            ))
                            files_to_delete.append(path)
                        except Exception as e:
                            logger.error(f"Erreur lors de l'analyse du fichier {path}: {e}")

                    pf += 1
                    self.p.set((pf / tf) * 100)
                    await asyncio.sleep(0)
                    self.r.update_idletasks()

            preview_window.summary_label = ttk.Label(preview_window.main_frame, 
                                                   text=f"Total: {len(files_to_delete)} fichiers trouvés",
                                                   style="Subtitle.TLabel")
            preview_window.summary_label.pack(pady=10)

            preview_window.button_frame = ttk.Frame(preview_window.main_frame)
            preview_window.button_frame.pack(fill="x", pady=10)

            preview_window.confirm_button = ttk.Button(
                preview_window.button_frame,
                text="Confirmer la suppression",
                command=lambda: self.confirm_suppression(files_to_delete, preview_window)
            )
            preview_window.confirm_button.pack(side="left", padx=5)

            preview_window.cancel_button = ttk.Button(
                preview_window.button_frame,
                text="Annuler",
                command=preview_window.destroy
            )
            preview_window.cancel_button.pack(side="right", padx=5)

            self.st.set("Prêt")
            self.p.set(0)

        except Exception as e:
            logger.error(f"Erreur lors de la prévisualisation: {e}")
            messagebox.showerror("Erreur", f"Une erreur est survenue: {str(e)}")

    def suppr_crit(self, c, dr, o, exts, min_size, ex):
        if any(e in c for e in ex):
            return False
        ts = os.path.getctime(c)
        df = datetime.datetime.fromtimestamp(ts)
        if exts:
            _, ext = os.path.splitext(c)
            if ext not in exts:
                return False
        if min_size and os.path.getsize(c) < min_size:
            return False
        if o == "avant":
            return df < dr
        elif o == "apres":
            return df > dr
        return False

    def confirm_suppression(self, files_to_delete, window):
        if not files_to_delete:
            messagebox.showinfo("Information", "Aucun fichier à supprimer.")
            window.destroy()
            return

        if messagebox.askyesno("Confirmation", "Êtes-vous sûr de vouloir supprimer ces fichiers ?"):
            try:
                for path in files_to_delete:
                    try:
                        if os.path.exists(path):
                            if os.path.isfile(path):
                                os.remove(path)
                            elif os.path.isdir(path):
                                shutil.rmtree(path)
                    except Exception as e:
                        logger.warning(f"Impossible de supprimer le fichier {path}: {e}")
                        continue

                messagebox.showinfo("Succès", "Les fichiers ont été supprimés avec succès.")
            except Exception as e:
                logger.error(f"Erreur lors de la suppression: {e}")
                messagebox.showerror("Erreur", f"Une erreur est survenue lors de la suppression: {str(e)}")
            finally:
                window.destroy()

    async def supprimer_doublons(self):
        try:
            self.st.set("Recherche des doublons...")
            self.p.set(0)
            r = self.dr.get()
            if not os.path.exists(r):
                messagebox.showerror("Erreur", "Le répertoire spécifié n'existe pas.")
                return

            p = tk.Toplevel(self.r)
            p.title("Fichiers en double")
            p.geometry("600x400")
            t = ttk.Treeview(p, columns=("Chemin", "Taille"), show="headings")
            t.heading("Chemin", text="Chemin")
            t.heading("Taille", text="Taille")
            t.pack(fill="both", expand=True, padx=10, pady=10)
            h = {}
            d = []
            tf = sum([len(files) for _, _, files in os.walk(r)])
            pf = 0
            for root, _, files in os.walk(r):
                for file in files:
                    path = os.path.join(root, file)
                    try:
                        with open(path, "rb") as f:
                            hf = hashlib.md5(f.read()).hexdigest()
                            if hf in h:
                                d.append(path)
                                size = os.path.getsize(path)
                                t.insert("", "end", values=(path, f"{size/1024/1024:.2f} MB"))
                            else:
                                h[hf] = path
                    except Exception as e:
                        logger.warning(f"Impossible de lire le fichier {path}: {e}")
                    pf += 1
                    self.p.set((pf / tf) * 100)
                    self.r.update_idletasks()
                    await asyncio.sleep(0)
            if not d:
                messagebox.showinfo("Information", "Aucun doublon trouvé.")
                p.destroy()
                return

            ttk.Button(p, text="Supprimer les doublons", command=lambda: self.confirm_suppression(d, p)).pack(pady=10)
            self.st.set("Prêt")
            self.p.set(0)
        except Exception as e:
            logger.error(f"Erreur lors de la recherche des doublons: {e}")
            messagebox.showerror("Erreur", f"Une erreur est survenue: {str(e)}")

    async def afficher_analyse(self):
        try:
            self.st.set("Analyse en cours...")
            self.p.set(0)
            r = self.ar.get() if self.ar.get() else os.getcwd()
            
            if not os.path.exists(r):
                messagebox.showerror("Erreur", "Le répertoire spécifié n'existe pas.")
                return

            result_window = tk.Toplevel(self.r)
            result_window.title(f"Analyse de {os.path.basename(r)}")
            result_window.geometry("800x600")
            
 
            main_container = ttk.Frame(result_window)
            main_container.pack(fill="both", expand=True, padx=20, pady=10)

     
            stats_frame = ttk.LabelFrame(main_container, text="Informations du dossier", padding=15)
            stats_frame.pack(fill="x", pady=10)

     
            health_data = self.dm.get_disk_health(r)
            if health_data:
                stats_info = [
                    ("Espace total:", f"{health_data['total']/1024/1024/1024:.1f} GB"),
                    ("Espace utilisé:", f"{health_data['used']/1024/1024/1024:.1f} GB ({health_data['percent']}%)"),
                    ("Espace libre:", f"{health_data['free']/1024/1024/1024:.1f} GB"),
                ]
                
                for label, value in stats_info:
                    row = ttk.Frame(stats_frame)
                    row.pack(fill="x", pady=2)
                    ttk.Label(row, text=label, style="Subtitle.TLabel").pack(side="left", padx=5)
                    ttk.Label(row, text=value, style="Stats.TLabel").pack(side="right", padx=5)

            tree_frame = ttk.LabelFrame(main_container, text="Distribution des fichiers", padding=15)
            tree_frame.pack(fill="both", expand=True, pady=10)

            result_tree = ttk.Treeview(tree_frame, 
                                     columns=("Type", "Count", "Size", "Percent", "LastModified"), 
                                     show="headings", 
                                     height=15)
            result_tree.heading("Type", text="Type de fichier")
            result_tree.heading("Count", text="Nombre")
            result_tree.heading("Size", text="Taille")
            result_tree.heading("Percent", text="Pourcentage")
            result_tree.heading("LastModified", text="Dernière modification")
            
            result_tree.column("Type", width=150)
            result_tree.column("Count", width=100)
            result_tree.column("Size", width=150)
            result_tree.column("Percent", width=100)
            result_tree.column("LastModified", width=150)
            
            scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=result_tree.yview)
            result_tree.configure(yscrollcommand=scrollbar.set)
            
            result_tree.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")

       
            types = {}
            total = 0
            tf = sum([len(files) for _, _, files in os.walk(r)])
            pf = 0
            last_modified = {}

            for root, _, files in os.walk(r):
                for file in files:
                    path = os.path.join(root, file)
                    try:
                        size = os.path.getsize(path)
                        ext = os.path.splitext(file)[1].lower()
                        if not ext:
                            ext = "(sans extension)"
                        total += size
                        
                        mod_time = datetime.datetime.fromtimestamp(os.path.getmtime(path))
                        if ext not in last_modified or mod_time > last_modified[ext]:
                            last_modified[ext] = mod_time
                        
                        if ext in types:
                            types[ext]['size'] += size
                            types[ext]['count'] += 1
                        else:
                            types[ext] = {'size': size, 'count': 1}
                            
                    except Exception as e:
                        logger.error(f"Impossible d'analyser le fichier {path}: {e}")
                    pf += 1
                    self.p.set((pf / tf) * 100)
                    await asyncio.sleep(0)
                    self.r.update_idletasks()


            sorted_types = sorted(types.items(), key=lambda x: x[1]['size'], reverse=True)

            for ext, data in sorted_types:
                size_mb = data['size'] / 1024 / 1024
                percent = (data['size'] / total) * 100 if total > 0 else 0
                result_tree.insert("", "end", values=(
                    ext,
                    data['count'],
                    f"{size_mb:.1f} MB",
                    f"{percent:.1f}%",
                    last_modified[ext].strftime("%Y-%m-%d %H:%M")
                ))

  
            result_tree.insert("", "end", values=(
                "TOTAL",
                sum(data['count'] for data in types.values()),
                f"{total/1024/1024:.1f} MB",
                "100%",
                "-"
            ))

            button_frame = ttk.Frame(result_window)
            button_frame.pack(fill="x", pady=10, padx=10)
            
            ttk.Button(button_frame, text="Exporter PDF", 
                      command=lambda: self.export_report('pdf')).pack(side="left", padx=5)
            ttk.Button(button_frame, text="Exporter Excel", 
                      command=lambda: self.export_report('excel')).pack(side="left", padx=5)
            ttk.Button(button_frame, text="Fermer", 
                      command=result_window.destroy).pack(side="right", padx=5)

            self.st.set("Prêt")
            self.p.set(0)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse: {e}")
            messagebox.showerror("Erreur", f"Une erreur est survenue: {str(e)}")

    def load_tasks(self):
        try:
            if os.path.exists('tasks.json'):
                with open('tasks.json', 'r') as f:
                    self.tasks = json.load(f)
                    for task in self.tasks:
                        self.schedule_task(task)
        except Exception as e:
            logger.error(f"Erreur lors du chargement des tâches: {e}")

    def save_tasks(self):
        try:
            with open('tasks.json', 'w') as f:
                json.dump(self.tasks, f)
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde des tâches: {e}")

    def schedule_task(self, task):
        try:
            def t():
                try:
                    if task['type'] == "Nettoyage automatique":
                        for root, dirs, files in os.walk(task['directory']):
                            for file in files:
                                path = os.path.join(root, file)
                                try:
                                    os.remove(path)
                                except Exception as e:
                                    logger.warning(f"Impossible de supprimer {path}: {e}")
                    elif task['type'] == "Recherche de doublons":
                        self.run_async_doublons()
                    elif task['type'] == "Analyse d'espace":
                        self.run_async_analyse()
                        
                    if task['notify']:
                        messagebox.showinfo("Tâche planifiée", f"La tâche {task['type']} a été exécutée avec succès")
                except Exception as e:
                    logger.error(f"Erreur lors de l'exécution de la tâche planifiée: {e}")

            if task['frequency'] == "quotidien":
                schedule.every().day.at(task['time']).do(t)
            elif task['frequency'] == "hebdomadaire":
                schedule.every().week.at(task['time']).do(t)
            elif task['frequency'] == "mensuel":
                schedule.every(30).days.at(task['time']).do(t)
        except Exception as e:
            logger.error(f"Erreur lors de la planification de la tâche: {e}")

    def calculate_next_run(self, frequency, time_str):
        hour, minute = map(int, time_str.split(':'))
        now = datetime.datetime.now()
        next_run = now.replace(hour=hour, minute=minute)
        
        if next_run <= now:
            if frequency == "quotidien":
                next_run += datetime.timedelta(days=1)
            elif frequency == "hebdomadaire":
                next_run += datetime.timedelta(days=7)
            elif frequency == "mensuel":
                next_run += datetime.timedelta(days=30)
        
        return next_run

    def show_manual(self):
        mw = tk.Toplevel(self.r)
        mw.title("Manuel d'utilisation")
        mw.geometry("600x400")
        tf = ttk.Frame(mw)
        tf.pack(fill="both", expand=True, padx=10, pady=10)
        s = ttk.Scrollbar(tf)
        s.pack(side="right", fill="y")
        tw = tk.Text(tf, wrap="word", yscrollcommand=s.set)
        tw.pack(side="left", fill="both", expand=True)
        s.config(command=tw.yview)
        mt = """
# Manuel Utilisateur - DataSweep

## 1. Menu Principal

### Barre de Menu
- **Fichier**
  - Nouveau : Démarre une nouvelle analyse
  - Ouvrir : Ouvre un rapport précédent
  - Enregistrer : Sauvegarde l'analyse actuelle
  - Quitter : Ferme l'application

- **Affichage**
  - Mode Sombre/Clair : Change le thème de l'application
  - Actualiser : Rafraîchit les données affichées

## 2. Fonctions de Nettoyage

### Suppression par Critères
- Sélectionner Dossier : Ouvre un explorateur pour choisir le dossier à analyser
- Définir Date : Choisir une date pour supprimer les fichiers plus anciens
- Extensions : Liste des extensions à cibler (ex: .tmp, .log)
- Taille : Définir une taille minimale en Mo
- Exceptions : Ajouter des fichiers/dossiers à ne pas supprimer
- Prévisualiser : Voir les fichiers qui seront supprimés
- Supprimer : Exécute la suppression après confirmation

### Recherche de Doublons
- Sélectionner Dossier : Choisir le dossier à analyser
- Analyser : Lance la recherche de doublons
- Supprimer : Efface les doublons sélectionnés

## 3. Analyse de l'Espace

### Vue Générale
- Espace Total : Affiche la capacité totale du disque
- Espace Utilisé : Montre l'espace occupé (en Go et %)
- Espace Libre : Indique l'espace disponible

### Analyse Détaillée
- Par Type : Répartition par type de fichier
- Par Taille : Liste des plus gros fichiers
- Par Date : Distribution temporelle
- Exporter : Sauvegarde l'analyse en PDF/Excel

## 4. Planification

### Nouvelle Tâche
- Type : Choisir le type de nettoyage
- Fréquence : 
  * Quotidienne
  * Hebdomadaire
  * Mensuelle
- Heure : Définir l'heure d'exécution
- Paramètres : Configurer les critères
- Notifications : Activer/désactiver les alertes

### Gestion des Tâches
- Liste : Voir toutes les tâches planifiées
- Modifier : Changer les paramètres
- Supprimer : Annuler une tâche
- Historique : Voir les exécutions passées

## 5. Prévisualisation

### Fenêtre de Prévisualisation
- Liste des Fichiers : Affiche les fichiers concernés
- Détails :
  * Nom du fichier
  * Chemin complet
  * Taille
  * Date de modification
- Actions :
  * Cocher/Décocher des fichiers
  * Trier la liste
  * Filtrer les résultats

## 6. Rapports

### Génération de Rapports
- Format : 
  * PDF
  * Excel
  * CSV
- Contenu :
  * Résumé des actions
  * Statistiques détaillées
  * Graphiques
  * Liste des fichiers

### Consultation
- Ouvrir : Voir un rapport existant
- Imprimer : Imprimer le rapport
- Partager : Exporter le rapport

## 7. Paramètres

### Configuration Générale
- Langue : Changer la langue
- Thème : Mode clair/sombre
- Notifications : Gérer les alertes

### Préférences
- Dossiers par défaut : Définir les chemins
- Critères par défaut : Configuration standard
- Raccourcis : Personnaliser les touches

## 8. Raccourcis Clavier

### Navigation
- Ctrl+N : Nouveau nettoyage
- Ctrl+O : Ouvrir
- Ctrl+S : Sauvegarder
- Ctrl+Q : Quitter
- F5 : Actualiser
- F1 : Aide

### Actions
- Ctrl+D : Recherche doublons
- Ctrl+A : Analyse espace
- Ctrl+P : Planification
- Ctrl+M : Menu principal
- Esc : Annuler/Fermer

## 9. Messages d'Erreur

### Types d'Erreurs
- Accès Refusé : Vérifier les permissions
- Fichier Occupé : Fermer les applications
- Espace Insuffisant : Libérer de l'espace
- Chemin Invalide : Vérifier le chemin

### Solutions
- Redémarrer l'application
- Vérifier les droits administrateur
- Libérer de l'espace disque
- Fermer les applications en conflit

## 10. Conseils d'Utilisation

### Bonnes Pratiques
- Toujours prévisualiser avant suppression
- Sauvegarder les données importantes
- Commencer par de petits dossiers
- Vérifier les exceptions

### Optimisation
- Nettoyer régulièrement
- Utiliser la planification
- Exporter les rapports
- Maintenir une liste d'exceptions
"""
        tw.insert("1.0", mt)
        tw.config(state="disabled")

    def show_about(self):
        at = """DataSweep
Version 1.0
Un outil pour gérer et nettoyer vos fichiers efficacement.
Développé avec Python et Tkinter.
© 2024 Tous droits réservés."""
        messagebox.showinfo("À propos", at)

    def initialize_planif_frame(self):
        t = ttk.Label(self.fp, text="Planifier une tâche", style="Title.TLabel")
        t.pack(pady=10)

        main_container = ttk.Frame(self.fp)
        main_container.pack(fill="both", expand=True, padx=20, pady=10)

        folder_frame = ttk.LabelFrame(main_container, text="Dossier cible", padding=15)
        folder_frame.pack(fill="x", pady=10)

        folder_content = ttk.Frame(folder_frame)
        folder_content.pack(fill="x", expand=True)

        self.pr = ttk.Entry(folder_content)
        self.pr.pack(side="left", fill="x", expand=True, padx=5)
        ttk.Button(folder_content, text="Parcourir", 
                  command=lambda: self.choisir_rep(self.pr)).pack(side="right", padx=5)

        config_frame = ttk.LabelFrame(main_container, text="Configuration de la tâche", padding=15)
        config_frame.pack(fill="x", pady=10)

        ttk.Label(config_frame, text="Type de tâche:", style="Subtitle.TLabel").pack(anchor="w", pady=(0, 5))
        self.task_type = ttk.Combobox(config_frame, values=[
            "Nettoyage automatique",
            "Recherche de doublons",
            "Analyse d'espace",
            "Sauvegarde"
        ])
        self.task_type.set("Nettoyage automatique")
        self.task_type.pack(fill="x", pady=(0, 10))

        ttk.Label(config_frame, text="Fréquence:", style="Subtitle.TLabel").pack(anchor="w", pady=(0, 5))
        self.vf = tk.StringVar(value="quotidien")
        
        freq_frame = ttk.Frame(config_frame)
        freq_frame.pack(fill="x", pady=(0, 10))
        
        frequencies = [
            ("Quotidien", "quotidien"),
            ("Hebdomadaire", "hebdomadaire"),
            ("Mensuel", "mensuel")
        ]
        
        for text, value in frequencies:
            radio = ttk.Radiobutton(freq_frame, text=text, variable=self.vf, value=value)
            radio.pack(side="left", padx=10)

        time_frame = ttk.Frame(config_frame)
        time_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(time_frame, text="Heure d'exécution:").pack(side="left", padx=5)
        self.hour_var = tk.StringVar(value="00")
        self.minute_var = tk.StringVar(value="00")
        
        hour_spin = ttk.Spinbox(time_frame, from_=0, to=23, width=5, 
                               textvariable=self.hour_var, format="%02.0f")
        hour_spin.pack(side="left", padx=5)
        
        ttk.Label(time_frame, text=":").pack(side="left")
        
        minute_spin = ttk.Spinbox(time_frame, from_=0, to=59, width=5,
                                 textvariable=self.minute_var, format="%02.0f")
        minute_spin.pack(side="left", padx=5)

        options_frame = ttk.LabelFrame(main_container, text="Options avancées", padding=15)
        options_frame.pack(fill="x", pady=10)

        retention_frame = ttk.Frame(options_frame)
        retention_frame.pack(fill="x", pady=5)
        ttk.Label(retention_frame, text="Période de rétention (jours):").pack(side="left", padx=5)
        self.retention_var = tk.StringVar(value="30")
        ttk.Entry(retention_frame, textvariable=self.retention_var, width=10).pack(side="left", padx=5)

        self.notify_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Envoyer des notifications", 
                       variable=self.notify_var).pack(anchor="w", pady=5)

        button_frame = ttk.Frame(main_container)
        button_frame.pack(fill="x", pady=20)
        
        ttk.Button(button_frame, text="Planifier", 
                  command=self.planifier_tache).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Retour",
                  command=self.show_menu_frame).pack(side="right", padx=5)

        status_frame = ttk.LabelFrame(main_container, text="Tâches planifiées", padding=15)
        status_frame.pack(fill="x", pady=10)
        
        self.scheduled_tasks = ttk.Treeview(status_frame, 
                                          columns=("Task", "Frequency", "Next Run"),
                                          show="headings",
                                          height=3)
        
        self.scheduled_tasks.heading("Task", text="Tâche")
        self.scheduled_tasks.heading("Frequency", text="Fréquence")
        self.scheduled_tasks.heading("Next Run", text="Prochaine exécution")
        
        self.scheduled_tasks.column("Task", width=150)
        self.scheduled_tasks.column("Frequency", width=100)
        self.scheduled_tasks.column("Next Run", width=150)
        
        self.scheduled_tasks.pack(fill="x", pady=5)

    def planifier_tache(self):
        try:
            r = self.pr.get()
            f = self.vf.get()
            task_type = self.task_type.get()
            hour = self.hour_var.get()
            minute = self.minute_var.get()
            retention = self.retention_var.get()
            
            if not os.path.exists(r):
                messagebox.showerror("Erreur", "Le répertoire spécifié n'existe pas.")
                return

            time_str = f"{hour.zfill(2)}:{minute.zfill(2)}"
            
            task = {
                'directory': r,
                'frequency': f,
                'type': task_type,
                'time': time_str,
                'retention': retention,
                'notify': self.notify_var.get()
            }
            
            self.tasks.append(task)
            self.save_tasks()
            
            self.schedule_task(task)
            
            next_run = self.calculate_next_run(f, time_str)
            self.scheduled_tasks.insert("", "end", values=(
                task_type,
                f,
                next_run.strftime("%Y-%m-%d %H:%M")
            ))

            messagebox.showinfo("Succès", "La tâche a été planifiée avec succès.")
            
        except Exception as e:
            logger.error(f"Erreur lors de la planification: {e}")
            messagebox.showerror("Erreur", f"Une erreur est survenue: {str(e)}")

if __name__ == "__main__":
    app = None
    try:
        app = ModernFileManager()
        app.dm.start_monitoring(os.getcwd(), app.refresh_dashboard)
        app.run()
    except Exception as e:
        logging.error(f"Erreur fatale: {e}")
        messagebox.showerror("Erreur", f"Une erreur fatale est survenue: {str(e)}")
    finally:
        if app and hasattr(app, 'dm'):
            app.dm.stop_monitoring()
