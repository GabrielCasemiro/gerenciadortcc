# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth import login as auth_login
from django.http import HttpResponseRedirect
from django.db import models
from django.forms import ModelForm, ModelMultipleChoiceField, ModelChoiceField, Textarea
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

import io
from django.http import FileResponse
from reportlab.pdfgen import canvas


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
        "ra":"RA/Matrícula",
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

class UserModelChoiceFieldMultiple(ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return obj.username

class DateInput(forms.DateInput):
    input_type = 'date'  

class  TimeInput(forms.DateInput):
    input_type = 'time'  

class TCCModelChoiceField(ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.titulo

class AtaForm(forms.ModelForm):
    avaliadores = UserModelChoiceFieldMultiple(queryset=Usuario.objects.filter(perfil="Professor"),required=False)
    tcc = TCCModelChoiceField(queryset=Trabalho.objects.filter(tipo='Andamento'),required=True)
    class Meta:
        model = Ata
        fields = ['tcc','data','hora','avaliadores','observacoes']
        labels = {
        "tcc": "TCC em Andamento",
        "data":"Data da Defesa",
        "avaliadores": "Avaliadores",
        "observacoes":"Observações"
        }
        widgets = {
            'hora':TimeInput(),
            'data': DateInput()
        }


############################################
##                                        ##
##             ATAS                       ##
##                                        ##
############################################

def gerar_certificado(usuario,defesa):
    buffer = io.BytesIO()

    p = canvas.Canvas(buffer)

    mensagem = "Certifico a participação do integrante %s na defesa do TCC %s no dia %s." % (usuario.username, defesa.tcc.titulo, defesa.data)
    p.drawString(100, 100, mensagem)

    p.showPage()
    p.save()

    return FileResponse(buffer, as_attachment=True, filename='hello.pdf')

def certificado(request):
    if request.method == "POST":
        usuario = request.POST.get('usuario')
        defesa = request.POST.get('defesa','')
        try:
            usuario_obj = get_object_or_404(Usuario, pk=int(atividade))
            defesa_obj = get_object_or_404(Ata, pk=int(usuario))
        except:
            return render(request, 'error.html', {'mensagem':"Erro ao selecionar o usuário ou a defesa. Entre em contato com os administradores."})
        if usuario_obj and defesa_obj:
            return gerar_certificado(usuario_obj, defesa_obj)
    else:
        return redirect('/index/')

def show_atas(request):
    path = str(request.path)
    usuario = request.user
    usuario_real = False
    usuario_real = Usuario.objects.filter(ra = request.user.username)
    atas = Ata.objects.all()

    try:
        if usuario_real != False:
            if request.session.get('perfil') == "Aluno":
                atas = andamento.filter(aluno=usuario_real)
            elif request.session.get('perfil') == "Professor":
                atas = andamento.filter(aluno=usuario_real)
    except:
        pass

    return render(request, 'show_atas.html', {"usuario": usuario, "path": path,"atas":atas})

def atas_add(request):
    path = str(request.path)
    form = AtaForm()
    usuario = request.user
    if request.method == "POST":
        teste = request.POST.copy() 
        f = AtaForm(teste)
        if teste['avaliadores'] != '':
            if f.is_valid():
                f.save()
                ## ENVIO DE EMAILS ###
                try:
                    trabalho = Trabalho.objects.get(id=teste['tcc'])
                    avaliadores = Usuario.objects.filter(username__contains = teste['avaliadores'])
                    avaliadores = avaliadores.values_list('email', flat=True)
                    avaliadores_emails = ','.join([str(i) for i in avaliadores])
                    mensagem_email = "\n\nUma defesa de um TCC foi cadastrada no Sistema Gerenciador de TCC com seu nome.\n\n"+"Acesse o sistema utilizando o link: " + link_site + "."
                    email = EmailMessage('Sistema Gerenciador de TCC', mensagem_email, to=[trabalho.aluno.email, trabalho.professor.email,avaliadores_emails])
                    email.send()
                except:
                    pass
                response = redirect('/show_defesas/')
                return response
            else:
                form = AtaForm(teste)
        else:
            return render(request, 'error.html', {'mensagem':"Selecione ao menos 1 avaliador."})
    titulo = "Adicionar Defesa"
    link = "/defesa/add/"
    return render(request, 'model_form.html', {"usuario":usuario,"form":form,"path": path,"titulo":titulo,"link":link})

def ata_delete(request):
    name = request.POST.get('username','')
    if request.method == "POST":
        if name:
            try:
                Ata.objects.filter(pk=name).delete()
            except:
                pass
    return redirect('/show_defesas/')

def defesa_show(request, pk):
    usuario = request.user
    path = 'defesa'
    defesa = get_object_or_404(Ata, pk=int(pk))

    atividades = Atividade.objects.filter(trabalho=Trabalho.objects.filter(pk=defesa.tcc.pk), aprovado=True)
    integrantes = list(defesa.avaliadores.all())
    integrantes.append(defesa.tcc.aluno)
    integrantes.append(defesa.tcc.professor)
    integrantes = list(set(list(integrantes)))

    return render(request, 'defesa_show.html', {'defesa':defesa,'path':path,'usuario':usuario,'atividades':atividades,'integrantes':integrantes})

def resultado_defesa(request, pk):
    usuario = request.user
    path = 'defesa'
    defesa = get_object_or_404(Ata, pk=int(pk))
    if defesa.monografia:
        if request.method == "POST":
            aprovado = request.POST.get('aprovado','')
            if aprovado != '':
                defesa.aprovado = aprovado
                if request.FILES:
                    uploaded_file = request.FILES['file']
                    defesa.entrega =  uploaded_file
                defesa.save()
                trabalho = Trabalho.objects.get(id=defesa.tcc.id)
                trabalho.tipo = 'Concluido'
                trabalho.save()
                return redirect('/defesa/show/'+str(defesa.id)+'/')
            else:
                return render(request, 'error.html', {'mensagem':"Preencha todos os campos para submeter o resultado."})
        return render(request, 'resultado_defesa.html', {'defesa':defesa,'path':path,'usuario':usuario})
    else:
        return render(request, 'error.html', {'mensagem':"Defesa sem monografia cadastrada."})


    

def selecionarDefesa(request):
    if request.method == "POST":
        atividade = request.POST.get('atividade')
        defesa = request.POST.get('defesa','')
        try:
            atividade_obj = get_object_or_404(Atividade, pk=int(atividade))
            defesa_obj = get_object_or_404(Ata, pk=int(defesa))
        except:
            return render(request, 'error.html', {'mensagem':"Erro ao selecionar a atividade ou a defesa. Entre em contato com os administradores."})
        if atividade_obj and defesa_obj:
            defesa_obj.monografia = atividade_obj
            defesa_obj.save()
            ### ENVIO DE E-MAIL ###
            trabalho = Trabalho.objects.get(id=defesa_obj.tcc.id)
            avaliadores_emails = ','.join([str(avaliador.email) for avaliador in defesa_obj.avaliadores.all()])
            mensagem = """A monografia do TCC %s foi cadastrada com sucesso no Sistema Gerenciador de TCC.\n\n
Informações sobre a defesa:\n
Data: %s\n
Observações: %s
\n\n
Acesse o sistema utilizando o link: %s.""" % (trabalho.titulo, defesa_obj.data.strftime('%d/%m/%Y'), defesa_obj.observacoes, link_site)

            email = EmailMessage('Sistema Gerenciador de TCC', mensagem, to=[trabalho.aluno.email, trabalho.professor.email, avaliadores_emails])
            
            ## ANEXO DA ATIVIDADE ##
            email.attach_file(atividade_obj.entrega.path)
            
            email.send()

        return redirect('/defesa/show/'+defesa+'/')
    else:
        return redirect('/index/')

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

def download_ata(request, pk):
    ata = get_object_or_404(Ata, pk=pk)
    link = os.path.join(BASE_DIR, 'media')
    response = HttpResponse(open(media_url_atividade+ata.entrega.url, 'rb').read())
    response['Content-Type'] = 'text/plain'
    response['Content-Disposition'] = 'attachment; filename=' + str(ata.entrega.name)
    return response


def entrega_tarefa(request, id_entrega):
    if request.method == "POST":
        atividade = get_object_or_404(Atividade, pk=id_entrega)
        file = request.FILES["entrega"]
        if file and atividade:
            if file.size <= 83886080:
                if file.content_type == u'application/pdf':
                    atividade.entrega = file
                    atividade.save()
                    try:
                        mensagem_email = u"A entrega da atividade "+atividade.titulo+" foi realizada com sucesso.\n\n"+"Acesse o sistema utilizando o link: "+link_site+"."
                        email = EmailMessage('Sistema Gerenciador de TCC', mensagem_email, to=[atividade.trabalho.aluno.email, atividade.trabalho.professor.email])
                        email.send()
                    except:
                        pass
                    link = '/trabalho/show/' + str(atividade.trabalho.id) + '/'
                    return redirect(link)
                else:
                    return render(request, 'error.html', {'mensagem':" O arquivo de entrega da atividade deve ser do tipo pdf."})
            else:
                return render(request, 'error.html', {'mensagem':"O arquivo de entrega da atividade deve ter menos de 10 MB."})
        else:
             return render(request, 'error.html', {'mensagem':"Atividade ou arquivo de entrega não encontrado."})
    else:
        return redirect('/index/')

def removerAtividade(request):
    if request.method == "POST":
        id_atividade = request.POST.get('id_atividade','')
        mensagem = "Atividade não encontrada! Entre em contato com os administradores do sistema."
        usuario = False
        atividade = False
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
def aprovarAtividade(request):
    if request.method == "POST":
        id_atividade = request.POST.get('id_atividade','')
        mensagem = "Atividade não encontrada! Entre em contato com os administradores do sistema."
        usuario = False
        atividade = False
        try:
            atividade = get_object_or_404(Atividade, pk=int(id_atividade))
        except:
            return JsonResponse({'mensagem': mensagem})
        if atividade != False:
            atividade.aprovado = True
            atividade.save()
            ### ENVIO DE EMAILS ###
            try:
                mensagem_email = u"A atividade "+atividade.titulo+" foi aprovada com sucesso.\n\n"+"Acesse o sistema utilizando o link: "+link_site+"."
                email = EmailMessage('Sistema Gerenciador de TCC', mensagem_email, to=[atividade.trabalho.aluno.email, atividade.trabalho.professor.email])
                email.send()
            except:
                print("Falha ao enviar o e-mail.")
            return JsonResponse({'mensagem': 'Atividade aprovada com sucesso!'})
    else:
        response = redirect('/index/')

def reprovarAtividade(request,pk):
    path = str(request.path)
    usuario = request.user
    try:
        atividade = get_object_or_404(Atividade, pk=int(pk))
    except:
        return render(request, 'error.html', {'mensagem':"Atividade não encontrada."})
    if request.method == "POST":
        observacoes = request.POST.get('observacoes','')
        mensagem = "Atividade não encontrada! Entre em contato com os administradores do sistema."
        if atividade != False and atividade.aprovado != True:
            mensagem_email = u"A atividade "+atividade.titulo+" foi reprovada.\n\nObservações do professor: \n"+observacoes+"\n\nAcesse o sistema utilizando o link: "+link_site+"."
            email = EmailMessage('Sistema Gerenciador de TCC', mensagem_email, to=[atividade.trabalho.aluno.email, atividade.trabalho.professor.email])
            if request.FILES:
                uploaded_file = request.FILES['file'] # file is the name value which you have provided in form for file field
                email.attach(uploaded_file.name, uploaded_file.read(), uploaded_file.content_type)
            email.send()
            return redirect('/trabalho/show/'+str(atividade.trabalho.pk)+'/')
        else:
            return redirect('/trabalho/show/'+str(atividade.trabalho.pk)+'/')
    else:
        return render(request, 'reprovar_atividade.html', {'path':path,'usuario':usuario,'atividade':atividade})

    
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
            try:
                ### ENVIO DE EMAILS ###
                mensagem_email = "\n\nUm trabalho foi cadastrado no Sistema Gerenciador de TCC com seu nome.\n\n"+"Acesse o sistema utilizando o link: " + link_site + "."
                email = EmailMessage('Sistema Gerenciador de TCC', mensagem_email, to=[Usuario.objects.filter(username=teste['aluno'])[0].email,Usuario.objects.filter(username=teste['professor'])[0].email])
                email.send()
            except:
                pass
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


def recuperar_senha(request):
    if request.method == "POST":
        username = request.POST.get('ra','')
        mensagem = "Usuário não encontrado! Verifique o RA/Matrícula e tente novamente."
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
    andamento = Trabalho.objects.all().filter(tipo="Andamento")
    pendente = Trabalho.objects.all().filter(tipo="Pendente")
    concluido = Trabalho.objects.all().filter(tipo="Concluido")
    try:
        if usuario_real != False:
            if request.session.get('perfil') == "Aluno":
                andamento = andamento.filter(aluno=usuario_real)
                concluido = concluido.filter(aluno=usuario_real)
            elif request.session.get('perfil') == "Professor":
                andamento = andamento.filter(aluno=usuario_real)
                concluido = concluido.filter(aluno=usuario_real)
    except:
        pass

    return render(request, 'index.html', {"usuario": usuario, "path": path,"andamento":andamento,"pendente":pendente,"concluido":concluido})
def pagina_erro(request,mensagem):
    return render(request, 'error.html', {'mensagem':mensagem}) 

def logout_act(request):
    logout(request)
    return HttpResponseRedirect('/login/')
