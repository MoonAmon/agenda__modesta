from django import forms
from .models import Orcamento, Recibo, PacoteServico


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
            'valor_hora_pacote': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'valor_hora_referencia': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'inclui_otimizacao': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'beneficios': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }
