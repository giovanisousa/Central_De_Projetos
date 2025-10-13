# -*- coding: utf-8 -*-
"""
Testes para o módulo google_calendar.py
Valida cálculo de datas, criação de eventos e funções auxiliares.
"""

import unittest
from datetime import datetime, timedelta
from google_calendar import (
    _calcular_sexta_feira_da_semana,
    validar_data_formato,
    obter_resumo_eventos
)


class TestCalculoSextaFeira(unittest.TestCase):
    """Testa cálculo de sexta-feira da semana."""
    
    def test_segunda_para_sexta(self):
        """Segunda-feira (2025-10-20) → Sexta-feira (2025-10-24)"""
        segunda = datetime(2025, 10, 20)  # Segunda
        resultado = _calcular_sexta_feira_da_semana(segunda)
        esperado = datetime(2025, 10, 24)  # Sexta
        self.assertEqual(resultado, esperado)
        self.assertEqual(resultado.weekday(), 4)  # 4 = Sexta
    
    def test_terca_para_sexta(self):
        """Terça-feira (2025-10-21) → Sexta-feira (2025-10-24)"""
        terca = datetime(2025, 10, 21)  # Terça
        resultado = _calcular_sexta_feira_da_semana(terca)
        esperado = datetime(2025, 10, 24)  # Sexta
        self.assertEqual(resultado, esperado)
    
    def test_quarta_para_sexta(self):
        """Quarta-feira (2025-10-22) → Sexta-feira (2025-10-24)"""
        quarta = datetime(2025, 10, 22)  # Quarta
        resultado = _calcular_sexta_feira_da_semana(quarta)
        esperado = datetime(2025, 10, 24)  # Sexta
        self.assertEqual(resultado, esperado)
    
    def test_quinta_para_sexta(self):
        """Quinta-feira (2025-10-23) → Sexta-feira (2025-10-24)"""
        quinta = datetime(2025, 10, 23)  # Quinta
        resultado = _calcular_sexta_feira_da_semana(quinta)
        esperado = datetime(2025, 10, 24)  # Sexta
        self.assertEqual(resultado, esperado)
    
    def test_sexta_para_sexta(self):
        """Sexta-feira (2025-10-24) → Mesma sexta-feira (2025-10-24)"""
        sexta = datetime(2025, 10, 24)  # Sexta
        resultado = _calcular_sexta_feira_da_semana(sexta)
        esperado = datetime(2025, 10, 24)  # Mesma sexta
        self.assertEqual(resultado, esperado)
    
    def test_sabado_para_sexta_anterior(self):
        """Sábado (2025-10-25) → Sexta anterior (2025-10-24)"""
        sabado = datetime(2025, 10, 25)  # Sábado
        resultado = _calcular_sexta_feira_da_semana(sabado)
        esperado = datetime(2025, 10, 24)  # Sexta anterior
        self.assertEqual(resultado, esperado)
    
    def test_domingo_para_sexta_anterior(self):
        """Domingo (2025-10-26) → Sexta anterior (2025-10-24)"""
        domingo = datetime(2025, 10, 26)  # Domingo
        resultado = _calcular_sexta_feira_da_semana(domingo)
        esperado = datetime(2025, 10, 24)  # Sexta anterior
        self.assertEqual(resultado, esperado)


