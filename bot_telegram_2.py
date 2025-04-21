# -*- coding: utf-8 -*-
"""
Bot de envio de sinais para canais do Telegram
Por: Trending Brasil
Versão: 3.0
"""

# Importar bibliotecas necessárias
import traceback
import socket
import pytz
from datetime import datetime, timedelta, time as dt_time
import json
import random
import time
import schedule
import requests
import logging
import sys
import os
from functools import lru_cache
import telebot
import threading
from datetime import time as datetime_time
import uuid
import copy

# Configuração do logger
BOT2_LOGGER = logging.getLogger("bot2")
BOT2_LOGGER.setLevel(logging.INFO)
bot2_formatter = logging.Formatter(
    "%(asctime)s - BOT2 - %(levelname)s - %(message)s")

# Evitar duplicação de handlers
if not BOT2_LOGGER.handlers:
    # Handler para arquivo (pode usar UTF-8)
    bot2_file_handler = logging.FileHandler("bot_telegram_bot2_logs.log", encoding='utf-8')
    bot2_file_handler.setFormatter(bot2_formatter)
    BOT2_LOGGER.addHandler(bot2_file_handler)

    # Handler para console (sem emojis para evitar problemas de codificação)
    class NoEmojiFormatter(logging.Formatter):
        """Formatter que remove emojis e outros caracteres Unicode incompatíveis com Windows console"""
        def format(self, record):
            # Primeiro obter a mensagem formatada normalmente
            msg = super().format(record)
            # Substitua emojis comuns por equivalentes ASCII
            emoji_map = {
                '🚀': '[ROCKET]',
                '🔧': '[CONFIG]',
                '✅': '[OK]',
                '❌': '[ERRO]',
                '⚠️': '[AVISO]',
                '🔄': '[RELOAD]',
                '📅': '[DATA]',
                '🔍': '[BUSCA]',
                '📊': '[STATS]',
                '📋': '[LISTA]',
                '🌐': '[GLOBAL]',
                '📣': '[ANUNCIO]',
                '🎬': '[VIDEO]',
                '⏱️': '[TEMPO]',
                '⏳': '[ESPERA]',
                '🟢': '[VERDE]',
                '🔒': '[LOCK]',
                '🔓': '[UNLOCK]',
                '📤': '[ENVIO]',
                '⚙️': '[ENGRENAGEM]',
                '🛑': '[PARAR]',
                '🆔': '[ID]',
            }
            
            for emoji, replacement in emoji_map.items():
                msg = msg.replace(emoji, replacement)
                
            return msg
    
    console_formatter = NoEmojiFormatter("%(asctime)s - BOT2 - %(levelname)s - %(message)s")
    bot2_console_handler = logging.StreamHandler()
    bot2_console_handler.setFormatter(console_formatter)
    BOT2_LOGGER.addHandler(bot2_console_handler)

# Credenciais Telegram
BOT2_TOKEN = "7997585882:AAFDyG-BYskj1gyAbh17X5jd6DDClXdluww"

# Inicialização do bot
bot2 = telebot.TeleBot(BOT2_TOKEN)

# Configuração dos canais para cada idioma
BOT2_CANAIS_CONFIG = {
    "pt": [-1002424874613],  # Canal para mensagens em português
    "en": [-1002453956387],  # Canal para mensagens em inglês
    "es": [-1002446547846]   # Canal para mensagens em espanhol
}

# Lista de IDs dos canais para facilitar iteração
BOT2_CHAT_IDS = []
for idioma, chats in BOT2_CANAIS_CONFIG.items():
    BOT2_CHAT_IDS.extend(chats)

# Links para cada idioma
LINKS_CORRETORA = {
    "pt": "https://trade.xxbroker.com/register?aff=741613&aff_model=revenue&afftrack=",
    "en": "https://trade.xxbroker.com/register?aff=741727&aff_model=revenue&afftrack=",
    "es": "https://trade.xxbroker.com/register?aff=741726&aff_model=revenue&afftrack="
}

