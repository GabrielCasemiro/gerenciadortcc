# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth import login as auth_login
from django.http import HttpResponseRedirect
from django.db import models
from django.forms import ModelForm, ModelChoiceField, Textarea
from django.shortcuts import redirect
from .models import *
from django import forms
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.core.mail import EmailMessage
from django.http import JsonResponse
from datetime import datetime, timedelta
import unicodedata
from django.http import HttpResponse
import os

from .models import media_url_atividade  
# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

############################################
##                                        ##
##           FUNCOES GENÉRICAS            ##
##                                        ##
############################################
link_site = "http://gerenciadortcc.pythonanywhere.com/login/"
def strip_accents(text):
    try:
        text = unicode(text, 'utf-8')
    except (TypeError, NameError): # unicode is a default on python 3 
        pass
    text = unicodedata.normalize('NFD', text)
    text = text.encode('ascii', 'ignore')
    text = text.decode("utf-8")
    return str(text)

############################################
##                                        ##
##             MODEL FORMS                ##
##                                        ##
############################################

class UserForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['username','ra','password','email','perfil']
        labels = {
        "username": "Nome Completo",
        "ra":"RA",
        "password": "Senha",
        "email":"E-mail",
        "perfil":"Perfil de Acesso"
        }
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
        widgets = {
            'descricao': Textarea(attrs={'cols': 80, 'rows': 10}),
        }

class AtividadeForm(forms.ModelForm):
    class Meta:
        model = Atividade
        fields = ['titulo','arquivo','data_inicio','data_final','trabalho']

class EntregaAtividadeForm(forms.ModelForm):
    class Meta:
        model = Atividade
        fields = ['entrega']
############################################
##                                        ##
##             TRABALHOS                  ##
##                                        ##
############################################

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
    formulario_list = []

    trabalho = get_object_or_404(Trabalho, pk=int(username))
    if request.method == "POST":
        form = AtividadeForm(request.POST or None)
        dados_form = request.POST
        if form.is_valid():
            form.save()
            try:
                mensagem_email = u"Uma nova atividade foi cadastrada no cronograma do TCC de seguinte título:"+trabalho.titulo+".\n\n"+"Informações sobre a atividade:\n\nNome da Atividade: "+dados_form['titulo']+"\nData de Início: "+dados_form['data_inicio']+"\nData de Término: "+dados_form['data_final']+"\n\n"+"Acesse o sistema utilizando o link: "+"http://gerenciadortcc.pythonanywhere.com/login/"+"."
                email = EmailMessage('Nova atividade para seu TCC', mensagem_email, to=[trabalho.aluno.email, trabalho.professor.email])
                email.send()
            except:
                print("Falha ao enviar o e-mail.")
            return redirect('/trabalho/show/' + username)
        else:
            return redirect('/index/')
    else:
        atividades = Atividade.objects.filter(trabalho=username).order_by("data_inicio")
        meses_atividades = []
        if atividades:
            datas_atividades = Atividade.objects.filter(trabalho=username).values_list('data_inicio', flat=True).distinct()
            datas_atividades_fim = Atividade.objects.filter(trabalho=username).values_list('data_final', flat=True).distinct()
            ## Calcula os meses das atividades ###
            maximo_date = max(datas_atividades_fim)
            minimo = min(datas_atividades)
            meses_atividades = [minimo.strftime('%m/%Y')]
            from calendar import monthrange

            while minimo <= maximo_date:
                minimo += timedelta(days=monthrange(minimo.year, minimo.month)[1])
                meses_atividades.append( datetime(minimo.year, minimo.month, 1).strftime('%m/%Y') )
        form = AtividadeForm()

        atividades_entregas = atividades.filter(arquivo=True)
        data_hoje = datetime.now().date()
        return render(request, 'trabalho_show.html', {'form':form,'trabalho':trabalho,'path':path,'usuario':usuario,'id':username,'atividades':atividades,'meses_atividades':meses_atividades,'atividades_entregas':atividades_entregas,'data_hoje':data_hoje})

