from django.urls import path, include
from . import views

app_name = 'audit'

urlpatterns = [
    path('', views.AuditMain.as_view(), name="audit"),
    path('user-category-form/', views.UserCategoryForm.as_view(), name="user_category_form"),
    path('user-subtheme-list/', views.UserSubthemeList.as_view(), name="user_subtheme_list"),
    path('question-form/<int:pk>/', views.AuditWizard.as_view(), name="question_form"),
    path('dashboard/', views.Dashboard.as_view(), name="dashboard"),
    path('dashboard/<int:pk>/', views.Dashboard.as_view(), name="dashboard"),
    path('recommendations/', views.Recomendations.as_view(), name="recommendations"),
    path('recommendations/<int:pk>/', views.Recomendations.as_view(), name="recommendations"),
    path('audit-settings/', views.AuditSettings.as_view(), name="audit_settings"),
]
