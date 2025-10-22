# Memento

Este repositório contém o código-fonte do projeto **Memento**, desenvolvido como Trabalho de Conclusão de Curso (TCC) em Ciência da Computação pela Universidade Federal de Pelotas (UFPEL).

Memento é um sistema de estudos inteligente projetado para otimizar o aprendizado, que opera inteiramente via **terminal (CLI)**. A aplicação processa materiais de estudo (PDFs) e utiliza Modelos de Linguagem (LLMs) treinados especificamente para gerar perguntas, avaliar as respostas dos usuários e aplicar a técnica de **repetição espaçada** para reforçar a memorização.

## Funcionalidades Principais

* **Processamento de Conteúdo:** Utiliza a biblioteca `docling` para processar documentos PDF e extrair o texto para análise.
* **Geração de Perguntas e Respostas (QAG):** Utiliza um modelo de IA treinado (`graziele-fagundes/Sabia7B-QAG`) para gerar automaticamente "flashcards" (pares de pergunta e resposta) relevantes sobre o conteúdo.
* **Avaliação (Grading) Inteligente:** Quando o usuário responde a uma pergunta no terminal, o sistema usa um modelo de IA treinado (`graziele-fagundes/BERTimbau-Grading`) para avaliar a qualidade semântica da resposta.
* **Repetição Espaçada (Spaced Repetition):** Com base no desempenho do usuário, o sistema agenda a próxima revisão de cada flashcard em intervalos de tempo otimizados, maximizando a retenção.
* **Gerenciamento de Usuários:** Sistema de autenticação local (via terminal) com armazenamento seguro de senhas (utilizando hash) em um banco de dados local.

## Tecnologias e Modelos

O projeto foi construído em **Python**, com foco em processamento de linguagem natural e operação local.

* **Modelos de IA (Fine-tuned):**
    * **`graziele-fagundes/Sabia7B-QAG`**: Um modelo baseado no Sabiá-7B que foi treinado (fine-tuning) pela autora especificamente para a tarefa de Geração de Perguntas e Respostas (QAG) em português.
    * **`graziele-fagundes/BERTimbau-Grading`**: Um modelo baseado no BERTimbau que foi treinado (fine-tuning) pela autora para a tarefa de avaliação semântica de respostas (Grading).

* **Banco de Dados:**
    * **`SQLite`**: Utilizado para armazenar dados de usuários, flashcards e histórico de estudos localmente.

* **Processamento de Documentos:**
    * **`docling`**: Biblioteca utilizada para a extração de texto de arquivos PDF.

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
* **Graziele Fagundes** - [github.com/graziele-fagundes](https://github.com/graziele-fagundes)
  
## Monografia
⏳ Monografia com todos os detalhes técnicos aqui em breve.