# URLs dos vídeos para cada idioma
LINKS_VIDEO = {
    "pt": "https://t.me/trendingbrazil/215",
    "en": "https://t.me/trendingenglish/226",
    "es": "https://t.me/trendingespanish/212"
}

# URLs diretas para GIFs
URL_GIF_POS_SINAL = "https://media.giphy.com/media/eWbGux0IXOygZ7m2Of/giphy.gif"
URL_GIF_PROMO = "https://media.giphy.com/media/whPiIq21hxXuJn7WVX/giphy.gif"

# Variáveis de controle
contador_sinais = 0  # Para rastrear os sinais múltiplos de 3
sinais_enviados_hoje = []  # Lista para armazenar os sinais enviados hoje
ultimo_sinal = None  # Armazenar o último sinal enviado

# Função para obter a hora atual no fuso horário de Brasília
def obter_hora_brasilia():
    """Retorna a hora atual no fuso horário de Brasília."""
    fuso_horario_brasilia = pytz.timezone("America/Sao_Paulo")
    return datetime.now(fuso_horario_brasilia)

# Função para gerar um sinal aleatório
def gerar_sinal():
    """Gera um sinal aleatório com ativo e direção."""
    ativos = [
        "EUR/USD (OTC)",
        "Gold/Silver (OTC)",
        "BTC/USD (OTC)",
        "ETH/USD (OTC)",
        "AUD/JPY (OTC)",
        "EUR/JPY (OTC)",
        "Worldcoin (OTC)",
        "Pepe (OTC)",
        "1000Sats (OTC)",
        "US 500 (OTC)"
    ]
    
    direcoes = ["CALL", "PUT"]
    
    ativo = random.choice(ativos)
    direcao = random.choice(direcoes)
    
    return {
        "ativo": ativo,
        "direcao": direcao,
        "tempo_expiracao": 5,  # 5 minutos de expiração
        "hora_criacao": obter_hora_brasilia()
    }

