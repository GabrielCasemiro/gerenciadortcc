"""tcc URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from . import views

urlpatterns = [
    url(r'^logout', views.logout_act),
    url(r'^index', views.home),
    url(r'^usuario/list/', views.usuario_list),
    url(r'^usuario/add/', views.usuario_add),
    url(r'^usuario/excluir/', views.usuario_delete),
    url(r'^usuario/edit/(?P<username>\w+)/$', views.usuario_edit),
    url(r'^trabalho/add/', views.trabalho_add),
    url(r'^trabalho/edit/(?P<username>\w+)/$', views.trabalho_edit),
    url(r'^trabalho/excluir/', views.trabalho_delete),
    url(r'^trabalho/show/(?P<username>\w+)/$', views.trabalho_show),
    url(r'^atualizar_entrega/(?P<id_entrega>\w+)/$', views.entrega_tarefa),
    url(r'^download_entrega/(?P<id_entrega>\w+)/$', views.download_file),
    url(r'^login', views.login),
    url(r'^recuperar_senha/', views.recuperar_senha),
    url(r'^removerAtividade/', views.removerAtividade)
]
