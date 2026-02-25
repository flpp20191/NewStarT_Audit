from django.contrib.auth.models import User
from django.db import models
from django.db import transaction
from collections import defaultdict
from django.db.models.signals import pre_delete
from django.dispatch import receiver

# from Wizard.models import *
from enum import Enum

# ------------------------------------------------------
# Audit
# ------------------------------------------------------

class QUESTION_TYPE(models.TextChoices):
    YES_NO = "yes_no", "Yes/No", 
    INTERVAL = "interval", "Interval",
    LIKERTA = "likert", "Likerta"

class Category(models.Model):
    name = models.CharField(max_length=500)
    total = models.IntegerField(default=0)
    iri = models.TextField(blank=True, null=True)
    description = models.TextField(default=None, null=True, blank=True)
    parent = models.ForeignKey('Category', on_delete=models.CASCADE, blank=True, null=True, default=None, related_name="subcategories")
    depth = models.PositiveIntegerField(default=0, null=True, blank=True)
    order = models.PositiveIntegerField(default=0, null=True, blank=True)

    @property
    def Name(self):
        # return self._name
        return self.name
    
    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.Name

    # icon = models.FilePathField(path=images_path, default=None, null=True, blank=True)
    # repeatIcon = models.IntegerField(blank=None, null=True, default=1)

    # selectable = models.BooleanField(default=False, null=True)
    # hasQuestions = models.BooleanField(default=False, null=True)

    # userSelected = models.ForeignKey('Category', on_delete=models.CASCADE, blank=True, null=True, default=None)
    # pages = models.ForeignKey('Category', on_delete=models.CASCADE, blank=True, null=True, default=None, related_name="type_pages")
    
    # def subtype_set_selectable(self):
    #     def sort_ascending(val):
    #         roman_nr = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5}
    #         nr = val._name.split(" ")
    #         for x in range(len(nr)):
    #             if nr[x] in roman_nr:
    #                 nr[x] = roman_nr[nr[x]]
    #         return str(nr)
    #     val = sorted(self.subtype_set.filter(selectable=True), key=sort_ascending)
    #     return val


class Subthemes(models.Model):
    iri = models.TextField(blank=True, null=True)
    subtheme = models.ManyToManyField(
        "Subthemes",
        default=None,
        blank=True,
        related_name="subthemes",
    )
    
    type = models.ManyToManyField(Category, related_name="subtheme_type")
    # mainType = models.ManyToManyField(Category, related_name="subtheme_mainType")

    name = models.CharField(max_length=200, default=None, null=True)
    description = models.TextField(null=True, blank=True)

class Condition(models.Model):
    question = models.ForeignKey("Question", on_delete=models.CASCADE, related_name="condition_question")
    type = models.ForeignKey(Category, on_delete=models.CASCADE, default=None, related_name="type_question_set")
    min = models.FloatField(null=True, blank=True)
    max = models.FloatField(null=True, blank=True)

    inverse = models.BooleanField(default=False)
    required = models.BooleanField(default=False)

    def check_in_interval(self, answer_value: float):
        interval = True
        if self.min != None: interval = False if self.min < answer_value else interval 
        if self.max != None: interval = False if answer_value < self.max else interval
        interval ^= not self.inverse
        return interval

    def check_value(self, ansewer_value):
        try:
            if self.question.answerType == QUESTION_TYPE.YES_NO:
                if (ansewer_value == "true") ^ self.inverse:
                    return True
                elif (ansewer_value == "false") ^ self.inverse:
                    return False
            elif self.question.answerType == QUESTION_TYPE.LIKERTA:
                return self.check_in_interval(self.question.likerta.index(ansewer_value))
            elif self.question.answerType == QUESTION_TYPE.INTERVAL:
                return self.check_in_interval(float(ansewer_value))
        except ValueError: pass
        return False

class Question(models.Model):
    iri = models.TextField(blank=True, null=True)

    question = models.TextField(default=None, null=True)
    weight = models.FloatField(default=1, null=True)
    
    group = models.CharField(default="", null=True, max_length=256)
    hint = models.CharField(default="", null=True, max_length=256)
    answerType = models.CharField(max_length=50, choices=QUESTION_TYPE.choices, default=QUESTION_TYPE.YES_NO)
    subtheme = models.ManyToManyField(Subthemes, related_name="question_set")
    condition = models.ManyToManyField(Condition, default=None, related_name="condition_set")
    
    likerta = models.JSONField(null=True, blank=True)
    
    # hint = models.CharField(max_length=50, default="", blank=True, null=True)

    # changed = models.BooleanField(default=False, null=True)

    # notAllowedQuestion = models.ManyToManyField('AbstractQuestion', blank=True, related_name="ignore_question")

    # def save(self, *args, **kwargs):
    #     self.changed = True
    #     super(Question, self).save(*args, **kwargs)

    def __str__(self):
        return str(self.question)

