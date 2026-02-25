from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views import View
from .models import UserCategory, Subthemes, Answer, QUESTION_TYPE, Score, Category, Question, Condition
from .forms import UserCategoryForm
from django.db import transaction
from collections import defaultdict
import json
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.contrib import messages
from django.utils import timezone
from django.conf import settings
from django.contrib.auth import authenticate, login, logout


class AuditMain(View):
    template_name = 'Audit/audit_main.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

class Login(View):
    template_name = 'Audit/login.html'
    success_url = "audit:audit"

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)
    
    def post(self, request, *args, **kwargs):
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect(self.success_url)
        else:
            messages.error(request, "Invalid username or password.")
            return render(request, self.template_name)

class Logout(View):
    success_url = "audit:audit"
    def get(self, request, *args, **kwargs):
        logout(request)
        return redirect(self.success_url)

class UserCategoryForm(LoginRequiredMixin, View):
    model = UserCategory
    form_class = UserCategoryForm
    template_name = 'Audit/categoryForm.html'
    success_url = 'audit:user_category_form'

    def get(self, request, *args, **kwargs):
        instance, created = UserCategory.objects.get_or_create(
            user=request.user
        )
        form = self.form_class(instance=instance)
        return render(request, self.template_name, {'form': form, 'created': created})
    
    def post(self, request, *args, **kwargs):
        instance, created = UserCategory.objects.get_or_create(
            user=request.user
        )
        form = self.form_class(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            return redirect(self.success_url)
        return render(request, self.template_name, {'form': form})

class UserSubthemeList(LoginRequiredMixin, View):
    model = UserCategory
    template_name = 'Audit/subtheme_list.html'

    def get(self, request, *args, **kwargs):
        context = {}
        try: context["auditTree"] = request.user.usercategory.auditTree
        except UserCategory.DoesNotExist: context["auditTree"] = None
        return render(request, self.template_name, context)

class AuditWizard(LoginRequiredMixin, View):
    model = Subthemes
    template_name = 'Audit/question_form.html'
    subtheme_url = 'audit:user_subtheme_list'
    dashboard_url = 'audit:dashboard'
    wizard_url = 'audit:question_form'

    def get(self, request, *args, **kwargs):
        subtheme = self.model.objects.get(id=kwargs.get("pk"))
        questions = subtheme.question_set.filter(condition__type__in=request.user.usercategory.category_set).distinct()
        form_question_groups = {}
        
        for q in questions:
            try: answer = Answer.objects.get(question=q, user=request.user).answer
            except Answer.DoesNotExist: answer = ""
            if not q.group in form_question_groups: form_question_groups[q.group] = {}
            form_question_groups[q.group][q] = answer
            print(q.group)
        context = {
            "QUESTION_TYPE": QUESTION_TYPE,
            "subtheme": subtheme,
            "form_question_groups": form_question_groups,
        }
        return render(request, self.template_name, context=context)
    
    def post(self, request, *args, **kwargs):
        with transaction.atomic():
            subtheme = self.model.objects.get(id=kwargs.get("pk"))
            questions = subtheme.question_set.filter(condition__type__in=request.user.usercategory.category_set).distinct()

            score_change: Category[dict] = defaultdict(dict)

            for question in questions:
                answer_value = request.POST.get(str(question.id))
                if answer_value is not None:
                    answer, created = Answer.objects.get_or_create(question=question, user=request.user)
                    answer.answer = answer_value
                    answer.save()
            if request.POST.get("action") == "dashboard":
                return redirect(self.dashboard_url)
            if request.POST.get("action") == "save":
                return redirect(self.wizard_url, pk=subtheme.id)
        return redirect(self.subtheme_url)

class Dashboard(LoginRequiredMixin, View):
    model = Category
    template_name = 'Audit/dashboard.html'

    def get(self, request, *args, **kwargs):
        if "pk" in kwargs:
            parent_category = self.model.objects.get(pk=kwargs.get("pk"))
            categories = parent_category.subcategories.all()
        else:
            parent_category = None
            categories = self.model.objects.filter(parent__isnull=True)
        
        scores = []
        subcategories = []
        for category in categories:
            score, create = Score.objects.get_or_create(user=request.user, category=category)
            score.save()
            if score.total > 0: scores.append(score)
            if category.subcategories.count() > 0:
                subcategories.append(category)
        chart = {
            "theta": [],
            "r": [],
        }
        for score in scores:
            val = score.true_percentage + score.mandatoryTrue_percentage
            chart["theta"].append(score.category.name + " " + str(round(val, 2)) + "%")
            chart["r"].append(val)
        if len(scores) < 3:
            chart = None
        else:
            chart = json.dumps(chart, ensure_ascii=False)

        context = {
            "back": parent_category,
            "subcategories": subcategories,
            "scores": scores,
            "chart": chart,
        }
        return render(request, self.template_name, context)

class Overview(LoginRequiredMixin, View):
    model = Category
    template_name = 'Audit/overview.html'

    def get(self, request, *args, **kwargs):
        if "pk" in kwargs:
            parent_category = self.model.objects.get(pk=kwargs.get("pk"))
            categories = parent_category.subcategories.all()
        else:
            parent_category = None
            categories = self.model.objects.filter(parent__isnull=True)
        
        subcategories = []
        if parent_category != None: category_list = [parent_category]
        else:
            category_list = categories
        conditions = Condition.objects.filter(type__in=category_list).distinct()
        answers = {}
        correct_answers = {}
        for condition in conditions:
            try: answer = Answer.objects.get(question=condition.question, user=request.user).answer
            except Answer.DoesNotExist: answer = None
            answers[condition] = answer
            if answer is not None: correct_answers[condition] = condition.check_value(answer)
            else: correct_answers[condition] = None
        conditions = sorted(conditions, key=lambda c: (c.required, not correct_answers[c] if correct_answers[c] is not None else -1), reverse=True)
        context = {
            "back": parent_category,
            "subcategories": categories,
            "conditions": conditions,
            "answers": answers,
            "QUESTION_TYPE": QUESTION_TYPE,
            "correct_answers": correct_answers,
        }

        return render(request, self.template_name, context)

class AuditSettings(LoginRequiredMixin, View):
    template_name = 'Audit/settings.html'

    def test_func(self):
        return self.request.user.is_superuser

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)
    
    def post(self, request, *args, **kwargs):
        if request.POST.get("action") == "delete_answers":
            Answer.objects.filter(user=request.user).delete()
        elif request.POST.get("action") == "update_score":
            delay = timezone.now() - request.user.usercategory.last_recalculated
            if delay.total_seconds() > settings.SCORE_UPDATE_DELAY:
                with transaction.atomic():
                    scores = defaultdict(dict)
                    stack = []
                    for answer in Answer.objects.filter(user=request.user):
                        score_change = answer.get_score_change()
                        for category, change in score_change.items():
                            if category not in scores:
                                scores[category] = {"true": 0, "false": 0, "mandatoryTrue": 0, "mandatoryFalse": 0}
                            for key in change:
                                scores[category][key] += change[key]
                            stack.append(category)
                    khan: dict[int] = defaultdict(int)
                    for category in Category.objects.all():
                        khan[category.pk] = category.subcategories.count()
                    checked_category = set()
                    while stack:
                        category = stack.pop()
                        if category in checked_category: continue
                        checked_category.add(category)

                        score, created = Score.objects.get_or_create(user=request.user, category=category)
                        score.update_total()
                        score.true = scores[category]["true"]
                        score.false = scores[category]["false"]
                        score.mandatoryTrue = scores[category]["mandatoryTrue"]
                        score.mandatoryFalse = scores[category]["mandatoryFalse"]
                        score.save()
                        if category.parent:
                            khan[category.parent.pk] -= 1
                            if khan[category.parent.pk] == 0: stack.append(category.parent)
                            if category.parent not in scores: scores[category.parent] = {"true": 0, "false": 0, "mandatoryTrue": 0, "mandatoryFalse": 0}
                            for key in scores[category]:
                                scores[category.parent][key] += scores[category][key]
                request.user.usercategory.last_recalculated = timezone.now()
                request.user.usercategory.save()
            else:
                messages.add_message(request, messages.WARNING, f"You can only update scores every 5 minutes. Please wait before trying again. Time remaining: {int(settings.SCORE_UPDATE_DELAY - delay.total_seconds())} seconds.")
                
        return redirect('audit:audit_settings')
