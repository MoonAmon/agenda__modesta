from django import forms
from decimal import Decimal, ROUND_HALF_UP
from .models import Orcamento, Recibo, PacoteServico

TWO_PLACES = Decimal("0.01")


class OrcamentoForm(forms.ModelForm):
    class Meta:
        model = Orcamento
        fields = [
            'cliente',
            'projeto',
            'pacote',
            'descricao',
            'horas_trabalhadas',
            'valor_hora',
            'valor_total',
            'forma_pagamento',
            'status_pagamento',
            'data_validade',
        ]
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-input'}),
            'projeto': forms.Select(attrs={'class': 'form-input'}),
            'pacote': forms.Select(attrs={'class': 'form-input'}),
            'descricao': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'horas_trabalhadas': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.5'}),
            'valor_hora': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'valor_total': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01', 'readonly': True}),
            'forma_pagamento': forms.Select(attrs={'class': 'form-input'}),
            'status_pagamento': forms.Select(attrs={'class': 'form-input'}),
            'data_validade': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Tornar horas e valor_hora não obrigatórios (serão preenchidos
        # automaticamente quando um pacote com horas inclusas for selecionado)
        self.fields['horas_trabalhadas'].required = False
        self.fields['valor_hora'].required = False
        self.fields['valor_total'].required = False

    def clean(self):
        cleaned_data = super().clean()
        pacote = cleaned_data.get('pacote')
        horas = cleaned_data.get('horas_trabalhadas')
        valor_hora = cleaned_data.get('valor_hora')

        if pacote and pacote.horas_inclusas:
            # Pacote com horas inclusas: preencher automaticamente
            valor = pacote.valor_hora_pacote.amount
            cleaned_data['horas_trabalhadas'] = pacote.horas_inclusas
            cleaned_data['valor_hora'] = valor.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
            cleaned_data['valor_total'] = (pacote.horas_inclusas * valor).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
        elif pacote:
            # Pacote sem horas inclusas (hora avulsa): precisa de horas
            if not horas:
                self.add_error('horas_trabalhadas', 'Informe a quantidade de horas.')
            valor = pacote.valor_hora_pacote.amount
            cleaned_data['valor_hora'] = valor.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
            if horas:
                cleaned_data['valor_total'] = (horas * valor).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
        else:
            # Sem pacote: precisa de horas e valor_hora
            if not horas:
                self.add_error('horas_trabalhadas', 'Informe a quantidade de horas.')
            if not valor_hora:
                self.add_error('valor_hora', 'Informe o valor por hora.')

        return cleaned_data


class ReciboForm(forms.ModelForm):
    class Meta:
        model = Recibo
        fields = [
            'cliente',
            'projeto',
            'descricao',
            'horas_trabalhadas',
            'valor_hora',
            'valor_total',
            'forma_pagamento',
        ]
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-input'}),
            'projeto': forms.Select(attrs={'class': 'form-input'}),
            'descricao': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'horas_trabalhadas': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.5'}),
            'valor_hora': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'valor_total': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'forma_pagamento': forms.Select(attrs={'class': 'form-input'}),
        }


class PacoteServicoForm(forms.ModelForm):
    class Meta:
        model = PacoteServico
        fields = [
            'nome',
            'descricao',
            'horas_inclusas',
            'valor_hora_pacote',
            'valor_hora_referencia',
            'inclui_otimizacao',
            'beneficios',
            'ativo',
        ]
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-input'}),
            'descricao': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'horas_inclusas': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.5'}),
            'inclui_otimizacao': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'beneficios': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }

    def clean_valor_hora_referencia(self):
        """Permitir valor_hora_referencia vazio."""
        valor = self.cleaned_data.get('valor_hora_referencia')
        # Se o valor for vazio ou 0, retornar None
        if not valor or (hasattr(valor, 'amount') and valor.amount == 0):
            return None
        return valor

    def clean_horas_inclusas(self):
        """Tratar horas_inclusas vazio como None."""
        horas = self.cleaned_data.get('horas_inclusas')
        if horas is not None and horas == 0:
            return None
        return horas