# Função para formatar a mensagem de sinal
def formatar_mensagem_sinal(sinal, idioma):
    """Formata a mensagem de sinal para o idioma especificado."""
    ativo = sinal["ativo"]
    direcao = sinal["direcao"]
    tempo_expiracao = sinal["tempo_expiracao"]
    
    # Obter horário atual
    hora_atual = obter_hora_brasilia()
    
    # Horário de expiração (5 minutos depois)
    hora_expiracao = hora_atual + timedelta(minutes=tempo_expiracao)
    
    # Horários de gales
    hora_gale1 = hora_expiracao + timedelta(minutes=5)
    hora_gale2 = hora_gale1 + timedelta(minutes=5)
    hora_gale3 = hora_gale2 + timedelta(minutes=5)
    
    # Emoji baseado na direção
    emoji = "🟩" if direcao == "CALL" else "🟥"
    
    # Texto da direção para cada idioma
    if direcao == "CALL":
        action_pt = "COMPRA"
        action_en = "BUY"
        action_es = "COMPRA"
    else:
        action_pt = "VENDA"
        action_en = "SELL"
        action_es = "VENTA"
    
    # Formatação de horários
    hora_atual_str = hora_atual.strftime("%H:%M")
    hora_expiracao_str = hora_expiracao.strftime("%H:%M")
    hora_gale1_str = hora_gale1.strftime("%H:%M")
    hora_gale2_str = hora_gale2.strftime("%H:%M")
    hora_gale3_str = hora_gale3.strftime("%H:%M")
    
    # Obter links específicos para o idioma
    link_corretora = LINKS_CORRETORA[idioma]
    link_video = LINKS_VIDEO[idioma]
    
    # Mensagens por idioma
    if idioma == "pt":
        mensagem = (
            f"💰{tempo_expiracao} minutos de expiração\n"
            f"{ativo};{hora_atual_str};{action_pt} {emoji} Digital\n\n"
            f"🕐TEMPO PARA {hora_expiracao_str}\n\n"
            f"1º GALE — TEMPO PARA {hora_gale1_str}\n"
            f"2º GALE TEMPO PARA {hora_gale2_str}\n"
            f"3º GALE TEMPO PARA {hora_gale3_str}\n\n"
            f'📲 <a href="{link_corretora}">Clique para abrir a corretora</a>\n'
            f'🙋‍♂️ Não sabe operar ainda? <a href="{link_video}">Clique aqui</a>'
        )
    elif idioma == "en":
        mensagem = (
            f"💰{tempo_expiracao} minutes expiration\n"
            f"{ativo};{hora_atual_str};{action_en} {emoji} Digital\n\n"
            f"🕐TIME UNTIL {hora_expiracao_str}\n\n"
            f"1st GALE — TIME UNTIL {hora_gale1_str}\n"
            f"2nd GALE TIME UNTIL {hora_gale2_str}\n"
            f"3rd GALE TIME UNTIL {hora_gale3_str}\n\n"
            f'📲 <a href="{link_corretora}">Click to open broker</a>\n'
            f'🙋‍♂️ Don\'t know how to trade yet? <a href="{link_video}">Click here</a>'
        )
    else:  # espanhol
        mensagem = (
            f"💰{tempo_expiracao} minutos de expiración\n"
            f"{ativo};{hora_atual_str};{action_es} {emoji} Digital\n\n"
            f"🕐TIEMPO HASTA {hora_expiracao_str}\n\n"
            f"1º GALE — TIEMPO HASTA {hora_gale1_str}\n"
            f"2º GALE TIEMPO HASTA {hora_gale2_str}\n"
            f"3º GALE TIEMPO HASTA {hora_gale3_str}\n\n"
            f'📲 <a href="{link_corretora}">Haga clic para abrir el corredor</a>\n'
            f'🙋‍♂️ ¿No sabe operar todavía? <a href="{link_video}">Haga clic aquí</a>'
        )
        
    return mensagem

# Função para formatar a mensagem de participação (múltiplos de 3)
def formatar_mensagem_participacao(idioma):
    """Formata a mensagem de participação para os sinais múltiplos de 3."""
    link_corretora = LINKS_CORRETORA[idioma]
    link_video = LINKS_VIDEO[idioma]
    
    if idioma == "pt":
        mensagem = (
            "⚠⚠PARA PARTICIPAR DESTA SESSÃO, SIGA O PASSO A PASSO ABAIXO⚠⚠\n\n"
            "1º ✅ —>  Crie sua conta na corretora no link abaixo e GANHE $10.000 DE GRAÇA pra começar a operar com a gente sem ter que arriscar seu dinheiro.\n\n"
            "Você vai poder testar todos nossas\n"
            "operações com risco ZERO!\n\n"
            "👇🏻👇🏻👇🏻👇🏻\n\n"
            f'<a href="{link_corretora}">CRIE SUA CONTA AQUI E GANHE R$10.000</a>\n\n'
            "—————————————————————\n\n"
            "2º ✅ —>  Assista o vídeo abaixo e aprenda como depositar e como entrar com a gente nas nossas operações!\n\n"
            "👇🏻👇🏻👇🏻👇🏻\n\n"
            f'<a href="{link_video}">CLIQUE AQUI E ASSISTA O VÍDEO</a>'
        )
    elif idioma == "en":
        mensagem = (
            "⚠⚠TO PARTICIPATE IN THIS SESSION, FOLLOW THE STEPS BELOW⚠⚠\n\n"
            "1st ✅ —> Create your broker account at the link below and GET $10,000 FOR FREE to start trading with us without having to risk your money.\n\n"
            "You will be able to test all our\n"
            "operations with ZERO risk!\n\n"
            "👇🏻👇🏻👇🏻👇🏻\n\n"
            f'<a href="{link_corretora}">CREATE YOUR ACCOUNT HERE AND GET $10,000</a>\n\n'
            "—————————————————————\n\n"
            "2nd ✅ —> Watch the video below and learn how to deposit and how to enter with us in our operations!\n\n"
            "👇🏻👇🏻👇🏻👇🏻\n\n"
            f'<a href="{link_video}">CLICK HERE AND WATCH THE VIDEO</a>'
        )
    else:  # espanhol
        mensagem = (
            "⚠⚠PARA PARTICIPAR EN ESTA SESIÓN, SIGA LOS PASOS A CONTINUACIÓN⚠⚠\n\n"
            "1º ✅ —> Cree su cuenta de corredor en el enlace a continuación y OBTENGA $10,000 GRATIS para comenzar a operar con nosotros sin tener que arriesgar su dinero.\n\n"
            "Podrá probar todas nuestras\n"
            "operaciones con riesgo CERO!\n\n"
            "👇🏻👇🏻👇🏻👇🏻\n\n"
            f'<a href="{link_corretora}">CREE SU CUENTA AQUÍ Y OBTENGA $10,000</a>\n\n'
            "—————————————————————\n\n"
            "2º ✅ —> ¡Mire el video a continuación y aprenda cómo depositar y cómo ingresar con nosotros en nuestras operaciones!\n\n"
            "👇🏻👇🏻👇🏻👇🏻\n\n"
            f'<a href="{link_video}">HAGA CLIC AQUÍ Y MIRE EL VIDEO</a>'
        )
        
    return mensagem

