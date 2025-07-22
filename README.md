# Conversor de Moedas Elegante

![Python](https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge&logo=python&logoColor=white)
![Status](https://img.shields.io/badge/Status-Concluído-brightgreen?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-informational?style=for-the-badge)

Um conversor de moedas de desktop moderno e completo, construído com Python e Tkinter, com uma interface elegante e um conjunto robusto de funcionalidades profissionais.


### Sobre o Projeto

Este projeto nasceu como um simples script e evoluiu para uma aplicação de desktop completa e polida. O objetivo foi criar uma ferramenta funcional, bonita e com uma ótima experiência de usuário, aplicando conceitos avançados de desenvolvimento, como:
- **Programação Orientada a Objetos (OOP):** Para uma estrutura de código limpa e escalável.
- **Multithreading:** Para garantir que a interface nunca trave durante operações de rede.
- **Cache de Dados:** Para otimizar o carregamento de recursos e permitir uso offline.
- **Design de UI/UX:** Foco em uma interface intuitiva e esteticamente agradável.

---

### ✨ Principais Funcionalidades

- **Cotações em Tempo Real:** Utiliza a API do [Frankfurter.app](https://frankfurter.app) para obter as taxas de câmbio mais recentes.
- **Interface Moderna e Responsiva:** Tema escuro e claro, com layout que se adapta a diferentes tamanhos de tela.
- **Gráfico de Histórico:** Visualização interativa da variação da cotação nos últimos 30 dias, com zoom e pan (usando Matplotlib).
- **Cache Local de Bandeiras:** As bandeiras são baixadas uma vez e salvas localmente para carregamento instantâneo e uso offline.
- **Lista de Favoritos:** Marque moedas com uma estrela (⭐) para que elas apareçam sempre no topo da lista, com as preferências salvas entre sessões.
- **Conversão "Ao Vivo":** O resultado é atualizado automaticamente enquanto você digita, sem a necessidade de clicar em botões.
- **Recursos de Usabilidade:**
    - Botão para **inverter** as moedas de origem e destino com um clique.
    - Botão para **copiar** o valor do resultado para a área de transferência.
    - **Validação de entrada** para permitir apenas números no campo de valor.
- **Gerenciamento de Janela Completo:**
    - O aplicativo abre perfeitamente centralizado na tela.
    - Suporte para modo janela, maximizado e tela cheia (F11 / Esc).
- **Personalização:** Menu "Créditos" customizado com uma **foto do desenvolvedor** (o arquivo `foto.jpg`) e links clicáveis.

---

### 🛠️ Tecnologias Utilizadas

- **Python 3**
- **Tkinter:** Para a construção da interface gráfica.
- **Pillow (PIL):** Para manipulação e exibição de imagens (bandeiras e foto).
- **Requests:** Para fazer as chamadas à API de cotações.
- **sv-ttk:** Para aplicar os temas modernos à interface.
- **Matplotlib:** Para a criação e integração do gráfico de histórico de dados.

---

### 🚀 Como Executar o Projeto

1.  **Clone o repositório:**
    ```bash
    git clone [https://github.com/Zaiknown/zaiknown-s-currency-converter](https://github.com/Zaiknown/zaiknown-s-currency-converter)
    cd conversor_moedas
    ```

2.  **Crie e ative um ambiente virtual (recomendado):**
    ```bash
    python -m venv venv
    # No Windows
    venv\Scripts\activate
    # No macOS/Linux
    # source venv/bin/activate
    ```

3.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Execute o aplicativo:**
    ```bash
    python main.py
    ```
    *Observação: O aplicativo procurará por um arquivo `foto.jpg` na pasta para exibir na aba "Créditos". Se não encontrar, funcionará normalmente sem a imagem.*

---

### 📄 Licença

Este projeto está sob a licença MIT.

**Desenvolvido por Matheus Zaino Pinto Oliveira.**