def download_file(request, id_entrega):
    atividade = get_object_or_404(Atividade, pk=id_entrega)
    link = os.path.join(BASE_DIR, 'media')
    response = HttpResponse(open(media_url_atividade+atividade.entrega.url, 'rb').read())
    response['Content-Type'] = 'text/plain'
    response['Content-Disposition'] = 'attachment; filename=' + str(atividade.entrega.name)
    return response
def entrega_tarefa(request, id_entrega):
    if request.method == "POST":
        atividade = get_object_or_404(Atividade, pk=id_entrega)
        file = request.FILES["entrega"]
        if file and atividade:
            atividade.entrega = file
            atividade.save()
            try:
                mensagem_email = u"Uma entrega de uma atividade foi realizada.\n\n"+"Informações sobre a atividade:\n\nNome da Atividade: "+atividade.titulo+"\nData de Início: "+atividade.data_inicio+"\nData final: "+atividade.data_final+"\n\n"+"Acesse o sistema utilizando o link: "+"http://gerenciadortcc.pythonanywhere.com/login/"+"."
                email = EmailMessage('Nova atividade para seu TCC', mensagem_email, to=[atividade.trabalho.aluno.email, atividade.trabalho.professor.email])
                email.send()
            except:
                print("Falha ao enviar o e-mail.")
            link = '/trabalho/show/' + str(atividade.trabalho.id) + '/'
            return redirect(link)
        else:
            return redirect('/index/')
    else:
        return redirect('/index/')
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
            ### ENVIO DE EMAILS ###
            mensagem_email = "\n\nUm trabalho foi cadastrado no Sistema Gerenciador de TCC com seu nome.\n\n"+"Acesse o sistema utilizando o link: " + link_site + "."
            email = EmailMessage('Sistema Gerenciador de TCC', mensagem_email, to=[Usuario.objects.filter(username=teste['aluno'])[0].email,Usuario.objects.filter(username=teste['professor'])[0].email])
            email.send()
            response = redirect('/index/')
            return response
        else:
            form = TrabalhoForm(teste)
    titulo = "Adicionar Trabalho"
    link = "/trabalho/add/"
    return render(request, 'model_form.html', {"usuario":usuario,"form":form,"path": path,"titulo":titulo,"link":link})

############################################
##                                        ##
##             USUÁRIOS                   ##
##                                        ##
############################################

def usuario_edit(request, username): 
    instance = get_object_or_404(Usuario, ra=int(username))
    if request.method == "POST":
        form = UserForm(request.POST or None, instance=instance)
        if form.is_valid():
            form.save()
            usuario = get_object_or_404(User, username=username)
            usuario.username = form.data['ra']
            usuario.first_name = form.data['username']
            usuario.email = form.data['email']
            usuario.set_password(form.data['password'])
            usuario.save()
            return HttpResponseRedirect('/usuario/list/')
    else:
        form = UserForm(instance=instance)
    return render(request, 'usuarios_edit.html', {'form': form,"ra":username}) 

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
            user = User.objects.create_user(teste['ra'], teste['email'], teste['password'],first_name=teste['username'])
            user.is_superuser = 1
            user.is_staff = 0
            user.is_active = 1
            user.save()
            f.save()
            usuarios = Usuario.objects.all()
            mensagem = "Usuário cadastrado com sucesso!" 
            mensagem_email = "\n\nParabéns " + teste['username'] + "! Você agora tem acesso ao sistema de Gerenciador de TCC.\n"+"Seu login: " + teste['ra'] + "\nSua senha: " + teste['password'] + "\n\nAcesse o sistema utilizando o link: " + link_site + "."        
            email = EmailMessage('Acesso ao Sistema Gerenciador de TCC', mensagem_email, to=[teste['email']])
            email.send()
            return render(request, 'usuarios_list.html', {"mensagem":mensagem,"usuario":usuario,"usuarios":usuarios,"path": path})
        else:
            form = UserForm(teste)
    return render(request, 'model_form.html', {"usuario":usuario,"form":form,"path": path,"titulo":titulo,"link":link})