# Função para formatar a mensagem de abertura da corretora
def formatar_mensagem_abertura_corretora(idioma):
    """Formata a mensagem de abertura da corretora para o idioma especificado."""
    link_corretora = LINKS_CORRETORA[idioma]
    
    if idioma == "pt":
        mensagem = (
            "👉🏼Abram a corretora Pessoal\n\n"
            "⚠FIQUEM ATENTOS⚠\n\n"
            "🔥Cadastre-se na XXBROKER agora mesmo🔥\n\n"
            f'➡ <a href="{link_corretora}">CLICANDO AQUI</a>'
        )
    elif idioma == "en":
        mensagem = (
            "👉🏼Open the broker now\n\n"
            "⚠STAY ALERT⚠\n\n"
            "🔥Register at XXBROKER right now🔥\n\n"
            f'➡ <a href="{link_corretora}">CLICK HERE</a>'
        )
    else:  # espanhol
        mensagem = (
            "👉🏼Abran el corredor ahora\n\n"
            "⚠ESTÉN ATENTOS⚠\n\n"
            "🔥Regístrese en XXBROKER ahora mismo🔥\n\n"
            f'➡ <a href="{link_corretora}">HACIENDO CLIC AQUÍ</a>'
        )
        
    return mensagem

# Função para enviar uma mensagem para todos os canais
def enviar_mensagem(mensagens_por_idioma, disable_preview=True):
    """
    Envia uma mensagem para todos os canais configurados.
    
    Args:
        mensagens_por_idioma: Dicionário com mensagens formatadas por idioma
        disable_preview: Se deve desabilitar a pré-visualização de links
    
    Returns:
        bool: True se o envio foi bem sucedido, False caso contrário
    """
    try:
        for idioma, canais in BOT2_CANAIS_CONFIG.items():
            mensagem = mensagens_por_idioma.get(idioma)
            if not mensagem:
                BOT2_LOGGER.warning(f"Mensagem não disponível para o idioma {idioma}")
                continue
                
            for chat_id in canais:
                try:
                    bot2.send_message(
                        chat_id=chat_id,
                        text=mensagem,
                        parse_mode="HTML",
                        disable_web_page_preview=disable_preview
                    )
                    BOT2_LOGGER.info(f"Mensagem enviada com sucesso para o canal {chat_id} ({idioma})")
                except Exception as e:
                    BOT2_LOGGER.error(f"Erro ao enviar mensagem para o canal {chat_id}: {str(e)}")
        return True
    except Exception as e:
        BOT2_LOGGER.error(f"Erro ao enviar mensagens: {str(e)}")
        BOT2_LOGGER.error(traceback.format_exc())
        return False

# Função para enviar um GIF para todos os canais
def enviar_gif(url_gif):
    """
    Envia um GIF para todos os canais configurados.
    
    Args:
        url_gif: URL do GIF a ser enviado
        
    Returns:
        bool: True se o envio foi bem sucedido, False caso contrário
    """
    try:
        for idioma, canais in BOT2_CANAIS_CONFIG.items():
            for chat_id in canais:
                try:
                    bot2.send_animation(
                        chat_id=chat_id,
                        animation=url_gif
                    )
                    BOT2_LOGGER.info(f"GIF enviado com sucesso para o canal {chat_id} ({idioma})")
                except Exception as e:
                    BOT2_LOGGER.error(f"Erro ao enviar GIF para o canal {chat_id}: {str(e)}")
        return True
    except Exception as e:
        BOT2_LOGGER.error(f"Erro ao enviar GIFs: {str(e)}")
        BOT2_LOGGER.error(traceback.format_exc())
        return False

# Função que envia o sinal para todos os canais
def enviar_sinal():
    """Envia um sinal para todos os canais configurados."""
    global contador_sinais, ultimo_sinal
    
    BOT2_LOGGER.info("Iniciando envio de sinal")
    
    # Incrementar o contador de sinais
    contador_sinais += 1
    
    # Gerar um novo sinal
    sinal = gerar_sinal()
    ultimo_sinal = sinal
    
    # Registrar informações do sinal
    BOT2_LOGGER.info(f"Sinal #{contador_sinais}: {sinal['ativo']} - {sinal['direcao']}")
    BOT2_LOGGER.info(f"Este é um sinal {'múltiplo de 3' if contador_sinais % 3 == 0 else 'normal'}")
    
    # Formatar mensagens para cada idioma
    mensagens = {}
    for idioma in BOT2_CANAIS_CONFIG.keys():
        mensagens[idioma] = formatar_mensagem_sinal(sinal, idioma)
    
    # Enviar o sinal
    enviado = enviar_mensagem(mensagens)
    
    if enviado:
        BOT2_LOGGER.info("Sinal enviado com sucesso")
        
        # Agendar envio do GIF pós-sinal (7 minutos depois)
        threading.Timer(7 * 60, enviar_gif_pos_sinal).start()
        BOT2_LOGGER.info("Agendado envio do GIF pós-sinal para daqui a 7 minutos")
        
        # Se for múltiplo de 3, agendar a sequência especial
        if contador_sinais % 3 == 0:
            threading.Timer(7 * 60, lambda: iniciar_sequencia_multiplo_tres(sinal)).start()
            BOT2_LOGGER.info("Agendada sequência especial para sinal múltiplo de 3")
    else:
        BOT2_LOGGER.error("Falha ao enviar o sinal")
    
    return enviado

# Função para enviar o GIF pós-sinal
def enviar_gif_pos_sinal():
    """Envia o GIF pós-sinal para todos os canais."""
    BOT2_LOGGER.info("Enviando GIF pós-sinal")
    return enviar_gif(URL_GIF_POS_SINAL)

# Função para iniciar a sequência de envios para sinais múltiplos de 3
def iniciar_sequencia_multiplo_tres(sinal):
    """
    Inicia a sequência de envios especial para os sinais múltiplos de 3.
    
    Args:
        sinal: O sinal que foi enviado
    """
    BOT2_LOGGER.info("Iniciando sequência para sinal múltiplo de 3")
    
    # O GIF pós-sinal já está agendado na função enviar_sinal
    
    # Agendar envio da mensagem de participação (40 minutos após o sinal)
    threading.Timer(40 * 60, enviar_mensagem_participacao).start()
    BOT2_LOGGER.info("Agendado envio da mensagem de participação para daqui a 40 minutos")

