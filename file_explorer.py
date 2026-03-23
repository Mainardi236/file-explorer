import os
import shutil
import platform
from datetime import datetime
import subprocess
import sys

# --- Funções Auxiliares ---

def formatar_tamanho(bytes_num):
    """Converte o número de bytes para um formato legível (KB, MB, GB, etc.)."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
        if bytes_num < 1024.0:
            return f"{bytes_num:3.1f} {unit}"
        bytes_num /= 1024.0
    return f"{bytes_num:3.1f} EB"

def listar_discos():
    """
    Lista os discos disponíveis no sistema e retorna um dicionário de caminhos.
    Adapta-se a Windows e sistemas tipo Unix (Linux/macOS).
    """
    discos = {}
    
    # Lógica para Windows: Tenta as letras de C: a Z:
    if platform.system() == "Windows":
        import win32api
        drives = win32api.GetLogicalDriveStrings()
        drives = drives.split('\000')[:-1]
        
        print("\n--- Discos e Drives Disponíveis ---")
        for i, drive in enumerate(drives, 1):
            try:
                # Remove a barra invertida final para caminhos de drive root
                caminho = drive.replace("\\", "")
                total, used, free = shutil.disk_usage(caminho)
                
                discos[str(i)] = caminho
                print(f"[{i}] {caminho} - Tamanho Total: {formatar_tamanho(total)}")
            except FileNotFoundError:
                # Ignora drives que estão listados mas não montados (ex: leitor de cartão vazio)
                continue
            except Exception as e:
                # Ignora outros erros, como permissão
                # print(f"Erro ao acessar {caminho}: {e}")
                continue
    
    # Lógica para Linux/macOS: Começa na raiz '/'
    else:
        raiz = "/"
        print("\n--- Sistema de Arquivos ---")
        try:
            total, used, free = shutil.disk_usage(raiz)
            discos['1'] = raiz
            print(f"[1] {raiz} (Raiz do Sistema) - Tamanho Total: {formatar_tamanho(total)}")
        except Exception:
            # Em sistemas Unix, a raiz sempre deve estar acessível, mas trata o erro por segurança
            print("Não foi possível acessar a raiz do sistema.")

    return discos

def listar_conteudo(caminho):
    """Lista o conteúdo (arquivos e pastas) de um dado caminho."""
    try:
        # Usa os.scandir para eficiência
        entradas = list(os.scandir(caminho))
    except PermissionError:
        print("\n!!! Erro: Permissão negada para acessar esta pasta. !!!")
        return None
    except FileNotFoundError:
        print("\n!!! Erro: O caminho especificado não existe. !!!")
        return None
    except Exception as e:
        print(f"\n!!! Ocorreu um erro ao listar o conteúdo: {e} !!!")
        return None

    # Separa pastas e arquivos para listagem
    pastas = []
    arquivos = []
    
    for entrada in entradas:
        if entrada.is_dir():
            pastas.append(entrada)
        elif entrada.is_file():
            arquivos.append(entrada)
            
    # Combina listas: Pastas primeiro, depois arquivos
    conteudo = pastas + arquivos
    
    print(f"\n--- Conteúdo de: {caminho} ---")

    print(f"| {'OP':<2} | {'Tipo':<6} | {'Tamanho':<10} | {'Última Modificação':<20} | {'Nome':<40}")
    print("-" * 85)
    
    entradas_mapa = {}
    indice = 1
    
    for entrada in conteudo:
        try:
            stats = entrada.stat()
            mod_time = datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            
            if entrada.is_dir():
                # Para pastas, apenas mostra <DIR> e não calcula o tamanho recursivo
                # para evitar que a listagem demore muito.
                tamanho_str = "<DIR>"
                tipo = "Pasta"
            else:
                # Para arquivos, mostra o tamanho formatado
                tamanho_str = formatar_tamanho(stats.st_size)
                tipo = "Arquivo"

            entradas_mapa[str(indice)] = entrada.path
            print(f"| {indice:<2} | {tipo:<6} | {tamanho_str:<10} | {mod_time:<20} | {entrada.name:<40}")
            indice += 1
            
        except Exception as e:
            # Em caso de erro em uma entrada específica (ex: link quebrado), apenas a ignora.
            # print(f"Erro ao processar {entrada.name}: {e}")
            continue

    return entradas_mapa

def abrir_arquivo(caminho):
    """Tenta abrir um arquivo com o programa padrão do sistema."""
    try:
        if platform.system() == "Windows":
            # Abre usando a shell padrão do Windows
            os.startfile(caminho)
        elif platform.system() == "Darwin":
            # Comando 'open' no macOS
            subprocess.call(('open', caminho))
        else:
            # Comando 'xdg-open' na maioria dos Linux desktops
            subprocess.call(('xdg-open', caminho))
        print(f"\n>> Tentando abrir arquivo: {os.path.basename(caminho)} <<")
    except Exception as e:
        print(f"\n!!! Erro ao tentar abrir o arquivo: {e} !!!")

# --- Função Principal do Explorador ---

def explorador_de_arquivos_master():
    """Lógica principal de navegação do explorador."""
    historico_caminhos = []  # Pilha para rastrear a navegação
    caminho_atual = None

    while True:
        if caminho_atual is None:
            # 1. Etapa: Listar Discos
            discos = listar_discos()
            if not discos:
                print("\n!!! Não foi possível encontrar nenhum disco acessível. Encerrando. !!!")
                break
                
            print("-" * 85)
            print("Ações Especiais: [sair] para encerrar.")
            
            escolha = input("Escolha o número do disco para acessar ou [sair]: ").lower()

            if escolha == 'sair':
                print("Encerrando o gerenciador de arquivos. Até mais!")
                break
            
            if escolha in discos:
                caminho_atual = discos[escolha]
                historico_caminhos.append(caminho_atual)
            else:
                print("\nOpção inválida. Tente novamente.")
                continue

        else:
            # 2. Etapa: Listar Conteúdo da Pasta Atual
            mapa_conteudo = listar_conteudo(caminho_atual)
            
            if mapa_conteudo is None:
                # Se falhou ao listar (ex: Permissão), volta um nível
                if historico_caminhos:
                    historico_caminhos.pop()
                    caminho_atual = historico_caminhos[-1] if historico_caminhos else None
                continue

            print("-" * 85)
            print("Ações Especiais: [sair] para encerrar | [voltar] para a pasta anterior.")
            escolha = input("Escolha o número da entrada, [voltar] ou [sair]: ").lower()

            if escolha == 'sair':
                print("Encerrando o gerenciador de arquivos. Até mais!")
                break
            
            if escolha == 'voltar':
                if len(historico_caminhos) > 1:
                    historico_caminhos.pop()  # Remove a pasta atual
                    caminho_atual = historico_caminhos[-1] # Volta para a pasta anterior
                    print(f"\n<< Voltando para: {caminho_atual} >>")
                else:
                    # Se está na raiz do disco, volta para a lista de discos
                    historico_caminhos.clear()
                    caminho_atual = None
                    print("\n<< Voltando para a lista de discos >>")
                continue

            if escolha in mapa_conteudo:
                caminho_selecionado = mapa_conteudo[escolha]
                
                if os.path.isdir(caminho_selecionado):
                    # Abrir Pasta: Atualiza o caminho e adiciona ao histórico
                    caminho_atual = caminho_selecionado
                    historico_caminhos.append(caminho_atual)
                    print(f"\n>> Entrando em: {os.path.basename(caminho_atual)} <<")
                
                elif os.path.isfile(caminho_selecionado):
                    # Abrir Arquivo: Chama a função para abrir e permanece na pasta atual
                    abrir_arquivo(caminho_selecionado)
                
                else:
                    print("\nEntrada inválida. Tente novamente.")
            else:
                print("\nOpção inválida. Tente novamente.")

# --- Execução ---

if __name__ == "__main__":
    # Verifica se o módulo win32api está disponível no Windows para listagem de discos
    if platform.system() == "Windows":
        try:
            import win32api
        except ImportError:
            print("--------------------------------------------------------------------------------")
            print("Aviso: Você está no Windows, mas a biblioteca 'pywin32' não foi encontrada.")
            print("A listagem de discos pode não funcionar corretamente.")
            print("Instale com 'pip install pywin32' e tente novamente.")
            print("--------------------------------------------------------------------------------")
            # Se não estiver instalado, o script ainda tentará listar o conteúdo
            # apenas começando pelo caminho atual, mas a listagem de discos será limitada.

    explorador_de_arquivos_master()