def usuario_delete(request):
    path = str(request.path)
    usuario = request.user 
    ra = request.POST.get('ra','')
    mensagem = ''
    if request.method == "POST":
        if ra:
            try:
                User.objects.filter(username=ra).delete()
                Usuario.objects.filter(ra=ra).delete()
            except:
                pass
            mensagem = "Usuário " + ra + " deletado com sucesso!" 
            
    usuarios = Usuario.objects.all()
    return render(request, 'usuarios_list.html', {"mensagem":mensagem,"usuario":usuario,"usuarios":usuarios,"path": path})

def usuario_list(request):
    path = str(request.path)
    usuario = request.user 
    usuarios = Usuario.objects.all()
    return render(request, 'usuarios_list.html', {"usuario":usuario,"usuarios":usuarios,"path": path})

def removerAtividade(request):
    if request.method == "POST":
        id_atividade = request.POST.get('id_atividade','')
        mensagem = "Atividade não encontrada! Entre em contato com os administradores do sistema."
        usuario = False
        try:
            atividade = get_object_or_404(Atividade, pk=int(id_atividade))
        except:
            return JsonResponse({'mensagem': mensagem})
        if atividade != False:
            try:
                atividade.delete()
                return JsonResponse({'mensagem': 'Atividade removida com sucesso!'})
            except:
                pass
    else:
        response = redirect('/index/')
        return response
def recuperar_senha(request):
    if request.method == "POST":
        username = request.POST.get('ra','')
        mensagem = "Usuário não encontrado! Verifique o RA e tente novamente."
        usuario = False
        try:
            usuario = get_object_or_404(Usuario, ra=int(username))
        except:
            return JsonResponse({'mensagem': mensagem})
        if usuario != False:
            mensagem_email = "\n\n"+ usuario.username +", seu acesso no Sistema de Gerenciador de TCC foi recuperado!\n\nSeu login: "+ str(usuario.ra)+"\nSua senha: "+usuario.password+"\n\nAcesse o sistema utilizando o link: " + link_site + "." 
            email = EmailMessage('Recuperação de Senha - Sistema Gerenciador de TCC', mensagem_email, to=[usuario.email])
            email.send()
            return JsonResponse({'mensagem': 'Sua acesso foi recuperado. Verifique seu e-mail para concluir a recuperação.'})
    else:
        return render(request, 'recuperar_senha.html')

############################################
##                                        ##
##             VIEWS                      ##
##                                        ##
############################################

def login(request):
    username = request.POST.get('username','')
    password = request.POST.get('password','')
    if username:
        user = authenticate(request, username=username, password=password)
        if user is not None:
            try:
                usuario = get_object_or_404(Usuario, ra=username)
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
    andamento = []
    pendente = []
    concluido = []
    usuario_real = False
    usuario_real = Usuario.objects.filter(ra = request.user.username)
    try:
        if usuario_real != False:
            if equest.session.get('perfil') == "Aluno":
                andamento = Trabalho.objects.filter(tipo="Andamento",aluno=usuario_real)
                pendente = Trabalho.objects.filter(tipo="Pendente",aluno=usuario_real)
                concluido = Trabalho.objects.filter(tipo="Concluido",aluno=usuario_real)
            elif request.session.get('perfil') == "Professor":
                andamento = Trabalho.objects.filter(tipo="Andamento",professor=usuario_real)
                pendente = Trabalho.objects.filter(tipo="Pendente",professor=usuario_real)
                concluido = Trabalho.objects.filter(tipo="Concluido",professor=usuario_real)
            else:
                andamento = Trabalho.objects.filter(tipo="Andamento")
                pendente = Trabalho.objects.filter(tipo="Pendente")
                concluido = Trabalho.objects.filter(tipo="Concluido")
    except:
        pass

    return render(request, 'index.html', {"usuario": usuario,
        "path": path,
        "andamento":andamento,
        "pendente":pendente,
        "concluido":concluido})

def logout_act(request):
    logout(request)
    return HttpResponseRedirect('/login/')