class TestValidacaoData(unittest.TestCase):
    """Testa validação de formato de data."""
    
    def test_data_valida_formato_correto(self):
        """Data válida no formato YYYY-MM-DD"""
        self.assertTrue(validar_data_formato('2025-10-20'))
        self.assertTrue(validar_data_formato('2025-12-31'))
        self.assertTrue(validar_data_formato('2025-01-01'))
    
    def test_data_invalida_formato_errado(self):
        """Data com formato incorreto"""
        self.assertFalse(validar_data_formato('20/10/2025'))  # DD/MM/YYYY
        self.assertFalse(validar_data_formato('10-20-2025'))  # MM-DD-YYYY
        self.assertFalse(validar_data_formato('2025/10/20'))  # Barras em vez de hífens
    
    def test_data_invalida_valores(self):
        """Data com valores inválidos"""
        self.assertFalse(validar_data_formato('2025-13-01'))  # Mês 13
        self.assertFalse(validar_data_formato('2025-02-30'))  # 30 de fevereiro
        self.assertFalse(validar_data_formato('2025-00-01'))  # Mês 0
    
    def test_data_string_vazia_ou_none(self):
        """String vazia ou None"""
        self.assertFalse(validar_data_formato(''))
        self.assertFalse(validar_data_formato(None))
    
    def test_data_string_aleatoria(self):
        """String que não é data"""
        self.assertFalse(validar_data_formato('não é uma data'))
        self.assertFalse(validar_data_formato('abc-def-ghi'))


class TestResumoEventos(unittest.TestCase):
    """Testa geração de resumo de eventos."""
    
    def test_resumo_eventos_semana_normal(self):
        """Gera resumo para semana normal (segunda a sexta)"""
        resultado = obter_resumo_eventos('2025-10-20', '2025-10-27')
        
        self.assertIn('homologacao_inicio', resultado)
        self.assertIn('homologacao_fim', resultado)
        self.assertIn('virada_inicio', resultado)
        self.assertIn('virada_fim', resultado)
        
        # Homologação: 20/10 (segunda) a 24/10 (sexta)
        self.assertEqual(resultado['homologacao_inicio'], '20/10/2025 (Monday)')
        self.assertEqual(resultado['homologacao_fim'], '24/10/2025 (Friday)')
        
        # Virada: 27/10 (segunda) a 31/10 (sexta)
        self.assertEqual(resultado['virada_inicio'], '27/10/2025 (Monday)')
        self.assertEqual(resultado['virada_fim'], '31/10/2025 (Friday)')
    
    def test_resumo_eventos_com_periodos(self):
        """Verifica formatação dos períodos"""
        resultado = obter_resumo_eventos('2025-10-20', '2025-10-27')
        
        self.assertIn('homologacao_periodo', resultado)
        self.assertIn('virada_periodo', resultado)
        
        # Períodos no formato "DD/MM a DD/MM/YYYY"
        self.assertEqual(resultado['homologacao_periodo'], '20/10 a 24/10/2025')
        self.assertEqual(resultado['virada_periodo'], '27/10 a 31/10/2025')
    
    def test_resumo_eventos_data_invalida(self):
        """Retorna dict vazio para data inválida"""
        resultado = obter_resumo_eventos('data-invalida', '2025-10-27')
        self.assertEqual(resultado, {})
        
        resultado = obter_resumo_eventos('2025-10-20', 'outra-invalida')
        self.assertEqual(resultado, {})


