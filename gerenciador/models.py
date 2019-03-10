# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.core.validators import MaxValueValidator
# Create your models here.
from django.contrib.auth.models import User
from django.db.models import Q

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
    ra = models.PositiveIntegerField(validators=[MaxValueValidator(999999)],default='')
    perfil = models.CharField(
        max_length=20,
        choices=ESCOLHA_PERFIL,
        default='Aluno'
    )
    
class Trabalho(models.Model):
    titulo = models.CharField(max_length=150,default='',help_text="Título do Trabalho")
    descricao = models.CharField(max_length=15000,default='',help_text="Descrição do Trabalho")
    tipo = models.CharField(
        max_length=30,
        choices=ESCOLHA_TRABALHO,
        default='Andamento'
    )
    data_inicio = models.DateField(help_text="Data de Início", auto_now_add=True)
    professor = models.ForeignKey(Usuario,limit_choices_to=Q(perfil='Professor'), related_name='Professor')
    aluno = models.ForeignKey(Usuario, limit_choices_to=Q(perfil='Aluno'), related_name='Aluno')

class Atividade(models.Model):
    titulo = models.CharField(max_length=150,default='',help_text="Título da Atividade")
    data_inicio = models.DateField(help_text="Data de início da atividade")
    data_final = models.DateField(help_text="Data final da entrega da Atividade")
    trabalho = models.ForeignKey(Trabalho,related_name='Trabalho')
    entrega = models.FileField(upload_to='entregas/')
    def range(self):
        datas = []
        diferenca = self.data_final.month - self.data_inicio.month
        if diferenca == 0:
            datas.append(self.data_inicio.month)
        else:
            for i in range(0, diferenca+1):
                datas.append(self.data_final.month - i)
        return datas

