#include <stdio.h>
#include <string.h>
#include <stdlib.h> 

// --- 1. DEFINIÇÃO DAS ESTRUTURAS ---
// (Idênticas à versão 3)

typedef struct {
    long ra; 
    char nome[100];
    char cpf[15];
    char telefone[20];
} Aluno;

typedef struct {
    int id;
    char nome[100];
} Turma;

typedef struct {
    int id;
    char nome[100];
} Materia;

typedef struct {
    long ra_aluno;
    int id_turma;
    int id_materia;
    float np1;
    float np2;
    float pim;
    int faltas;
    float media_final;
    char status[20];
} Matricula;

typedef struct {
    int id_turma;
    int id_materia;
} TurmaMateria;


// --- 2. NOMES DOS ARQUIVOS DE DADOS ---
// (Idênticos à versão 3)
const char* ALUNOS_DB = "alunos.dat";
const char* TURMAS_DB = "turmas.dat";
const char* MATERIAS_DB = "materias.dat";
const char* MATRICULAS_DB = "matriculas.dat";
const char* GRADE_DB = "grade.dat"; 


// --- 3. FUNÇÕES DE ALUNOS ---

void salvarAluno(Aluno aluno) {
    FILE *f = fopen(ALUNOS_DB, "ab");
    if (f == NULL) return;
    fwrite(&aluno, sizeof(Aluno), 1, f);
    fclose(f);
}

int carregarAlunos(Aluno* buffer, int max_alunos) {
    FILE *f = fopen(ALUNOS_DB, "rb");
    if (f == NULL) return 0;
    int count = 0;
    while(count < max_alunos && fread(&buffer[count], sizeof(Aluno), 1, f)) {
        count++;
    }
    fclose(f);
    return count;
}

int buscarAlunoPorRA(long ra_buscado, Aluno* out_aluno) {
    FILE *f = fopen(ALUNOS_DB, "rb");
    if (f == NULL) return 0;
    Aluno aluno_lido;
    while(fread(&aluno_lido, sizeof(Aluno), 1, f)) {
        if (aluno_lido.ra == ra_buscado) {
            *out_aluno = aluno_lido; 
            fclose(f);
            return 1; 
        }
    }
    fclose(f);
    return 0; 
}

// --- NOVO: Função para buscar por CPF ---
// Retorna 1 se achou, 0 se não
int buscarAlunoPorCPF(char* cpf_buscado, Aluno* out_aluno) {
    FILE *f = fopen(ALUNOS_DB, "rb");
    if (f == NULL) return 0;

    Aluno aluno_lido;
    while(fread(&aluno_lido, sizeof(Aluno), 1, f)) {
        // Usa strcmp (comparação de strings)
        if (strcmp(aluno_lido.cpf, cpf_buscado) == 0) {
            *out_aluno = aluno_lido; // Copia os dados
            fclose(f);
            return 1; // Encontrado
        }
    }
    fclose(f);
    return 0; // Não encontrado
}


// --- 4. FUNÇÕES DE TURMAS (Sem mudanças) ---
void salvarTurma(Turma turma) {
    FILE *f = fopen(TURMAS_DB, "ab");
    if (f == NULL) return;
    fwrite(&turma, sizeof(Turma), 1, f);
    fclose(f);
}
int carregarTurmas(Turma* buffer, int max_turmas) {
    FILE *f = fopen(TURMAS_DB, "rb");
    if (f == NULL) return 0;
    int count = 0;
    while(count < max_turmas && fread(&buffer[count], sizeof(Turma), 1, f)) {
        count++;
    }
    fclose(f);
    return count;
}

// --- 5. FUNÇÕES DE MATÉRIAS (Sem mudanças) ---
void salvarMateria(Materia materia) {
    FILE *f = fopen(MATERIAS_DB, "ab");
    if (f == NULL) return;
    fwrite(&materia, sizeof(Materia), 1, f);
    fclose(f);
}
int carregarMaterias(Materia* buffer, int max_materias) {
    FILE *f = fopen(MATERIAS_DB, "rb");
    if (f == NULL) return 0;
    int count = 0;
    while(count < max_materias && fread(&buffer[count], sizeof(Materia), 1, f)) {
        count++;
    }
    fclose(f);
    return count;
}

// --- 6. FUNÇÕES DE MATRÍCULA (NOTAS) (Sem mudanças) ---
void salvarMatricula(Matricula matricula) {
    FILE *f = fopen(MATRICULAS_DB, "ab");
    if (f == NULL) return;
    fwrite(&matricula, sizeof(Matricula), 1, f);
    fclose(f);
}
int carregarMatriculas(Matricula* buffer, int max_matriculas) {
    FILE *f = fopen(MATRICULAS_DB, "rb");
    if (f == NULL) return 0;
    int count = 0;
    while(count < max_matriculas && fread(&buffer[count], sizeof(Matricula), 1, f)) {
        count++;
    }
    fclose(f);
    return count;
}
void atualizarMatricula(Matricula matricula_atualizada) {
    FILE *f_in = fopen(MATRICULAS_DB, "rb");
    FILE *f_out = fopen("temp.dat", "wb"); 
    if (f_in == NULL || f_out == NULL) return;
    Matricula matricula_lida;
    int encontrado = 0;
    while(fread(&matricula_lida, sizeof(Matricula), 1, f_in)) {
        if (matricula_lida.ra_aluno == matricula_atualizada.ra_aluno &&
            matricula_lida.id_turma == matricula_atualizada.id_turma &&
            matricula_lida.id_materia == matricula_atualizada.id_materia) {
            fwrite(&matricula_atualizada, sizeof(Matricula), 1, f_out);
            encontrado = 1;
        } else {
            fwrite(&matricula_lida, sizeof(Matricula), 1, f_out);
        }
    }
    if (!encontrado) {
        fwrite(&matricula_atualizada, sizeof(Matricula), 1, f_out);
    }
    fclose(f_in);
    fclose(f_out);
    remove(MATRICULAS_DB);
    rename("temp.dat", MATRICULAS_DB);
}

// --- 7. FUNÇÕES DE GRADE (TURMA-MATÉRIA) (Sem mudanças) ---
void salvarTurmaMateria(TurmaMateria tm) {
    FILE *f = fopen(GRADE_DB, "ab");
    if (f == NULL) return;
    fwrite(&tm, sizeof(TurmaMateria), 1, f);
    fclose(f);
}
int carregarTurmaMateria(TurmaMateria* buffer, int max_registros) {
    FILE *f = fopen(GRADE_DB, "rb");
    if (f == NULL) return 0;
    int count = 0;
    while(count < max_registros && fread(&buffer[count], sizeof(TurmaMateria), 1, f)) {
        count++;
    }
    fclose(f);
    return count;
}