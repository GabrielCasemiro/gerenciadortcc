# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth import login as auth_login
from django.http import HttpResponseRedirect
from django.db import models
from django.forms import ModelForm, ModelChoiceField
from django.shortcuts import redirect
from .models import *
from django import forms
from django.shortcuts import get_object_or_404
from django.db.models import Q
def strip_accents(text):
    """
    Strip accents from input String.

    :param text: The input string.
    :type text: String.

    :returns: The processed String.
    :rtype: String.
    """
    try:
        text = unicode(text, 'utf-8')
    except (TypeError, NameError): # unicode is a default on python 3 
        pass
    text = unicodedata.normalize('NFD', text)
    text = text.encode('ascii', 'ignore')
    text = text.decode("utf-8")
    return str(text)

class UserForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['username','ra','password','email','ra','perfil']
        widgets = {
        'password': forms.PasswordInput(),
        }


class UserModelChoiceField(ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.username

class TrabalhoForm(forms.ModelForm):
    aluno = UserModelChoiceField(queryset=Usuario.objects.filter(perfil="Aluno"),required=False)
    professor = UserModelChoiceField(queryset=Usuario.objects.filter(perfil="Professor"),required=False)
    class Meta:
        model = Trabalho
        fields = ['titulo','descricao','aluno','professor','tipo']

class AtividadeForm(forms.ModelForm):
    class Meta:
        model = Atividade
        fields = ['titulo','data_inicio','data_final','trabalho']

def trabalho_delete(request):
    name = request.POST.get('username','')
    if request.method == "POST":
        if name:
            try:
                Trabalho.objects.filter(pk=name).delete()
            except:
                pass
    return redirect('/index/')
def trabalho_show(request, username):
    usuario = request.user 
    path = "trabalho"

    trabalho = get_object_or_404(Trabalho, pk=username)
    if request.method == "POST":
        form = AtividadeForm(request.POST or None)
        if form.is_valid():
            form.save()
            return redirect('/trabalho/show/' + username)
        else:
            return redirect('/index/')

    atividades = Atividade.objects.filter(trabalho=username).all()
    return render(request, 'trabalho_show.html', {'trabalho':trabalho,'path':path,'usuario':usuario,'id':username,'atividades':atividades})


def trabalho_edit(request, username): 
    instance = get_object_or_404(Trabalho, pk=username)
    if request.method == "POST":
        form = TrabalhoForm(request.POST or None, instance=instance)
        if form.is_valid():
            form.save()
            return redirect('/index/')
    else:
        form = TrabalhoForm(instance=instance)
    titulo = u"Edição do Trabalho: %s" % instance.descricao
    link = u"/trabalho/edit/%s/" % instance.pk
    return render(request, 'model_form.html', {'form': form,"username":username,"titulo":titulo, "link":link}) 

def trabalho_add(request):
    path = str(request.path)
    form = TrabalhoForm()
    usuario = request.user
    if request.method == "POST":
        teste = request.POST.copy() 
        f = TrabalhoForm(teste)
        if f.is_valid():
            f.save()
            response = redirect('/index/')
            return response
        else:
            form = TrabalhoForm(teste)
    titulo = "Adicionar Trabalho"
    link = "/trabalho/add/"
    return render(request, 'model_form.html', {"usuario":usuario,"form":form,"path": path,"titulo":titulo,"link":link})

def usuario_edit(request, username): 
    instance = get_object_or_404(Usuario, username=username)
    if request.method == "POST":
        form = UserForm(request.POST or None, instance=instance)
        usuario = get_object_or_404(User, username=username)
        if form.is_valid():
            form.save()
            usuario.set_password(form.data['password'])
            usuario.save()
            return HttpResponseRedirect('/usuario/list/')
    else:
        form = UserForm(instance=instance)
    return render(request, 'usuarios_edit.html', {'form': form,"username":username}) 

def usuario_add(request):
    path = str(request.path)
    form = UserForm()
    usuario = request.user
    titulo = "Adicionar Usuário"
    link = "/usuario/add/"
    existe = 0
    if request.method == "POST":
        teste = request.POST.copy() 
        f = UserForm(teste)
        if f.is_valid():
            user = User.objects.create_user(teste['username'], teste['email'], teste['password'])
            user.is_superuser = 1
            user.is_staff = 0
            user.is_active = 1
            user.save()
            f.save()
            usuarios = Usuario.objects.all()
            mensagem = "Usuário cadastrado com sucesso!" 
            return render(request, 'usuarios_list.html', {"mensagem":mensagem,"usuario":usuario,"usuarios":usuarios,"path": path})
        else:
            form = UserForm(teste)
    return render(request, 'model_form.html', {"usuario":usuario,"form":form,"path": path,"titulo":titulo,"link":link})

def usuario_delete(request):
    path = str(request.path)
    usuario = request.user 
    name = request.POST.get('username','')
    mensagem = ''
    if request.method == "POST":
        if name:
            try:
                User.objects.filter(username=name).delete()
                Usuario.objects.filter(username=name).delete()
            except:
                pass
            mensagem = "Usuário " + name + " deletado com sucesso!" 
            
    usuarios = Usuario.objects.all()
    return render(request, 'usuarios_list.html', {"mensagem":mensagem,"usuario":usuario,"usuarios":usuarios,"path": path})

def usuario_list(request):
    path = str(request.path)
    usuario = request.user 
    usuarios = Usuario.objects.all()
    return render(request, 'usuarios_list.html', {"usuario":usuario,"usuarios":usuarios,"path": path})
    
def login(request):
    username = request.POST.get('username','')
    password = request.POST.get('password','')
    if username:
        user = authenticate(request, username=username, password=password)
        if user is not None:
            try:
                usuario = get_object_or_404(Usuario, username=username)
            except:
                pass        
            try:
                request.session['perfil'] = usuario.perfil
            except:
                pass
            auth_login(request, user)
            return HttpResponseRedirect('/index/')
        else:
            mensagem = "Usuário inválido."
            return render(request, 'login.html', {"mensagem":mensagem})
    else:
        return render(request, 'login.html')

def home(request):
    path = str(request.path)
    usuario = request.user
    if not request.session.get('perfil') == "Coordenador":
        andamento = Trabalho.objects.filter(Q(tipo="Andamento",aluno=usuario.username)|Q(tipo="Andamento",professor=usuario.username))
        pendente = Trabalho.objects.filter(Q(tipo="Pendente",aluno=usuario.username)|Q(tipo="Pendente",professor=usuario.username))
        concluido = Trabalho.objects.filter(Q(tipo="Concluido",aluno=usuario.username)|Q(tipo="Concluido",professor=usuario.username))
    else:
        andamento = Trabalho.objects.filter(tipo="Andamento")
        pendente = Trabalho.objects.filter(tipo="Pendente")
        concluido = Trabalho.objects.filter(tipo="Concluido")

    return render(request, 'index.html', {"usuario": usuario,
        "path": path,
        "andamento":andamento,
        "pendente":pendente,
        "concluido":concluido})

# LOGOUT
def logout_act(request):
    logout(request)
    return HttpResponseRedirect('/login/')