class Score(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name="category_score")
    category = models.ForeignKey(Category, null=True, on_delete=models.CASCADE, related_name="question_answer")

    total = models.FloatField(default=0)

    mandatoryTrue = models.FloatField(default=0)
    mandatoryFalse = models.FloatField(default=0)
    true = models.FloatField(default=0)
    false = models.FloatField(default=0)
    @property
    def unanswered(self) -> float:
        return self.total - self.mandatoryTrue - self.mandatoryFalse - self.true - self.false

    @property
    def mandatoryTrue_percentage(self) -> float:
        if self.total == 0: return 0
        return round(self.mandatoryTrue / self.total * 100, 2)
    @property
    def mandatoryFalse_percentage(self) -> float:
        if self.total == 0: return 0
        return round(self.mandatoryFalse / self.total * 100, 2)
    @property
    def true_percentage(self) -> float:
        if self.total == 0: return 0
        return round(self.true / self.total * 100, 2)
    @property
    def false_percentage(self) -> float:
        if self.total == 0: return 0
        return round(self.false / self.total * 100, 2)
    @property
    def unanswered_percentage(self) -> float:
        if self.total == 0: return 0
        return round(self.unanswered / self.total * 100, 2)
    # @property
    # def mandatoryUnanswered_percentage(self) -> float:
    #     if self.total == 0: return 0
    #     return self.mandatoryUnanswered() / self.total * 100

    class Meta:
        unique_together = ('user', 'category')
    
    def mandatoryUnanswered(self) -> float:
        return self.total - self.mandatoryTrue - self.mandatoryFalse - self.true - self.false

    def update_total(self, commit=True):
        self.total = 0
        stack = [self.category]
        while stack:
            current = stack.pop()
            self.total += sum([x.question.weight for x in current.type_question_set.all()])
            for category in current.subcategories.all():
                stack.append(category)
        if commit: self.save()

    def save(self, *args, **kwargs):
        if not self.pk:
            self.update_total(commit=False)
        super(Score, self).save(*args, **kwargs)

class Answer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=None, null=True)
    answer = models.TextField(default="", null=True)
    question = models.ForeignKey(Question, null=True, on_delete=models.CASCADE, related_name="question_answer")

    def save(self, *args, **kwargs):
        with transaction.atomic():
            old_answer = None
            if self.pk:
                old_answer = Answer.objects.get(pk=self.pk)
            if old_answer and old_answer.answer == self.answer: return

            old_score_change = old_answer.get_score_change() if old_answer else defaultdict(dict)
            new_score_change = self.get_score_change()

            stack = [(category, old_score_change[category], new_score_change[category]) for category in Category.objects.filter(type_question_set__question=self.question).distinct()]

            while stack:
                category, old_score, new_score = stack.pop()
                score, created = Score.objects.get_or_create(user=self.user, category=category)
                for key in ["mandatoryTrue", "mandatoryFalse", "true", "false"]:
                    score.__dict__[key] += new_score.get(key, 0) - old_score.get(key, 0)
                score.save()
                if category.parent:
                    stack.append((category.parent, old_score, new_score))

        return super(Answer, self).save(*args, **kwargs)
    
    def delete_score(self):
        with transaction.atomic():
            score_change = self.get_score_change()
            stack = [(category, score_change[category]) for category in Category.objects.filter(type_question_set__question=self.question).distinct()]
            while stack:
                category, score_change = stack.pop()
                score = Score.objects.get(user=self.user, category=category)
                for key in ["mandatoryTrue", "mandatoryFalse", "true", "false"]:
                    score.__dict__[key] -= score_change.get(key, 0)
                score.save()
                if category.parent:
                    stack.append((category.parent, score_change))
    
    def get_score_change(self) -> dict:
        score = defaultdict(dict)

        condition: Condition
        for condition in self.question.condition.all():
            if not condition.type in score:
                score[condition.type] = {"mandatoryTrue": 0, "mandatoryFalse": 0, "true": 0, "false": 0}
            t, f = 0, 0
            if self.question.answerType == QUESTION_TYPE.YES_NO:
                if (self.answer == "true") ^ condition.inverse:
                    t += 1
                elif (self.answer == "false") ^ condition.inverse:
                    f += 1
            elif self.question.answerType == QUESTION_TYPE.LIKERTA:
                try:
                    if condition.check_in_interval(float(self.question.likerta.index(self.answer))):
                        t += 1
                    else:
                        f += 1
                except ValueError:
                    pass
            elif self.question.answerType == QUESTION_TYPE.INTERVAL:
                try:
                    if condition.check_in_interval(float(self.answer)):
                        t += 1
                    else:
                        f += 1
                except ValueError:
                    pass
            if condition.required:
                score[condition.type]["mandatoryTrue"] += t
                score[condition.type]["mandatoryFalse"] += f
            else:
                score[condition.type]["true"] += t
                score[condition.type]["false"] += f
        return score

@receiver(pre_delete, sender=Answer)
def before_delete(sender, instance: Answer, **kwargs):
    instance.delete_score()

class UserCategory(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    category = models.ManyToManyField(Category, blank=True, default=None, related_name="user_category")

    _audit_tree = models.JSONField(null=True)
    last_recalculated = models.DateTimeField(auto_now=True)

    @property
    def category_set(self) -> set:
        category_set = set()
        stack = list(self.category.all())
        while stack:
            current: Subthemes = stack.pop()
            if current not in category_set:
                category_set.add(current)
                stack.extend(current.subcategories.all())
        return category_set

    @property
    def auditTree(self):
        if self._audit_tree == None:
            self._audit_tree = get_user_audit_tree(self)
            # self.save()
        return self._audit_tree
    
def get_user_audit_tree(self: UserCategory) -> dict:
    category_set = self.category_set
    
    audit_tree = defaultdict(dict)
    stack = [(audit_tree[x.iri], x) for x in Subthemes.objects.filter(subtheme__isnull=True, type__in=category_set).distinct()]
    while stack:
        _dict, current_level = stack.pop()
        _dict["subthemes"] = {}
        _dict["name"] = current_level.name
        _dict["pk"] = current_level.pk
        _dict["questions"] = current_level.question_set.count() > 0
        for subtheme in current_level.subthemes.filter(type__in=category_set).distinct(): #filter(type__in=category_set)
            _dict["subthemes"][subtheme.iri] = {}
            stack.append((_dict["subthemes"][subtheme.iri], subtheme))
    return audit_tree
