# Memento

Este repositório contém o código-fonte do projeto **Memento**, desenvolvido como Trabalho de Conclusão de Curso (TCC) em Ciência da Computação pela Universidade Federal de Pelotas (UFPEL).

Memento é um sistema de estudos inteligente projetado para otimizar o aprendizado, que opera inteiramente via **terminal (CLI)**. A aplicação processa materiais de estudo (PDFs) e utiliza Modelos de Linguagem (LLMs) treinados especificamente para gerar perguntas, avaliar as respostas dos usuários e aplicar a técnica de **repetição espaçada** para reforçar a memorização.

## Funcionalidades Principais

* **Processamento de Conteúdo:** Utiliza a biblioteca `docling` para processar documentos PDF e extrair o texto para geração.
* **Geração de Perguntas e Respostas (QAG):** Utiliza o modelo [**graziele-fagundes/Sabia7B-QAG**](https://huggingface.co/graziele-fagundes/Sabia7B-QAG), treinado para gerar automaticamente *flashcards* (pares de pergunta e resposta) relevantes com base no conteúdo extraído.
* **Avaliação (Grading) Inteligente:** Emprega o modelo [**graziele-fagundes/BERTimbau-Grading**](https://huggingface.co/graziele-fagundes/BERTimbau-Grading) para analisar e pontuar semanticamente as respostas fornecidas pelo usuário, comparando-as com as respostas ideais.
* **Repetição Espaçada (Spaced Repetition):** Com base no desempenho do usuário, o sistema agenda a próxima revisão de cada flashcard em intervalos de tempo otimizados, maximizando a retenção.
* **Banco de Dados Local (SQLite):** Responsável pelo armazenamento persistente de usuários, flashcards e histórico de estudos.

## Como Executar o Projeto

Para executar o Memento localmente, siga estes passos:

1.  **Clone o repositório:**
    ```
    git clone https://github.com/graziele-fagundes/Memento.git
    cd Memento
    ```

2.  **Crie e ative um ambiente virtual:**
    ```
    # No Windows (PowerShell):
    python -m venv venv
    .\venv\Scripts\activate
    
    # No macOS/Linux:
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Instale as dependências:**
    ```
    pip install -r requirements.txt
    ```

4.  **Execute a aplicação:**
    O banco de dados `SQLite` será criado automaticamente no primeiro uso.
    ```
    python main.py
    ```
    A aplicação será iniciada no seu terminal. Siga as instruções na tela para se registrar ou fazer login.

## Autora
**Graziele Fagundes** - [github.com/graziele-fagundes](https://github.com/graziele-fagundes)
  
## Monografia
⏳ Monografia com todos os detalhes técnicos aqui em breve.