class TestCenarioCompleto(unittest.TestCase):
    """Testa cenários completos de uso."""
    
    def test_cenario_implantacao_padrao(self):
        """Cenário típico: Início em segunda, homologação e virada em segundas seguintes"""
        # Data início: 20/10/2025 (segunda)
        # Homologação: 20/10 a 24/10 (segunda a sexta)
        # Virada: 27/10 a 31/10 (segunda a sexta da semana seguinte)
        
        data_inicio = '2025-10-20'
        data_homolog = '2025-10-20'
        data_virada = '2025-10-27'
        
        # Validar datas
        self.assertTrue(validar_data_formato(data_inicio))
        self.assertTrue(validar_data_formato(data_homolog))
        self.assertTrue(validar_data_formato(data_virada))
        
        # Calcular sextas-feiras
        dt_homolog = datetime.strptime(data_homolog, '%Y-%m-%d')
        dt_virada = datetime.strptime(data_virada, '%Y-%m-%d')
        
        sexta_homolog = _calcular_sexta_feira_da_semana(dt_homolog)
        sexta_virada = _calcular_sexta_feira_da_semana(dt_virada)
        
        # Validar resultados
        self.assertEqual(sexta_homolog.strftime('%Y-%m-%d'), '2025-10-24')
        self.assertEqual(sexta_virada.strftime('%Y-%m-%d'), '2025-10-31')
        
        # Gerar resumo
        resumo = obter_resumo_eventos(data_homolog, data_virada)
        self.assertEqual(resumo['homologacao_periodo'], '20/10 a 24/10/2025')
        self.assertEqual(resumo['virada_periodo'], '27/10 a 31/10/2025')
    
    def test_cenario_inicio_meio_semana(self):
        """Cenário: Início em quarta-feira"""
        # Data início: 22/10/2025 (quarta)
        # Homologação: 22/10 a 24/10 (quarta a sexta - mesma semana)
        # Virada: 29/10 a 31/10 (quarta a sexta da semana seguinte)
        
        data_homolog = '2025-10-22'  # Quarta
        data_virada = '2025-10-29'   # Quarta da semana seguinte
        
        dt_homolog = datetime.strptime(data_homolog, '%Y-%m-%d')
        dt_virada = datetime.strptime(data_virada, '%Y-%m-%d')
        
        sexta_homolog = _calcular_sexta_feira_da_semana(dt_homolog)
        sexta_virada = _calcular_sexta_feira_da_semana(dt_virada)
        
        # Ambas devem cair na sexta (24/10 e 31/10)
        self.assertEqual(sexta_homolog.strftime('%Y-%m-%d'), '2025-10-24')
        self.assertEqual(sexta_virada.strftime('%Y-%m-%d'), '2025-10-31')
    
    def test_cenario_inicio_sexta(self):
        """Cenário edge case: Início em sexta-feira"""
        # Data início: 24/10/2025 (sexta)
        # Homologação: 24/10 (apenas sexta)
        # Virada: 31/10 (sexta da semana seguinte)
        
        data_homolog = '2025-10-24'  # Sexta
        data_virada = '2025-10-31'   # Sexta da semana seguinte
        
        dt_homolog = datetime.strptime(data_homolog, '%Y-%m-%d')
        dt_virada = datetime.strptime(data_virada, '%Y-%m-%d')
        
        sexta_homolog = _calcular_sexta_feira_da_semana(dt_homolog)
        sexta_virada = _calcular_sexta_feira_da_semana(dt_virada)
        
        # Ambas devem retornar a própria data (já são sextas)
        self.assertEqual(sexta_homolog.strftime('%Y-%m-%d'), '2025-10-24')
        self.assertEqual(sexta_virada.strftime('%Y-%m-%d'), '2025-10-31')


def run_tests():
    """Executa todos os testes."""
    print("\n" + "="*70)
    print("TESTES DO MÓDULO GOOGLE CALENDAR")
    print("="*70 + "\n")
    
    # Criar suite de testes
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Adicionar todos os testes
    suite.addTests(loader.loadTestsFromTestCase(TestCalculoSextaFeira))
    suite.addTests(loader.loadTestsFromTestCase(TestValidacaoData))
    suite.addTests(loader.loadTestsFromTestCase(TestResumoEventos))
    suite.addTests(loader.loadTestsFromTestCase(TestCenarioCompleto))
    
    # Executar testes com verbose
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Resumo final
    print("\n" + "="*70)
    print("RESUMO DOS TESTES")
    print("="*70)
    print(f"✅ Testes executados: {result.testsRun}")
    print(f"✅ Sucessos: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ Falhas: {len(result.failures)}")
    print(f"❌ Erros: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n🎉 TODOS OS TESTES PASSARAM! 🎉\n")
        return 0
    else:
        print("\n⚠️ ALGUNS TESTES FALHARAM ⚠️\n")
        return 1


if __name__ == '__main__':
    exit(run_tests())
