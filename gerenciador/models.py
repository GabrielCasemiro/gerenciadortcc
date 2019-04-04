# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import models
from django.core.validators import MaxValueValidator
from django.contrib.auth.models import User
from datetime import datetime, timedelta
from django.core.validators import FileExtensionValidator
media_url_atividade = '/home/gabriel/Desktop/TCC/tcc/gerenciador'
ESCOLHA_PERFIL = (
    ('Aluno', 'Aluno'),
    ('Professor', 'Professor'),
    ('Coordenador', 'Coordenador')
    )

ESCOLHA_TRABALHO = (
    ('Andamento', 'Em Andamento'),
    ('Pendente', 'Pendente'),
    ('Concluido', 'Concluido')
    )

class Usuario(models.Model):
    username = models.CharField(primary_key=True, max_length=150,default='')
    email = models.EmailField(max_length=254,default='')
    password = models.CharField(max_length=150,default='')
    ra = models.PositiveIntegerField(validators=[MaxValueValidator(999999)],default='',unique = True)
    perfil = models.CharField(
        max_length=20,
        choices=ESCOLHA_PERFIL,
        default='Aluno'
    )
    
class Trabalho(models.Model):
    titulo = models.CharField(max_length=150,default='',help_text="Título do Trabalho")
    descricao = models.CharField(max_length=30000,default='',help_text="Descrição do Trabalho")
    tipo = models.CharField(
        max_length=30,
        choices=ESCOLHA_TRABALHO,
        default='Andamento'
    )
    data_inicio = models.DateField(help_text="Data de Início", auto_now_add=True)
    aluno = models.ForeignKey(Usuario, related_name='Aluno',blank=True, null=True,on_delete=models.CASCADE)
    professor = models.ForeignKey(Usuario, related_name='Professor',blank=True, null=True,on_delete=models.CASCADE)

class Atividade(models.Model):
    titulo = models.CharField(max_length=150,default='',help_text="Título da Atividade")
    data_inicio = models.DateField(help_text="Data de início da atividade")
    data_final = models.DateField(help_text="Data final da entrega da Atividade")
    arquivo = models.BooleanField(default=False,help_text="Atividade terá entrega")
    trabalho = models.ForeignKey(Trabalho,related_name='Trabalho',on_delete=models.CASCADE)
    entrega = models.FileField(blank=True, null=True,validators=[FileExtensionValidator(allowed_extensions=['pdf'])])
    def range(self):
        datas = []
        diferenca = self.data_final.month - self.data_inicio.month
        if diferenca == 0:
            datas.append(self.data_inicio.month)
        else:
            for i in range(0, diferenca+1):
                datas.append(self.data_final.month - i)
        return datas
    def data_mes_ano(self):
        maximo_date = self.data_final
        minimo = self.data_inicio
        meses_atividades = [minimo.strftime('%m/%Y')]
        while minimo <= maximo_date:
            minimo += timedelta(days=31)
            meses_atividades.append(datetime(minimo.year, minimo.month, 1).strftime('%m/%Y') )
        return meses_atividades

