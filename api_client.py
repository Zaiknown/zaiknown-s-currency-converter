# api_client.py

import requests
from datetime import date, timedelta

class ApiClient:
    """Uma classe dedicada a todas as comunicações com a API do Frankfurter."""
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://api.frankfurter.app"

    def obter_nomes_moedas(self):
        """Busca o dicionário de moedas e seus nomes completos."""
        url = f"{self.base_url}/currencies"
        resposta = self.session.get(url, timeout=10)
        resposta.raise_for_status()
        return resposta.json()

    def obter_taxa_atual(self, base, destino):
        """Busca a taxa de câmbio mais recente entre duas moedas."""
        if base == destino:
            return 1.0
        
        url = f"{self.base_url}/latest?from={base.upper()}&to={destino.upper()}"
        resposta = self.session.get(url, timeout=10)
        resposta.raise_for_status()
        dados = resposta.json()
        taxa = dados.get('rates', {}).get(destino.upper())
        if taxa is None:
            raise ValueError(f"Taxa para {destino} não encontrada na resposta da API.")
        return taxa

    def obter_historico(self, base, destino, dias=30):
        """Busca os dados de cotação dos últimos X dias."""
        hoje = date.today()
        data_inicio = hoje - timedelta(days=dias)
        hoje_str = hoje.strftime('%Y-%m-%d')
        data_inicio_str = data_inicio.strftime('%Y-%m-%d')
        
        url = f"{self.base_url}/{data_inicio_str}..{hoje_str}?from={base}&to={destino}"
        resposta = self.session.get(url, timeout=15)
        resposta.raise_for_status()
        dados = resposta.json()

        rates = dados.get('rates', {})
        if not rates:
            raise ValueError("Não há dados históricos para este par de moedas.")
            
        datas_ord = sorted(rates.keys())
        valores = [rates[d][destino] for d in datas_ord]
        return datas_ord, valores