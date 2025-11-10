import tkinter as tk
from tkinter import ttk, messagebox
import ctypes
import os
import random
import time
from collections import defaultdict

# --- 1. A Ponte (ctypes) - 5 estruturas ---

class Aluno(ctypes.Structure):
    _fields_ = [
        ("ra", ctypes.c_long),
        ("nome", ctypes.c_char * 100),
        ("cpf", ctypes.c_char * 15),
        ("telefone", ctypes.c_char * 20)
    ]
class Turma(ctypes.Structure): _fields_ = [("id", ctypes.c_int), ("nome", ctypes.c_char * 100)]
class Materia(ctypes.Structure): _fields_ = [("id", ctypes.c_int), ("nome", ctypes.c_char * 100)]
class Matricula(ctypes.Structure):
    _fields_ = [
        ("ra_aluno", ctypes.c_long),
        ("id_turma", ctypes.c_int),
        ("id_materia", ctypes.c_int),
        ("np1", ctypes.c_float), ("np2", ctypes.c_float), ("pim", ctypes.c_float),
        ("faltas", ctypes.c_int),
        ("media_final", ctypes.c_float),
        ("status", ctypes.c_char * 20)
    ]
class TurmaMateria(ctypes.Structure): _fields_ = [("id_turma", ctypes.c_int), ("id_materia", ctypes.c_int)]

# --- Carrega a biblioteca C ---
lib_c_path = "./database.dll"
if not os.path.exists(lib_c_path):
    messagebox.showerror("Erro Crítico", f"Biblioteca C não encontrada em {lib_c_path}\nCompile o 'database.c' (nova versão) primeiro!")
    exit()
try:
    lib_c = ctypes.CDLL(lib_c_path)
except OSError as e:
    messagebox.showerror("Erro Crítico", f"Não foi possível carregar a DLL. {e}")
    exit()

# --- Define os tipos de argumentos e retorno (BOA PRÁTICA) ---

# Aluno
lib_c.salvarAluno.argtypes = [Aluno]
lib_c.carregarAlunos.argtypes = [ctypes.POINTER(Aluno), ctypes.c_int]
lib_c.carregarAlunos.restype = ctypes.c_int
lib_c.buscarAlunoPorRA.argtypes = [ctypes.c_long, ctypes.POINTER(Aluno)]
lib_c.buscarAlunoPorRA.restype = ctypes.c_int
# --- NOVO: Definição da busca por CPF ---
lib_c.buscarAlunoPorCPF.argtypes = [ctypes.c_char_p, ctypes.POINTER(Aluno)]
lib_c.buscarAlunoPorCPF.restype = ctypes.c_int

# Turma
lib_c.salvarTurma.argtypes = [Turma]
lib_c.carregarTurmas.argtypes = [ctypes.POINTER(Turma), ctypes.c_int]
lib_c.carregarTurmas.restype = ctypes.c_int

# Materia
lib_c.salvarMateria.argtypes = [Materia]
lib_c.carregarMaterias.argtypes = [ctypes.POINTER(Materia), ctypes.c_int]
lib_c.carregarMaterias.restype = ctypes.c_int

# Matricula
lib_c.salvarMatricula.argtypes = [Matricula]
lib_c.carregarMatriculas.argtypes = [ctypes.POINTER(Matricula), ctypes.c_int]
lib_c.carregarMatriculas.restype = ctypes.c_int
lib_c.atualizarMatricula.argtypes = [Matricula]

# Grade (TurmaMateria)
lib_c.salvarTurmaMateria.argtypes = [TurmaMateria]
lib_c.carregarTurmaMateria.argtypes = [ctypes.POINTER(TurmaMateria), ctypes.c_int]
lib_c.carregarTurmaMateria.restype = ctypes.c_int


# --- 2. A Lógica de Cálculo (Python) (Sem mudanças) ---
def calcular_status(np1, np2, pim, faltas):
    if faltas >= 15:
        media = 0.0
        status = "Reprovado (Faltas)"
        return media, status
    media = ((np1 * 4) + (np2 * 4) + (pim * 2)) / 10.0
    status = "Aprovado" if media >= 7.0 else "Exame"
    return media, status

# --- 3. A Aplicação Tkinter ---