# Função para enviar a mensagem de participação
def enviar_mensagem_participacao():
    """Envia a mensagem de participação para todos os canais."""
    BOT2_LOGGER.info("Enviando mensagem de participação")
    
    # Formatar mensagens para cada idioma
    mensagens = {}
    for idioma in BOT2_CANAIS_CONFIG.keys():
        mensagens[idioma] = formatar_mensagem_participacao(idioma)
    
    enviado = enviar_mensagem(mensagens)
    
    if enviado:
        BOT2_LOGGER.info("Mensagem de participação enviada com sucesso")
        
        # Agendar envio do GIF promocional (10 minutos depois)
        threading.Timer(10 * 60, enviar_gif_promocional).start()
        BOT2_LOGGER.info("Agendado envio do GIF promocional para daqui a 10 minutos")
    else:
        BOT2_LOGGER.error("Falha ao enviar mensagem de participação")
    
    return enviado

# Função para enviar o GIF promocional
def enviar_gif_promocional():
    """Envia o GIF promocional para todos os canais."""
    BOT2_LOGGER.info("Enviando GIF promocional")
    enviado = enviar_gif(URL_GIF_PROMO)
    
    if enviado:
        BOT2_LOGGER.info("GIF promocional enviado com sucesso")
        
        # Agendar envio da mensagem de abertura da corretora (1 minuto depois)
        threading.Timer(1 * 60, enviar_mensagem_abertura_corretora).start()
        BOT2_LOGGER.info("Agendado envio da mensagem de abertura da corretora para daqui a 1 minuto")
    else:
        BOT2_LOGGER.error("Falha ao enviar GIF promocional")
    
    return enviado

# Função para enviar a mensagem de abertura da corretora
def enviar_mensagem_abertura_corretora():
    """Envia a mensagem de abertura da corretora para todos os canais."""
    BOT2_LOGGER.info("Enviando mensagem de abertura da corretora")
    
    # Formatar mensagens para cada idioma
    mensagens = {}
    for idioma in BOT2_CANAIS_CONFIG.keys():
        mensagens[idioma] = formatar_mensagem_abertura_corretora(idioma)
    
    enviado = enviar_mensagem(mensagens)
    
    if enviado:
        BOT2_LOGGER.info("Mensagem de abertura da corretora enviada com sucesso")
    else:
        BOT2_LOGGER.error("Falha ao enviar mensagem de abertura da corretora")
    
    return enviado

# Função para iniciar o bot e agendar os sinais
def iniciar_bot():
    """Inicia o bot e agenda o envio de sinais para cada hora."""
    BOT2_LOGGER.info("Iniciando bot...")
    
    # Agendar envio de sinais para minuto 13 de cada hora
    for hora in range(24):
        # Formato: HH:MM (exemplo: "09:13")
        horario = f"{hora:02d}:13"
        schedule.every().day.at(horario).do(enviar_sinal)
        BOT2_LOGGER.info(f"Agendado envio de sinal para {horario}")
    
    BOT2_LOGGER.info("Bot iniciado com sucesso. Executando loop de agendamento...")
    
    # Loop para verificar os agendamentos
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except Exception as e:
            BOT2_LOGGER.error(f"Erro no loop principal: {str(e)}")
            BOT2_LOGGER.error(traceback.format_exc())
            time.sleep(10)  # Esperar um pouco antes de continuar

# Executar o bot se este arquivo for executado diretamente
if __name__ == "__main__":
    try:
        BOT2_LOGGER.info("Iniciando execução do bot")
        iniciar_bot()
    except KeyboardInterrupt:
        BOT2_LOGGER.info("Bot interrompido pelo usuário")
    except Exception as e:
        BOT2_LOGGER.error(f"Erro ao iniciar o bot: {str(e)}")
        BOT2_LOGGER.error(traceback.format_exc())
