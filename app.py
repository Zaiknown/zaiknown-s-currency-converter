# app.py

import tkinter as tk
from tkinter import ttk, font, messagebox
from PIL import Image, ImageTk, ImageDraw
import io
import threading
from queue import Queue
from concurrent.futures import ThreadPoolExecutor
import sv_ttk
import webbrowser
import os
import json
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

from api_client import ApiClient

class CurrencyConverterApp:
    def __init__(self, root):
        self.root = root
        self.api_client = ApiClient()
        self.gui_queue = Queue()

        # Variáveis de estado
        self.nomes_moedas = {}
        self.bandeiras_cache = {}
        self.favoritos = set()
        self.ultimo_par_convertido = None
        self.after_id = None
        self.tema_atual = "dark"
        self.currency_map = {} # <-- MUDANÇA: Dicionário vazio para o mapa

        # Constantes
        self.CACHE_DIR = "flag_cache"
        self.FAVORITOS_FILE = "favorites.json"
        
        self._inicializar_app()
        self._criar_widgets()
        self.processar_fila()

    def _inicializar_app(self):
        """Prepara o ambiente do app, como criar pastas e carregar dados iniciais."""
        if not os.path.exists(self.CACHE_DIR):
            os.makedirs(self.CACHE_DIR)
        
        self._carregar_mapa_moedas() # <-- MUDANÇA: Carrega o novo arquivo JSON
        self.carregar_favoritos()
        
        self.root.title("Zaiknown's Currency Converter")
        self.root.iconbitmap("icon.ico")
        self.root.minsize(580, 550)
        sv_ttk.set_theme(self.tema_atual)
        
        threading.Thread(target=self._obter_nomes_moedas_worker, daemon=True).start()

    # --- MUDANÇA: Nova função para carregar o mapa de moedas do arquivo JSON ---
    def _carregar_mapa_moedas(self):
        """Carrega o mapeamento de moeda para país do arquivo currency_map.json."""
        try:
            with open("currency_map.json", "r") as f:
                self.currency_map = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # Se o arquivo não existir ou for inválido, usa um mapa vazio
            self.currency_map = {}

    def _criar_widgets(self):
        # ... (todo o código de criação de widgets permanece o mesmo)
        self.FONT_LABEL = font.Font(family="Bahnschrift", size=11)
        self.FONT_TITULO_CREDITOS = font.Font(family="Bahnschrift", size=14, weight="bold")
        self.FONT_RESULTADO_B = font.Font(family="Bahnschrift", size=16, weight="bold")
        self.COR_DESTAQUE = "#0078D7" 
        self.COR_HOVER = "#0098F7"
        self.COR_MENU_HOVER = "#3e3e3e"
        try:
            self.FOTO_CRIADOR = self.criar_foto_circular("foto.jpg", 120)
        except Exception:
            self.FOTO_CRIADOR = None
        self.root.bind("<F11>", self.toggle_fullscreen)
        self.root.bind("<Escape>", self.sair_fullscreen)
        self.placeholder_bandeira = ImageTk.PhotoImage(Image.new('RGBA', (35, 25), (50, 50, 50, 255)))
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        frame_principal = ttk.Frame(self.root)
        frame_principal.grid(row=0, column=0, sticky="nsew")
        frame_principal.columnconfigure(0, weight=1)
        frame_principal.rowconfigure(4, weight=1)
        menu_frame = ttk.Frame(frame_principal, style='Card.TFrame')
        menu_frame.grid(row=0, column=0, sticky='ew')
        menu_left_frame = ttk.Frame(menu_frame)
        menu_left_frame.pack(side='left', padx=(5,0))
        style = ttk.Style()
        style.configure('Custom.TMenubutton', font=self.FONT_LABEL, padding=(8, 6))
        style.map('Custom.TMenubutton', background=[('active', self.COR_MENU_HOVER)])
        style.configure('Custom.TButton', font=self.FONT_LABEL, padding=(8, 6))
        style.map('Custom.TButton', background=[('active', self.COR_MENU_HOVER)])
        view_menubutton = ttk.Menubutton(menu_left_frame, text="Exibir", style='Custom.TMenubutton')
        view_menubutton.pack(side='left')
        view_menu = tk.Menu(view_menubutton, tearoff=0)
        view_menu.add_command(label="Alternar Tema (Claro/Escuro)", command=self.alternar_tema)
        view_menu.add_separator()
        view_menu.add_command(label="Tela Cheia (F11)", command=self.toggle_fullscreen)
        view_menu.add_command(label="Sair da Tela Cheia (Esc)", command=self.sair_fullscreen)
        view_menubutton['menu'] = view_menu
        creditos_button = ttk.Button(menu_left_frame, text="Créditos", style='Custom.TButton', command=self.mostrar_creditos)
        creditos_button.pack(side='left', padx=5)
        sair_button = ttk.Button(menu_frame, text="Sair", style='Custom.TButton', command=self.root.quit)
        sair_button.pack(side='right', padx=5, pady=(2,2))
        ttk.Separator(frame_principal).grid(row=1, column=0, sticky='ew', pady=(0, 15))
        ttk.Label(frame_principal, text="Conversor de Moedas", font=font.Font(family="Bahnschrift", size=20, weight="bold")).grid(row=2, column=0, pady=(0, 20))
        controles_frame = ttk.LabelFrame(frame_principal, text="Configuração da Conversão", padding=(25, 15))
        controles_frame.grid(row=3, column=0, sticky="ew", padx=50)
        controles_frame.columnconfigure(2, weight=1)
        controles_frame.columnconfigure(4, weight=0)
        validation_command = (self.root.register(self.validar_entrada_numerica), '%P')
        ttk.Label(controles_frame, text="Valor:", font=self.FONT_LABEL).grid(row=0, column=0, columnspan=2, padx=5, pady=10, sticky="w")
        self.entrada_valor = ttk.Entry(controles_frame, font=self.FONT_LABEL, width=30, validate='key', validatecommand=validation_command)
        self.entrada_valor.grid(row=0, column=2, columnspan=3, padx=5, pady=10, sticky="ew")
        ttk.Separator(controles_frame, orient="horizontal").grid(row=1, column=0, columnspan=5, pady=10, sticky="ew")
        ttk.Label(controles_frame, text="De:", font=self.FONT_LABEL).grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.flag_label_origem = ttk.Label(controles_frame, image=self.placeholder_bandeira)
        self.flag_label_origem.grid(row=2, column=1, padx=(5,0), pady=5, sticky="w")
        self.moeda_origem = ttk.Combobox(controles_frame, state="readonly", font=self.FONT_LABEL, width=15)
        self.moeda_origem.grid(row=2, column=2, padx=(5,10), pady=5, sticky="ew")
        self.favorito_origem_btn = ttk.Button(controles_frame, text="☆", style='Custom.TButton', width=3, command=lambda: self.toggle_favorito('origem'))
        self.favorito_origem_btn.grid(row=2, column=4, padx=5)
        inverter_button = ttk.Button(controles_frame, text="⇅", style='Custom.TButton', width=3, command=self.inverter_moedas)
        inverter_button.grid(row=3, column=3, padx=5)
        ttk.Label(controles_frame, text="Para:", font=self.FONT_LABEL).grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.flag_label_destino = ttk.Label(controles_frame, image=self.placeholder_bandeira)
        self.flag_label_destino.grid(row=4, column=1, padx=(5,0), pady=5, sticky="w")
        self.moeda_destino = ttk.Combobox(controles_frame, state="readonly", font=self.FONT_LABEL, width=15)
        self.moeda_destino.grid(row=4, column=2, padx=(5,10), pady=5, sticky="ew")
        self.favorito_destino_btn = ttk.Button(controles_frame, text="☆", style='Custom.TButton', width=3, command=lambda: self.toggle_favorito('destino'))
        self.favorito_destino_btn.grid(row=4, column=4, padx=5)
        action_frame = ttk.Frame(frame_principal)
        action_frame.grid(row=4, column=0, sticky="")
        botoes_acao_frame = ttk.Frame(action_frame)
        botoes_acao_frame.pack(pady=25)
        style.configure('Accent.TButton', font=font.Font(family="Bahnschrift", size=12, weight="bold"))
        style.map('Accent.TButton', background=[('active', self.COR_HOVER)], foreground=[('active', 'white')])
        self.converter_button = ttk.Button(botoes_acao_frame, text="Converter", command=self.converter, style='Accent.TButton', padding=(10, 5))
        self.converter_button.pack(side="left", padx=5)
        self.grafico_button = ttk.Button(botoes_acao_frame, text="Ver Histórico", command=self.mostrar_grafico, padding=(10, 5), state="disabled")
        self.grafico_button.pack(side="left", padx=5)
        resultado_frame = ttk.Frame(action_frame)
        resultado_frame.pack(pady=10)
        resultado_frame.columnconfigure(0, weight=1)
        self.label_resultado_origem = ttk.Label(resultado_frame, font=font.Font(family="Bahnschrift", size=12))
        self.label_resultado_origem.grid(row=0, column=0, columnspan=2)
        self.label_resultado_meio = ttk.Label(resultado_frame, font=self.FONT_LABEL, foreground="gray")
        self.label_resultado_meio.grid(row=1, column=0, columnspan=2)
        self.label_resultado_destino = ttk.Label(resultado_frame, font=font.Font(family="Bahnschrift", size=16, weight="bold"), foreground=self.COR_DESTAQUE)
        self.label_resultado_destino.grid(row=2, column=0, sticky="e")
        self.copiar_button = ttk.Button(resultado_frame, text="Copiar 📋", style='Custom.TButton', command=self.copiar_resultado, state="disabled")
        self.copiar_button.grid(row=2, column=1, sticky="w", padx=10)
        self.status_var = tk.StringVar()
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W, padding=5)
        status_bar.grid(row=1, column=0, sticky="ew")
        self.status_var.set("Iniciando...")
        self.entrada_valor.bind("<KeyRelease>", self.on_valor_changed)
        self.moeda_origem.bind("<<ComboboxSelected>>", self.on_moeda_selecionada)
        self.moeda_destino.bind("<<ComboboxSelected>>", self.on_moeda_selecionada)
        self.centralizar_janela(self.root)
    
    # --- Métodos Worker (que rodam em threads) ---
    def _obter_nomes_moedas_worker(self):
        try:
            nomes = self.api_client.obter_nomes_moedas()
            self.gui_queue.put(("moedas_carregadas", nomes))
        except Exception as e:
            self.gui_queue.put(("erro", f"Falha ao carregar nomes das moedas: {e}"))
            
    def _obter_taxas_worker(self, base, destino, valor):
        try:
            taxa_conversao = self.api_client.obter_taxa_atual(base, destino)
            convertido = valor * taxa_conversao
            nome_origem = self.nomes_moedas.get(base, base)
            nome_destino = self.nomes_moedas.get(destino, destino)
            resultado_dados = {"origem_str": f"{valor:,.2f} {nome_origem} ({base})", "destino_str": f"{convertido:,.2f} {nome_destino} ({destino})"}
            self.ultimo_par_convertido = (base, destino)
            self.gui_queue.put(("conversao_concluida", resultado_dados))
        except Exception as e:
            self.gui_queue.put(("erro", f"Erro na conversão: {e}"))
            
    def _obter_historico_worker(self, base, destino):
        try:
            datas, valores = self.api_client.obter_historico(base, destino)
            self.gui_queue.put(("historico_carregado", (datas, valores)))
        except Exception as e:
            self.gui_queue.put(("erro_historico", f"Não foi possível obter o histórico: {e}"))

    def _carregar_bandeira_worker(self, codigo_moeda):
        if codigo_moeda in self.bandeiras_cache: return
        caminho_arquivo_local = os.path.join(self.CACHE_DIR, f"{codigo_moeda}.png")
        try:
            pil_image = None
            if os.path.exists(caminho_arquivo_local):
                pil_image = Image.open(caminho_arquivo_local)
            else:
                # --- MUDANÇA: Usa o mapa carregado do JSON ---
                codigo_pais = self.currency_map.get(codigo_moeda, codigo_moeda[:2]).lower()
                url = f"https://flagcdn.com/w40/{codigo_pais}.png"
                resposta = self.api_client.session.get(url, timeout=10)
                resposta.raise_for_status()
                with open(caminho_arquivo_local, 'wb') as f:
                    f.write(resposta.content)
                pil_image = Image.open(io.BytesIO(resposta.content))
            if pil_image:
                pil_image = pil_image.convert("RGBA").resize((35, 25), Image.Resampling.LANCZOS)
                photo_image = ImageTk.PhotoImage(pil_image)
                self.bandeiras_cache[codigo_moeda] = photo_image
                self.gui_queue.put(("bandeira_individual_pronta", codigo_moeda))
        except Exception:
            self.bandeiras_cache[codigo_moeda] = self.placeholder_bandeira
            self.gui_queue.put(("bandeira_individual_pronta", codigo_moeda))

    # ... (o resto da classe app.py, com todas as outras funções, permanece o mesmo)
    def _pre_carregar_todas_as_bandeiras_worker(self, lista_moedas):
        with ThreadPoolExecutor(max_workers=10) as executor:
            executor.map(self._carregar_bandeira_worker, lista_moedas)
        self.gui_queue.put(("todas_bandeiras_carregadas", None))
    def converter(self):
        try:
            valor_str = self.entrada_valor.get().replace(',', '.')
            if not valor_str: return
            valor = float(valor_str)
            origem = self.moeda_origem.get()
            destino = self.moeda_destino.get()
            if not origem or not destino or '-' in origem or '-' in destino:
                return
            self.grafico_button.config(state="disabled")
            self.converter_button.config(state="disabled")
            self.copiar_button.config(state="disabled")
            self.label_resultado_destino.config(text="Convertendo...")
            threading.Thread(target=self._obter_taxas_worker, args=(origem, destino, valor), daemon=True).start()
        except (ValueError, tk.TclError):
            self.label_resultado_destino.config(text="")
            self.converter_button.config(state="normal")
    def on_valor_changed(self, event=None):
        if self.after_id:
            self.root.after_cancel(self.after_id)
        if not self.entrada_valor.get().strip():
            self.label_resultado_origem.config(text="")
            self.label_resultado_meio.config(text="")
            self.label_resultado_destino.config(text="")
            self.copiar_button.config(state="disabled")
            self.grafico_button.config(state="disabled")
            return
        self.after_id = self.root.after(500, self.converter)
    def on_moeda_selecionada(self, event):
        self.atualizar_estrelas_e_bandeiras()
        self.on_valor_changed()
    def inverter_moedas(self):
        origem = self.moeda_origem.get()
        destino = self.moeda_destino.get()
        if not origem or not destino or '-' in origem or '-' in destino: return
        self.moeda_origem.set(destino)
        self.moeda_destino.set(origem)
        self.atualizar_estrelas_e_bandeiras()
        if self.entrada_valor.get().strip():
            self.converter()
    def atualizar_listas_de_moedas(self):
        moedas_disponiveis = sorted(list(self.nomes_moedas.keys()))
        favoritos_ord = sorted(list(self.favoritos))
        nao_favoritos = [m for m in moedas_disponiveis if m not in self.favoritos]
        lista_final = moedas_disponiveis
        if favoritos_ord:
            lista_final = favoritos_ord + ["-"*20] + nao_favoritos
        self.moeda_origem['values'] = lista_final
        self.moeda_destino['values'] = lista_final
    def toggle_favorito(self, tipo):
        combobox = self.moeda_origem if tipo == 'origem' else self.moeda_destino
        moeda_selecionada = combobox.get()
        if not moeda_selecionada or '-' in moeda_selecionada: return
        if moeda_selecionada in self.favoritos:
            self.favoritos.remove(moeda_selecionada)
        else:
            self.favoritos.add(moeda_selecionada)
        self.salvar_favoritos()
        self.atualizar_listas_de_moedas()
        self.atualizar_estrelas_e_bandeiras()
    def atualizar_estrelas_e_bandeiras(self):
        origem = self.moeda_origem.get()
        destino = self.moeda_destino.get()
        self.favorito_origem_btn.config(text="⭐" if origem in self.favoritos else "☆")
        self.favorito_destino_btn.config(text="⭐" if destino in self.favoritos else "☆")
        if origem in self.bandeiras_cache:
            self.flag_label_origem.config(image=self.bandeiras_cache[origem])
        if destino in self.bandeiras_cache:
            self.flag_label_destino.config(image=self.bandeiras_cache[destino])
    def processar_fila(self):
        try:
            while not self.gui_queue.empty():
                tipo_msg, dados = self.gui_queue.get_nowait()
                if tipo_msg == "moedas_carregadas":
                    self.nomes_moedas = dados
                    self.total_bandeiras = len(self.nomes_moedas)
                    self.bandeiras_carregadas_contador = 0
                    self.atualizar_listas_de_moedas()
                    self.moeda_origem.set("USD")
                    self.moeda_destino.set("BRL")
                    self.atualizar_estrelas_e_bandeiras()
                    self.status_var.set("Verificando cache de bandeiras...")
                    threading.Thread(target=self._pre_carregar_todas_as_bandeiras_worker, args=(list(self.nomes_moedas.keys()),), daemon=True).start()
                elif tipo_msg == "bandeira_individual_pronta":
                    self.bandeiras_carregadas_contador += 1
                    self.status_var.set(f"Carregando bandeiras... ({self.bandeiras_carregadas_contador}/{self.total_bandeiras})")
                    self.atualizar_estrelas_e_bandeiras()
                elif tipo_msg == "todas_bandeiras_carregadas":
                    self.status_var.set("Pronto!")
                    self.atualizar_estrelas_e_bandeiras()
                    self.root.after(500, lambda: self.status_var.set(""))
                elif tipo_msg == "conversao_concluida":
                    self.label_resultado_origem.config(text=dados["origem_str"])
                    self.label_resultado_meio.config(text="equivale a")
                    self.label_resultado_destino.config(text=dados["destino_str"])
                    self.converter_button.config(state="normal")
                    self.grafico_button.config(state="normal")
                    self.copiar_button.config(state="normal")
                elif tipo_msg == "historico_carregado":
                    datas, valores = dados
                    base, destino = self.ultimo_par_convertido
                    self.desenhar_grafico(datas, valores, base, destino)
                    self.status_var.set("Pronto!")
                    self.root.after(500, lambda: self.status_var.set(""))
                    self.grafico_button.config(state="normal")
                elif tipo_msg == "erro_historico":
                    messagebox.showerror("Erro de Histórico", dados)
                    self.status_var.set("Pronto!")
                    self.root.after(500, lambda: self.status_var.set(""))
                    self.grafico_button.config(state="normal")
                elif tipo_msg == "erro":
                    messagebox.showerror("Erro", dados)
                    if "conversão" in dados or "taxa" in dados.lower():
                        self.converter_button.config(state="normal")
                        self.label_resultado_destino.config(text="")
                        self.grafico_button.config(state="disabled")
                        self.ultimo_par_convertido = None
        finally:
            self.root.after(100, self.processar_fila)
    def carregar_favoritos(self):
        if os.path.exists(self.FAVORITOS_FILE):
            try:
                with open(self.FAVORITOS_FILE, 'r') as f:
                    self.favoritos = set(json.load(f))
            except (json.JSONDecodeError, IOError): self.favoritos = set()
        else: self.favoritos = set()
    def salvar_favoritos(self):
        with open(self.FAVORITOS_FILE, 'w') as f:
            json.dump(list(self.favoritos), f)
    def copiar_resultado(self):
        resultado_texto = self.label_resultado_destino.cget("text")
        if resultado_texto and "Convertendo" not in resultado_texto:
            try:
                numero_a_copiar = resultado_texto.split(" ")[0]
                self.root.clipboard_clear()
                self.root.clipboard_append(numero_a_copiar)
                self.copiar_button.config(text="Copiado!")
                self.root.after(1500, lambda: self.copiar_button.config(text="Copiar 📋"))
            except: pass
    def alternar_tema(self):
        if self.tema_atual == "dark":
            sv_ttk.set_theme("light")
            self.tema_atual = "light"
        else:
            sv_ttk.set_theme("dark")
            self.tema_atual = "dark"
    def desenhar_grafico(self, datas, valores, base, destino):
        grafico_janela = tk.Toplevel(self.root)
        grafico_janela.title(f"Histórico de {base} para {destino}")
        grafico_janela.geometry("800x600")
        grafico_janela.transient(self.root)
        grafico_janela.grab_set()
        cor_fundo = "#FAFAFA" if self.tema_atual == "light" else "#2B2B2B"
        cor_texto = "black" if self.tema_atual == "light" else "white"
        fig = Figure(figsize=(8, 6), dpi=100, facecolor=cor_fundo)
        ax = fig.add_subplot(111, facecolor=cor_fundo)
        ax.plot(datas, valores, color=self.COR_DESTAQUE, linewidth=2)
        ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('gray'); ax.spines['bottom'].set_color('gray')
        ax.tick_params(axis='x', colors=cor_texto); ax.tick_params(axis='y', colors=cor_texto)
        ax.grid(True, linestyle='--', alpha=0.3)
        ax.set_title(f"Cotação de {base} para {destino} (Últimos 30 dias)", color=cor_texto, fontsize=16, pad=20)
        ax.set_ylabel(f"Valor de 1 {base} em {destino}", color=cor_texto)
        fig.autofmt_xdate(rotation=45, ha='right'); fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=grafico_janela)
        canvas.draw()
        toolbar_frame = ttk.Frame(grafico_janela)
        toolbar_frame.pack(side=tk.BOTTOM, fill=tk.X)
        toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
        toolbar.update()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        self.centralizar_janela(grafico_janela)
    def mostrar_creditos(self):
        creditos_janela = tk.Toplevel(self.root)
        creditos_janela.title("Sobre")
        creditos_janela.geometry("400x300"); creditos_janela.resizable(False, False)
        creditos_janela.transient(self.root); creditos_janela.grab_set()
        if self.FOTO_CRIADOR:
            foto_label = ttk.Label(creditos_janela, image=self.FOTO_CRIADOR)
            foto_label.pack(pady=(15, 0))
        ttk.Label(creditos_janela, text="Desenvolvido por:", font=self.FONT_LABEL).pack(pady=(10, 5))
        ttk.Label(creditos_janela, text="Matheus Zaino Pinto Oliveira", font=self.FONT_TITULO_CREDITOS).pack()
        ttk.Label(creditos_janela, text="Técnico de informática pelo IFCE", font=self.FONT_LABEL).pack()
        links_frame = ttk.Frame(creditos_janela)
        links_frame.pack(pady=15)
        def criar_link(parent, texto, url):
            link = ttk.Label(parent, text=texto, foreground=self.COR_DESTAQUE, cursor="hand2", font=self.FONT_LABEL)
            link.pack(pady=3)
            link.bind("<Button-1>", lambda e: webbrowser.open_new(url))
        criar_link(links_frame, "GitHub: github.com/Zaiknown", "https://github.com/Zaiknown")
        criar_link(links_frame, "Instagram: @zaiknown.py", "https://instagram.com/zaiknown.py")
        criar_link(links_frame, "LinkedIn: https://www.linkedin.com/in/matheus-zaino-94947234b/")
        self.centralizar_janela(creditos_janela)
    def criar_foto_circular(self, caminho_imagem, tamanho):
        try:
            img = Image.open(caminho_imagem).convert("RGBA")
            img = img.resize((tamanho, tamanho), Image.Resampling.LANCZOS)
            mascara = Image.new('L', (tamanho, tamanho), 0)
            draw = ImageDraw.Draw(mascara)
            draw.ellipse((0, 0, tamanho, tamanho), fill=255)
            img.putalpha(mascara)
            return ImageTk.PhotoImage(img)
        except FileNotFoundError: return None
    def validar_entrada_numerica(self, valor_potencial):
        if valor_potencial == "": return True
        for char in valor_potencial:
            if not (char.isdigit() or char in ".,"): return False
        if valor_potencial.count('.') > 1 or valor_potencial.count(',') > 1: return False
        if valor_potencial.count('.') == 1 and valor_potencial.count(',') == 1: return False
        return True
    def centralizar_janela(self, janela_alvo):
        janela_alvo.update_idletasks()
        largura, altura = janela_alvo.winfo_width(), janela_alvo.winfo_height()
        largura_tela, altura_tela = janela_alvo.winfo_screenwidth(), janela_alvo.winfo_screenheight()
        x, y = (largura_tela // 2) - (largura // 2), (altura_tela // 2) - (altura // 2)
        janela_alvo.geometry(f'{largura}x{altura}+{x}+{y}')
    def toggle_fullscreen(self, event=None):
        self.root.attributes('-fullscreen', not self.root.attributes('-fullscreen'))
    def sair_fullscreen(self, event=None):
        self.root.attributes('-fullscreen', False)
    def mostrar_grafico(self):
        if not self.ultimo_par_convertido: return
        base, destino = self.ultimo_par_convertido
        self.status_var.set(f"Buscando histórico de {base}/{destino}...")
        self.grafico_button.config(state="disabled")
        threading.Thread(target=self._obter_historico_worker, args=(base, destino), daemon=True).start()
    def start(self):
        self.root.mainloop()