class App(tk.Tk):
    
    MAX_REGISTROS = 256 
    
    def __init__(self):
        super().__init__()
        self.title("Sistema de Gestão Acadêmica (SGA)")
        self.geometry("900x700")
        
        # Caches de dados
        self.cache_alunos = {} 
        self.cache_turmas = {} 
        self.cache_materias = {} 
        self.cache_grade = defaultdict(list)
        
        self.ra_aluno_encontrado = None 
        self.matricula_selecionada = None 
        
        # --- Criação das Abas ---
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.tab_gestao = ttk.Frame(self.notebook)
        self.tab_alunos = ttk.Frame(self.notebook)
        self.tab_notas = ttk.Frame(self.notebook)
        # --- NOVO: Aba de Busca/Boletim ---
        self.tab_boletim = ttk.Frame(self.notebook)
        self.tab_exames = ttk.Frame(self.notebook)
        
        self.notebook.add(self.tab_gestao, text=" Gestão ")
        self.notebook.add(self.tab_alunos, text=" Alunos ")
        self.notebook.add(self.tab_notas, text=" Notas e Faltas ")
        self.notebook.add(self.tab_boletim, text=" Boletim Aluno ")
        self.notebook.add(self.tab_exames, text=" Alunos em Exame ")  # Nova aba

        # --- Popula cada Aba ---
        self.criar_aba_gestao()
        self.criar_aba_alunos()
        self.criar_aba_notas()
        self.criar_aba_boletim()
        self.criar_aba_exames()  # Nova aba

        
        self.carregar_dados_para_cache()
        self.atualizar_comboboxes_globais()

    # --- Funções de Carregamento de Dados ---
    
    def carregar_dados_para_cache(self):
        # Limpa caches
        self.cache_alunos.clear()
        self.cache_turmas.clear()
        self.cache_materias.clear()
        self.cache_grade.clear()

        # Carrega Alunos
        AlunoArray = Aluno * self.MAX_REGISTROS
        buffer_a = AlunoArray()
        num_alunos = lib_c.carregarAlunos(buffer_a, self.MAX_REGISTROS)
        for i in range(num_alunos):
            aluno = buffer_a[i]
            self.cache_alunos[aluno.ra] = aluno.nome.decode('utf-8')
            
        # Carrega Turmas
        TurmaArray = Turma * self.MAX_REGISTROS
        buffer_t = TurmaArray()
        num_turmas = lib_c.carregarTurmas(buffer_t, self.MAX_REGISTROS)
        for i in range(num_turmas):
            turma = buffer_t[i]
            self.cache_turmas[turma.id] = turma.nome.decode('utf-8')
            
        # Carrega Matérias
        MateriaArray = Materia * self.MAX_REGISTROS
        buffer_m = MateriaArray()
        num_materias = lib_c.carregarMaterias(buffer_m, self.MAX_REGISTROS)
        for i in range(num_materias):
            materia = buffer_m[i]
            self.cache_materias[materia.id] = materia.nome.decode('utf-8')
            
        # Carrega a Grade
        GradeArray = TurmaMateria * self.MAX_REGISTROS
        buffer_g = GradeArray()
        num_grade = lib_c.carregarTurmaMateria(buffer_g, self.MAX_REGISTROS)
        for i in range(num_grade):
            ligacao = buffer_g[i]
            if ligacao.id_materia not in self.cache_grade[ligacao.id_turma]:
                self.cache_grade[ligacao.id_turma].append(ligacao.id_materia)

        # Atualiza tabelas na Aba Gestão
        self.atualizar_tree_gestao(self.tree_turmas, self.cache_turmas)
        self.atualizar_tree_gestao(self.tree_materias, self.cache_materias)
        self.atualizar_tree_grade()
    
    def atualizar_comboboxes_globais(self):
        turma_list = [f"{nome} (ID: {id})" for id, nome in self.cache_turmas.items()]
        materia_list = [f"{nome} (ID: {id})" for id, nome in self.cache_materias.items()]
        
        # Aba Gestão (Grade)
        self.combo_grade_turma['values'] = turma_list
        self.combo_grade_materia['values'] = materia_list
        
        # Aba Alunos (Matricular)
        self.combo_turma_mat['values'] = turma_list
        
        # Aba Notas (Filtrar)
        self.combo_turma_notas['values'] = turma_list
        self.combo_materia_notas['values'] = [] # Sempre limpo, depende da turma

    def atualizar_tree_gestao(self, tree, cache_dados):
        for row in tree.get_children(): tree.delete(row)
        for id, nome in cache_dados.items():
            tree.insert("", "end", values=(id, nome))

    def _get_id_from_combo(self, combo_value):
        try:
            return int(combo_value.split("(ID: ")[1].replace(")", ""))
        except:
            return None

    # --- ABA 1: GESTÃO (Idêntica à Versão 3) ---
    def criar_aba_gestao(self):
        nb_gestao = ttk.Notebook(self.tab_gestao)
        nb_gestao.pack(fill="both", expand=True, padx=5, pady=5)
        
        tab_turmas = ttk.Frame(nb_gestao, padding=10)
        tab_materias = ttk.Frame(nb_gestao, padding=10)
        tab_grade = ttk.Frame(nb_gestao, padding=10)
        
        nb_gestao.add(tab_turmas, text="Turmas")
        nb_gestao.add(tab_materias, text="Matérias")
        nb_gestao.add(tab_grade, text="Grade Curricular (Ligar Matéria à Turma)")
        
        # --- Painel de Turmas ---
        frame_nova_turma = ttk.LabelFrame(tab_turmas, text="Nova Turma", padding=10)
        frame_nova_turma.pack(fill="x", side="top")
        ttk.Label(frame_nova_turma, text="Nome da Turma:").grid(row=0, column=0, padx=5, sticky="w")
        self.entry_turma_nome = ttk.Entry(frame_nova_turma, width=40)
        self.entry_turma_nome.grid(row=0, column=1, padx=5, sticky="ew")
        ttk.Button(frame_nova_turma, text="Salvar Turma", command=self.salvar_turma).grid(row=0, column=2, padx=10)
        frame_lista_turmas = ttk.LabelFrame(tab_turmas, text="Turmas Existentes", padding=10)
        frame_lista_turmas.pack(fill="both", expand=True, pady=10)
        self.tree_turmas = ttk.Treeview(frame_lista_turmas, columns=('id', 'nome'), show='headings')
        self.tree_turmas.heading('id', text='ID')
        self.tree_turmas.heading('nome', text='Nome')
        self.tree_turmas.pack(fill="both", expand=True)

        # --- Painel de Matérias ---
        frame_nova_materia = ttk.LabelFrame(tab_materias, text="Nova Matéria", padding=10)
        frame_nova_materia.pack(fill="x", side="top")
        ttk.Label(frame_nova_materia, text="Nome da Matéria:").grid(row=0, column=0, padx=5, sticky="w")
        self.entry_materia_nome = ttk.Entry(frame_nova_materia, width=40)
        self.entry_materia_nome.grid(row=0, column=1, padx=5, sticky="ew")
        ttk.Button(frame_nova_materia, text="Salvar Matéria", command=self.salvar_materia).grid(row=0, column=2, padx=10)
        frame_lista_materias = ttk.LabelFrame(tab_materias, text="Matérias Existentes", padding=10)
        frame_lista_materias.pack(fill="both", expand=True, pady=10)
        self.tree_materias = ttk.Treeview(frame_lista_materias, columns=('id', 'nome'), show='headings')
        self.tree_materias.heading('id', text='ID')
        self.tree_materias.heading('nome', text='Nome')
        self.tree_materias.pack(fill="both", expand=True)

        # --- Painel da Grade Curricular ---
        frame_ligar_grade = ttk.LabelFrame(tab_grade, text="Ligar Matéria à Turma", padding=10)
        frame_ligar_grade.pack(fill="x", side="top")
        ttk.Label(frame_ligar_grade, text="Turma:").grid(row=0, column=0, padx=5, sticky="w")
        self.combo_grade_turma = ttk.Combobox(frame_ligar_grade, width=35, state="readonly")
        self.combo_grade_turma.grid(row=0, column=1, padx=5, sticky="ew")
        ttk.Label(frame_ligar_grade, text="Matéria:").grid(row=1, column=0, padx=5, sticky="w")
        self.combo_grade_materia = ttk.Combobox(frame_ligar_grade, width=35, state="readonly")
        self.combo_grade_materia.grid(row=1, column=1, padx=5, sticky="ew")
        ttk.Button(frame_ligar_grade, text="Ligar Matéria à Turma", command=self.salvar_ligacao_grade).grid(row=2, column=0, columnspan=2, pady=10)
        frame_lista_grade = ttk.LabelFrame(tab_grade, text="Grade Atual", padding=10)
        frame_lista_grade.pack(fill="both", expand=True, pady=10)
        self.tree_grade = ttk.Treeview(frame_lista_grade, columns=('turma', 'materia'), show='headings')
        self.tree_grade.heading('turma', text='Turma')
        self.tree_grade.heading('materia', text='Matéria')
        self.tree_grade.pack(fill="both", expand=True)

    def gerar_id_unico(self): return int(time.time() * 1000) % 1000000

    def salvar_turma(self):
        nome = self.entry_turma_nome.get()
        if not nome: return messagebox.showwarning("Erro", "O nome da turma não pode estar vazio.")
        turma_c = Turma(id=self.gerar_id_unico(), nome=nome.encode('utf-8'))
        lib_c.salvarTurma(turma_c)
        messagebox.showinfo("Sucesso", f"Turma '{nome}' salva com ID: {turma_c.id}")
        self.entry_turma_nome.delete(0, 'end')
        self.carregar_dados_para_cache()
        self.atualizar_comboboxes_globais()

    def salvar_materia(self):
        nome = self.entry_materia_nome.get()
        if not nome: return messagebox.showwarning("Erro", "O nome da matéria não pode estar vazio.")
        materia_c = Materia(id=self.gerar_id_unico(), nome=nome.encode('utf-8'))
        lib_c.salvarMateria(materia_c)
        messagebox.showinfo("Sucesso", f"Matéria '{nome}' salva com ID: {materia_c.id}")
        self.entry_materia_nome.delete(0, 'end')
        self.carregar_dados_para_cache()
        self.atualizar_comboboxes_globais()

    def salvar_ligacao_grade(self):
        id_turma = self._get_id_from_combo(self.combo_grade_turma.get())
        id_materia = self._get_id_from_combo(self.combo_grade_materia.get())
        if not id_turma or not id_materia:
            return messagebox.showerror("Erro", "Selecione uma Turma e uma Matéria válidas.")
        if id_materia in self.cache_grade.get(id_turma, []):
            return messagebox.showwarning("Aviso", "Essa matéria já está ligada a essa turma.")
        tm_c = TurmaMateria(id_turma=id_turma, id_materia=id_materia)
        lib_c.salvarTurmaMateria(tm_c)
        nome_turma = self.cache_turmas.get(id_turma, "Turma")
        nome_materia = self.cache_materias.get(id_materia, "Matéria")
        messagebox.showinfo("Sucesso", f"Matéria '{nome_materia}' ligada à Turma '{nome_turma}'!")
        self.carregar_dados_para_cache()
        
    def atualizar_tree_grade(self):
        for row in self.tree_grade.get_children(): self.tree_grade.delete(row)
        for id_turma, lista_id_materias in self.cache_grade.items():
            nome_turma = self.cache_turmas.get(id_turma, f"ID {id_turma}")
            for id_materia in lista_id_materias:
                nome_materia = self.cache_materias.get(id_materia, f"ID {id_materia}")
                self.tree_grade.insert("", "end", values=(nome_turma, nome_materia))

    # --- ABA 2: ALUNOS (Cadastro e Matrícula na Turma) ---
    def criar_aba_alunos(self):
        nb_alunos = ttk.Notebook(self.tab_alunos)
        nb_alunos.pack(fill="both", expand=True, padx=5, pady=5)
        
        tab_novo_aluno = ttk.Frame(nb_alunos, padding=10)
        tab_buscar_matricular = ttk.Frame(nb_alunos, padding=10)
        
        nb_alunos.add(tab_novo_aluno, text="Novo Aluno")
        nb_alunos.add(tab_buscar_matricular, text="Buscar / Matricular Aluno")

        # --- Painel Novo Aluno ---
        frame_cadastro = ttk.LabelFrame(tab_novo_aluno, text="Cadastro de Novo Aluno", padding=10)
        frame_cadastro.pack(fill="x", expand=True, padx=10, pady=10)
        ttk.Label(frame_cadastro, text="Nome:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.entry_aluno_nome = ttk.Entry(frame_cadastro, width=40)
        self.entry_aluno_nome.grid(row=0, column=1, columnspan=3, sticky="ew", padx=5, pady=2)
        ttk.Label(frame_cadastro, text="CPF:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.entry_aluno_cpf = ttk.Entry(frame_cadastro, width=20)
        self.entry_aluno_cpf.grid(row=1, column=1, sticky="w", padx=5, pady=2)
        ttk.Label(frame_cadastro, text="Telefone:").grid(row=1, column=2, sticky="w", padx=5, pady=2)
        self.entry_aluno_tel = ttk.Entry(frame_cadastro, width=20)
        self.entry_aluno_tel.grid(row=1, column=3, sticky="w", padx=5, pady=2)
        ttk.Button(frame_cadastro, text="Cadastrar Aluno", command=self.salvar_aluno).grid(row=2, column=0, columnspan=4, pady=10)
        
        # --- Painel Buscar / Matricular ---
        frame_busca = ttk.LabelFrame(tab_buscar_matricular, text="Buscar Aluno por RA", padding=10)
        frame_busca.pack(fill="x", side="top", pady=5)
        ttk.Label(frame_busca, text="RA:").grid(row=0, column=0, padx=5, sticky="w")
        self.entry_busca_ra = ttk.Entry(frame_busca, width=20)
        self.entry_busca_ra.grid(row=0, column=1, padx=5, sticky="w")
        ttk.Button(frame_busca, text="Buscar", command=self.buscar_aluno_ra).grid(row=0, column=2, padx=10)
        self.label_busca_resultado = ttk.Label(frame_busca, text="Nenhum aluno buscado.", foreground="blue")
        self.label_busca_resultado.grid(row=1, column=0, columnspan=3, pady=5)
        
        # --- MUDANÇA (Request 1): Painel de Matrícula simplificado ---
        self.frame_matricular = ttk.LabelFrame(tab_buscar_matricular, text="Matricular Aluno na Turma", padding=10)
        self.frame_matricular.pack(fill="x", side="top", pady=10)

        ttk.Label(self.frame_matricular, text="Turma:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.combo_turma_mat = ttk.Combobox(self.frame_matricular, width=40, state="readonly")
        self.combo_turma_mat.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        
        # O Combobox de Matéria foi REMOVIDO
        
        self.btn_matricular = ttk.Button(self.frame_matricular, text="Matricular Aluno na Turma", 
                                         command=self.matricular_aluno_na_turma, state="disabled") # Novo comando
        self.btn_matricular.grid(row=2, column=0, columnspan=2, pady=10)

    def gerar_ra(self):
        return int(time.time() * 10 + random.randint(100, 999))

    def salvar_aluno(self):
        try:
            nome = self.entry_aluno_nome.get()
            cpf = self.entry_aluno_cpf.get()
            tel = self.entry_aluno_tel.get()
            if not nome or not cpf:
                return messagebox.showwarning("Erro", "Nome e CPF são obrigatórios.")
            
            aluno_c = Aluno(ra=self.gerar_ra(), nome=nome.encode('utf-8'), 
                            cpf=cpf.encode('utf-8'), telefone=tel.encode('utf-8'))
            lib_c.salvarAluno(aluno_c)
            messagebox.showinfo("Sucesso", f"Aluno {nome} salvo com o RA: {aluno_c.ra}")
            self.entry_aluno_nome.delete(0, 'end')
            self.entry_aluno_cpf.delete(0, 'end')
            self.entry_aluno_tel.delete(0, 'end')
            self.carregar_dados_para_cache()
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro: {e}")

    def buscar_aluno_ra(self):
        try: ra = int(self.entry_busca_ra.get())
        except ValueError: return messagebox.showerror("Erro", "RA inválido. Digite apenas números.")
            
        aluno_encontrado = Aluno()
        resultado = lib_c.buscarAlunoPorRA(ra, ctypes.byref(aluno_encontrado))
        
        if resultado == 1:
            nome = aluno_encontrado.nome.decode('utf-8')
            self.label_busca_resultado.config(text=f"Aluno Encontrado: {nome} (RA: {ra})", foreground="green")
            self.ra_aluno_encontrado = ra
            self.btn_matricular.config(state="normal") 
        else:
            self.label_busca_resultado.config(text=f"Aluno com RA {ra} não encontrado.", foreground="red")
            self.ra_aluno_encontrado = None
            self.btn_matricular.config(state="disabled") 

    # --- NOVO (Request 1): Lógica de Matrícula na Turma Inteira ---
    def matricular_aluno_na_turma(self):
        if self.ra_aluno_encontrado is None:
            return messagebox.showerror("Erro", "Nenhum aluno selecionado. Busque um RA primeiro.")

        id_turma = self._get_id_from_combo(self.combo_turma_mat.get())
        if not id_turma:
            return messagebox.showerror("Erro", "Selecione uma Turma válida.")
            
        # Pega a lista de matérias da grade
        lista_id_materias = self.cache_grade.get(id_turma, [])
        
        if not lista_id_materias:
            return messagebox.showwarning("Aviso", "Esta turma não possui matérias na Grade Curricular. "
                                          "Vá em Gestão -> Grade Curricular para adicioná-las.")
        
        # Loop para criar uma matrícula para CADA matéria da grade
        count = 0
        for id_materia in lista_id_materias:
            matricula_c = Matricula(
                ra_aluno=self.ra_aluno_encontrado,
                id_turma=id_turma,
                id_materia=id_materia,
                np1=0.0, np2=0.0, pim=0.0,
                faltas=0, media_final=0.0,
                status=b"Pendente"
            )
            lib_c.salvarMatricula(matricula_c)
            count += 1
        
        nome_aluno = self.cache_alunos.get(self.ra_aluno_encontrado, "Aluno")
        nome_turma = self.cache_turmas.get(id_turma, "Turma")
        messagebox.showinfo("Sucesso", f"{nome_aluno} matriculado em {count} matérias da turma {nome_turma}!")

    # --- ABA 3: NOTAS E FALTAS (Lógica de filtro atualizada) ---
    def criar_aba_notas(self):
        frame_filtros = ttk.LabelFrame(self.tab_notas, text="Filtros", padding=10)
        frame_filtros.pack(fill="x", side="top", pady=5)
        
        ttk.Label(frame_filtros, text="Turma:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.combo_turma_notas = ttk.Combobox(frame_filtros, width=35, state="readonly")
        self.combo_turma_notas.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        self.combo_turma_notas.bind("<<ComboboxSelected>>", self.on_turma_select_notas)
        
        ttk.Label(frame_filtros, text="Matéria:").grid(row=0, column=2, sticky="w", padx=5, pady=2)
        self.combo_materia_notas = ttk.Combobox(frame_filtros, width=35, state="readonly")
        self.combo_materia_notas.grid(row=0, column=3, sticky="ew", padx=5, pady=2)
        
        ttk.Button(frame_filtros, text="Carregar Alunos Matriculados", command=self.carregar_matriculas_para_tree).grid(row=1, column=0, columnspan=4, pady=10)

        main_frame_notas = ttk.Frame(self.tab_notas, padding=10)
        main_frame_notas.pack(fill="both", expand=True)

        frame_lista_notas = ttk.LabelFrame(main_frame_notas, text="Alunos Matriculados", padding=10)
        frame_lista_notas.pack(fill="both", expand=True, side="left", padx=5)
        
        cols = ('ra', 'nome', 'np1', 'np2', 'pim', 'faltas', 'media', 'status')
        self.tree_notas = ttk.Treeview(frame_lista_notas, columns=cols, show='headings')
        for col in cols:
            self.tree_notas.heading(col, text=col.capitalize())
            self.tree_notas.column(col, width=80)
        self.tree_notas.column('nome', width=150)
        self.tree_notas.pack(fill="both", expand=True)
        self.tree_notas.bind('<<TreeviewSelect>>', self.on_tree_notas_select)

        self.frame_edicao_notas = ttk.LabelFrame(main_frame_notas, text="Editar Notas/Faltas", padding=10)
        self.frame_edicao_notas.pack(fill="y", side="right", padx=5)
        
        self.label_aluno_selecionado = ttk.Label(self.frame_edicao_notas, text="Selecione um aluno na tabela", font=("Arial", 10, "bold"))
        self.label_aluno_selecionado.grid(row=0, column=0, columnspan=2, pady=10)
        
        ttk.Label(self.frame_edicao_notas, text="NP1:").grid(row=1, column=0, sticky="w", padx=5, pady=3)
        self.entry_edit_np1 = ttk.Entry(self.frame_edicao_notas, width=10, state="disabled")
        self.entry_edit_np1.grid(row=1, column=1, sticky="w", padx=5, pady=3)
        ttk.Label(self.frame_edicao_notas, text="NP2:").grid(row=2, column=0, sticky="w", padx=5, pady=3)
        self.entry_edit_np2 = ttk.Entry(self.frame_edicao_notas, width=10, state="disabled")
        self.entry_edit_np2.grid(row=2, column=1, sticky="w", padx=5, pady=3)
        ttk.Label(self.frame_edicao_notas, text="PIM:").grid(row=3, column=0, sticky="w", padx=5, pady=3)
        self.entry_edit_pim = ttk.Entry(self.frame_edicao_notas, width=10, state="disabled")
        self.entry_edit_pim.grid(row=3, column=1, sticky="w", padx=5, pady=3)
        ttk.Label(self.frame_edicao_notas, text="Faltas:").grid(row=4, column=0, sticky="w", padx=5, pady=3)
        self.entry_edit_faltas = ttk.Entry(self.frame_edicao_notas, width=10, state="disabled")
        self.entry_edit_faltas.grid(row=4, column=1, sticky="w", padx=5, pady=3)
        self.btn_salvar_notas = ttk.Button(self.frame_edicao_notas, text="Salvar Notas", command=self.salvar_notas_aluno, state="disabled")
        self.btn_salvar_notas.grid(row=5, column=0, columnspan=2, pady=10)

    # Evento de filtro para Notas (Atualiza matérias baseado na turma)
    def on_turma_select_notas(self, event=None):
        self.combo_materia_notas.set('') # Limpa seleção
        id_turma = self._get_id_from_combo(self.combo_turma_notas.get())
        if not id_turma: return self.combo_materia_notas.config(values=[])
            
        id_materias_filtradas = self.cache_grade.get(id_turma, [])
        lista_nomes_materias = []
        for id_mat in id_materias_filtradas:
            nome = self.cache_materias.get(id_mat, f"ID {id_mat}")
            lista_nomes_materias.append(f"{nome} (ID: {id_mat})")
            
        self.combo_materia_notas['values'] = lista_nomes_materias
        if lista_nomes_materias: self.combo_materia_notas.current(0)
        
    def carregar_matriculas_para_tree(self):
        for row in self.tree_notas.get_children(): self.tree_notas.delete(row)
        id_turma_filtro = self._get_id_from_combo(self.combo_turma_notas.get())
        id_materia_filtro = self._get_id_from_combo(self.combo_materia_notas.get())
        
        if not id_turma_filtro or not id_materia_filtro:
            return messagebox.showwarning("Filtro Incompleto", "Selecione uma Turma E uma Matéria.")

        MatriculaArray = Matricula * self.MAX_REGISTROS
        buffer_matriculas = MatriculaArray()
        num_matriculas = lib_c.carregarMatriculas(buffer_matriculas, self.MAX_REGISTROS)
        
        for i in range(num_matriculas):
            matricula = buffer_matriculas[i]
            if (matricula.id_turma == id_turma_filtro and matricula.id_materia == id_materia_filtro):
                ra, nome = matricula.ra_aluno, self.cache_alunos.get(matricula.ra_aluno, "...")
                self.tree_notas.insert("", "end", iid=ra, values=( 
                    ra, nome, f"{matricula.np1:.1f}", f"{matricula.np2:.1f}", f"{matricula.pim:.1f}",
                    matricula.faltas, f"{matricula.media_final:.2f}", matricula.status.decode('utf-8') ))
    
    def on_tree_notas_select(self, event):
        selected_items = self.tree_notas.selection()
        if not selected_items: return
        
        ra_selecionado = selected_items[0]
        dados_linha = self.tree_notas.item(ra_selecionado)['values']
        self.matricula_selecionada = { "ra": dados_linha[0], "nome": dados_linha[1] }
        
        self.label_aluno_selecionado.config(text=f"Editando: {dados_linha[1]}\nRA: {dados_linha[0]}")
        for entry, value in zip([self.entry_edit_np1, self.entry_edit_np2, self.entry_edit_pim, self.entry_edit_faltas], [dados_linha[2], dados_linha[3], dados_linha[4], dados_linha[5]]):
            entry.config(state="normal")
            entry.delete(0, 'end')
            entry.insert(0, value)
        self.btn_salvar_notas.config(state="normal")

    def salvar_notas_aluno(self):
        if not self.matricula_selecionada: return messagebox.showerror("Erro", "Nenhum aluno selecionado.")
        try:
            ra, np1, np2, pim, faltas = (
                self.matricula_selecionada['ra'], float(self.entry_edit_np1.get()), float(self.entry_edit_np2.get()),
                float(self.entry_edit_pim.get()), int(self.entry_edit_faltas.get()) )
            id_turma = self._get_id_from_combo(self.combo_turma_notas.get())
            id_materia = self._get_id_from_combo(self.combo_materia_notas.get())
            if not id_turma or not id_materia:
                return messagebox.showerror("Erro", "Filtros de turma/matéria perdidos.")

            media, status = calcular_status(np1, np2, pim, faltas)
            matricula_c = Matricula(
                ra_aluno=ra, id_turma=id_turma, id_materia=id_materia,
                np1=np1, np2=np2, pim=pim, faltas=faltas,
                media_final=media, status=status.encode('utf-8') )
            
            lib_c.atualizarMatricula(matricula_c)
            messagebox.showinfo("Sucesso", f"Notas de {self.matricula_selecionada['nome']} salvas!")
            
            self.matricula_selecionada = None
            for entry in [self.entry_edit_np1, self.entry_edit_np2, self.entry_edit_pim, self.entry_edit_faltas]:
                entry.delete(0, 'end'); entry.config(state="disabled")
            self.label_aluno_selecionado.config(text="Selecione um aluno na tabela")
            self.btn_salvar_notas.config(state="disabled")
            self.carregar_matriculas_para_tree() # Recarrega a tabela
        except ValueError: messagebox.showerror("Erro de Entrada", "Notas e faltas devem ser números válidos.")
        except Exception as e: messagebox.showerror("Erro", f"Ocorreu um erro: {e}")


    # --- NOVO (Request 2 e 3): ABA BOLETIM ALUNO ---
    def criar_aba_boletim(self):
        # Frame de Busca
        frame_busca = ttk.LabelFrame(self.tab_boletim, text="Busca de Aluno", padding=10)
        frame_busca.pack(fill="x", side="top", pady=5, padx=5)
        
        ttk.Label(frame_busca, text="RA ou CPF:").grid(row=0, column=0, padx=5, sticky="w")
        self.entry_boletim_busca = ttk.Entry(frame_busca, width=30)
        self.entry_boletim_busca.grid(row=0, column=1, padx=5, sticky="ew")
        
        ttk.Button(frame_busca, text="Buscar por RA", command=self.buscar_boletim_ra).grid(row=0, column=2, padx=5)
        ttk.Button(frame_busca, text="Buscar por CPF", command=self.buscar_boletim_cpf).grid(row=0, column=3, padx=5)
        
        # Frame de Dados Pessoais
        self.frame_boletim_dados = ttk.LabelFrame(self.tab_boletim, text="Dados Pessoais", padding=10)
        self.frame_boletim_dados.pack(fill="x", side="top", pady=5, padx=5)
        
        self.lbl_boletim_nome = ttk.Label(self.frame_boletim_dados, text="Nome: N/A")
        self.lbl_boletim_nome.grid(row=0, column=0, sticky="w", padx=5)
        self.lbl_boletim_ra = ttk.Label(self.frame_boletim_dados, text="RA: N/A")
        self.lbl_boletim_ra.grid(row=0, column=1, sticky="w", padx=20)
        self.lbl_boletim_cpf = ttk.Label(self.frame_boletim_dados, text="CPF: N/A")
        self.lbl_boletim_cpf.grid(row=1, column=0, sticky="w", padx=5)
        self.lbl_boletim_tel = ttk.Label(self.frame_boletim_dados, text="Telefone: N/A")
        self.lbl_boletim_tel.grid(row=1, column=1, sticky="w", padx=20)

        # Frame da Situação Acadêmica (Boletim)
        self.frame_boletim_situacao = ttk.LabelFrame(self.tab_boletim, text="Situação Acadêmica", padding=10)
        self.frame_boletim_situacao.pack(fill="both", expand=True, side="top", pady=5, padx=5)
        
        cols = ('turma', 'materia', 'np1', 'np2', 'pim', 'faltas', 'media', 'status')
        self.tree_boletim = ttk.Treeview(self.frame_boletim_situacao, columns=cols, show='headings')
        for col in cols:
            self.tree_boletim.heading(col, text=col.capitalize())
            self.tree_boletim.column(col, width=90)
        self.tree_boletim.column('turma', width=120)
        self.tree_boletim.column('materia', width=120)
        self.tree_boletim.pack(fill="both", expand=True)

    def buscar_boletim_ra(self):
        try: ra = int(self.entry_boletim_busca.get())
        except ValueError: return messagebox.showerror("Erro", "RA inválido. Digite apenas números.")
        
        aluno_encontrado = Aluno()
        resultado = lib_c.buscarAlunoPorRA(ra, ctypes.byref(aluno_encontrado))
        self.processar_busca_boletim(resultado, aluno_encontrado)

    def buscar_boletim_cpf(self):
        cpf = self.entry_boletim_busca.get()
        if not cpf: return messagebox.showerror("Erro", "Digite um CPF.")
            
        aluno_encontrado = Aluno()
        resultado = lib_c.buscarAlunoPorCPF(cpf.encode('utf-8'), ctypes.byref(aluno_encontrado))
        self.processar_busca_boletim(resultado, aluno_encontrado)

    def processar_busca_boletim(self, resultado, aluno_c):
        # Limpa os campos e a tabela
        self.lbl_boletim_nome.config(text="Nome: N/A")
        self.lbl_boletim_ra.config(text="RA: N/A")
        self.lbl_boletim_cpf.config(text="CPF: N/A")
        self.lbl_boletim_tel.config(text="Telefone: N/A")
        for row in self.tree_boletim.get_children(): self.tree_boletim.delete(row)

        if resultado == 0:
            messagebox.showinfo("Busca", "Aluno não encontrado.")
            return

        # 1. Preenche os dados pessoais
        self.lbl_boletim_nome.config(text=f"Nome: {aluno_c.nome.decode('utf-8')}")
        self.lbl_boletim_ra.config(text=f"RA: {aluno_c.ra}")
        self.lbl_boletim_cpf.config(text=f"CPF: {aluno_c.cpf.decode('utf-8')}")
        self.lbl_boletim_tel.config(text=f"Telefone: {aluno_c.telefone.decode('utf-8')}")

        # 2. Busca e preenche a situação acadêmica
        MatriculaArray = Matricula * self.MAX_REGISTROS
        buffer_matriculas = MatriculaArray()
        num_matriculas = lib_c.carregarMatriculas(buffer_matriculas, self.MAX_REGISTROS)
        
        encontrou_matricula = False
        for i in range(num_matriculas):
            matricula = buffer_matriculas[i]
            
            # Filtra apenas as matrículas deste aluno
            if matricula.ra_aluno == aluno_c.ra:
                encontrou_matricula = True
                # Busca os nomes nos caches
                nome_turma = self.cache_turmas.get(matricula.id_turma, f"ID {matricula.id_turma}")
                nome_materia = self.cache_materias.get(matricula.id_materia, f"ID {matricula.id_materia}")
                
                self.tree_boletim.insert("", "end", values=(
                    nome_turma,
                    nome_materia,
                    f"{matricula.np1:.1f}",
                    f"{matricula.np2:.1f}",
                    f"{matricula.pim:.1f}",
                    matricula.faltas,
                    f"{matricula.media_final:.2f}",
                    matricula.status.decode('utf-8')
                ))
        
        if not encontrou_matricula:
            self.tree_boletim.insert("", "end", values=("Aluno ainda não matriculado em turmas.", "", "", "", "", "", "", ""))

        # --- NOVO: ABA ALUNOS EM EXAME ---
    def criar_aba_exames(self):
        frame_top = ttk.LabelFrame(self.tab_exames, text="Filtrar por Turma (opcional)", padding=10)
        frame_top.pack(fill="x", side="top", pady=5, padx=5)

        ttk.Label(frame_top, text="Turma:").grid(row=0, column=0, padx=5, sticky="w")
        self.combo_exame_turma = ttk.Combobox(frame_top, width=40, state="readonly")
        self.combo_exame_turma.grid(row=0, column=1, padx=5)
        self.combo_exame_turma['values'] = [f"{nome} (ID: {id})" for id, nome in self.cache_turmas.items()]

        ttk.Button(frame_top, text="Carregar Alunos em Exame", command=self.carregar_exames).grid(row=0, column=2, padx=10)

        frame_lista = ttk.LabelFrame(self.tab_exames, text="Alunos com Status 'Exame'", padding=10)
        frame_lista.pack(fill="both", expand=True, pady=5, padx=5)

        cols = ('ra', 'nome', 'turma', 'materia', 'media', 'faltas', 'status')
        self.tree_exames = ttk.Treeview(frame_lista, columns=cols, show='headings')
        for col in cols:
            self.tree_exames.heading(col, text=col.capitalize())
            self.tree_exames.column(col, width=100)
        self.tree_exames.column('nome', width=150)
        self.tree_exames.column('turma', width=130)
        self.tree_exames.column('materia', width=130)
        self.tree_exames.pack(fill="both", expand=True)

    def carregar_exames(self):
        for row in self.tree_exames.get_children():
            self.tree_exames.delete(row)

        id_turma_filtro = self._get_id_from_combo(self.combo_exame_turma.get()) if self.combo_exame_turma.get() else None

        MatriculaArray = Matricula * self.MAX_REGISTROS
        buffer_matriculas = MatriculaArray()
        num_matriculas = lib_c.carregarMatriculas(buffer_matriculas, self.MAX_REGISTROS)

        count = 0
        for i in range(num_matriculas):
            m = buffer_matriculas[i]
            status = m.status.decode('utf-8')
            if status.lower() == "exame".lower() and (id_turma_filtro is None or m.id_turma == id_turma_filtro):
                nome_aluno = self.cache_alunos.get(m.ra_aluno, "Desconhecido")
                nome_turma = self.cache_turmas.get(m.id_turma, f"ID {m.id_turma}")
                nome_materia = self.cache_materias.get(m.id_materia, f"ID {m.id_materia}")
                self.tree_exames.insert("", "end", values=(
                    m.ra_aluno, nome_aluno, nome_turma, nome_materia,
                    f"{m.media_final:.2f}", m.faltas, status
                ))
                count += 1

        messagebox.showinfo("Resultado", f"Foram encontrados {count} alunos em exame.")


if __name__ == "__main__":
    app = App()
    app.mainloop()
