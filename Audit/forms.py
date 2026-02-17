from django import forms
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe
from .models import Category, UserCategory
from django.forms.widgets import SelectMultiple

# from django.utils.translation import gettext_lazy as _

class MultiSelect(SelectMultiple):
    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(
            name, value, label, selected, index, subindex=subindex, attrs=attrs
        )

        # value.instance is available for ModelChoiceField
        if hasattr(value, "instance"):
            obj = value.instance
            option["attrs"].update({
                "data-depth": obj.depth,
                "data-parent": obj.parent_id or "",
            })

        return option

class UserCategoryForm(forms.ModelForm):
    class Meta:
        model = UserCategory
        fields = [
            'category',
        ]
        labels = {
            'category': 'Categories',
        }
        widgets = {
            'category': MultiSelect(attrs={'class': 'form-control'}),
        }

# class CategorySelect(forms.Select):
#     def __init__(self, attrs=None, choices=()):
#         attrs = attrs or {}
#         attrs.setdefault("id", "category-select")
#         attrs.setdefault("class", "form-control")
#         super().__init__(attrs=attrs, choices=choices)
      
#     def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
#         option = super().create_option(name, value, label, selected, index, subindex=subindex, attrs=attrs)
#         # Add a class to each <option>
#         if value:
#             try:
#                 try:
#                   obj = CategoryTemplate.objects.get(pk=value)
#                 except TypeError:
#                   obj = self.choices.queryset.get(pk=getattr(value, 'value', value) )
                
#                 option['attrs']['class'] = 'category-select-indent-' + str(obj.depth)
#                 if obj.parent != None:
#                   option['attrs']['class'] += ' parent-category-' + str(obj.parent.pk)
#                 if obj.subcategories.all().count() == 0:
#                   option['attrs']['class'] += ' lowest-category' 
#             except self.choices.queryset.model.DoesNotExist:
#                 pass
            
#         # print(option)

#         return option

# class AdvertisementForm(forms.ModelForm):
#     class Meta:
#         model = Advertisement
#         fields = [
#             'name_lv',
#             'name_en',
#             'main_info_lv',
#             'main_info_en',
#             'region',
#             'category',
#             'description_lv',
#             'description_en',
#             'image',
#             'price',
#             'e_mail',
#             'phone_number'
#         ]
#         labels = {
#             'name_lv': _('i18n.advertisement.form.name_lv'),
#             'name_en': _('i18n.advertisement.form.name_en'),
#             'main_info_lv': _('i18n.advertisement.form.main_info_lv'),
#             'main_info_en': _('i18n.advertisement.form.main_info_en'),
#             'region': _('i18n.advertisement.form.region'),
#             'category': _('i18n.advertisement.form.category'),
#             'description_lv': _('i18n.advertisement.form.description_lv'),
#             'description_en': _('i18n.advertisement.form.description_en'),
#             'image': _('i18n.advertisement.form.image'),
#             'price': _('i18n.advertisement.form.price'),
#             'e_mail': _('i18n.advertisement.form.e_mail'),
#             'phone_number': _('i18n.advertisement.form.phone_number'),
#         }
#         widgets = {
#             'region': RegionSelect(attrs={'class': 'form-control', 'id': 'region-select', 'tr_class': 'required'}),
#             'category': CategorySelect(attrs={'required': False}),
#             'name_lv': forms.TextInput(attrs={'class': 'form-control', 'tr_class': 'required'}),
#             'name_en': forms.TextInput(attrs={'class': 'form-control', 'tr_class': 'required'}),
#             'main_info_lv': forms.Textarea(attrs={'class': 'form-control', 'tr_class': 'required'}),
#             'main_info_en': forms.Textarea(attrs={'class': 'form-control', 'tr_class': 'required'}),
#             'description_lv': forms.Textarea(attrs={'class': 'form-control ad_changable', 'tr_class': 'd-none'}),
#             'description_en': forms.Textarea(attrs={'class': 'form-control ad_changable', 'tr_class': 'd-none'}),
#             'image': forms.ClearableFileInput(attrs={'class': 'ad_changable', 'tr_class': 'd-none'}),
#             'price': forms.NumberInput(attrs={'class': 'form-control ad_changable', 'tr_class': 'd-none'}),
#             'e_mail': forms.EmailInput(attrs={'class': 'form-control ad_changable', 'tr_class': 'd-none'}),
#             'phone_number': forms.TextInput(attrs={'class': 'form-control ad_changable', 'tr_class': 'd-none'}),
#         }

#         help_texts = {
#             'image': 'Max 1.5MB',
#         }

#     def clean(self):
#         cleaned = super().clean()

#         category: CategoryTemplate = cleaned['category']
#         while category.parent:
#             category = category.parent

#         if not category.visibility in ["ad", "both"] or not category.ad_type.public: 
#             self.add_error("category", _("Atlasītā kategorija nav publiski redzama"))

#         if cleaned['category'].subcategories.all().count() > 0:
#             self.add_error("category", _("Atlasītā kategorija \"%(category)s\" nav zemākā līmeņa kategorija") % {
#                 "category": cleaned['category'].name
#             })

#         data = {}
#         can_submit = True
#         for extra_field in category.ad_type.other_fields.all():
#             if extra_field.input_type == "input":
#                 for lang in ["_lv", "_en"]:
#                     if "extra_field_" + str(extra_field.id) + lang in self.request.POST:
#                         val = self.request.POST["extra_field_" + str(extra_field.id) + lang]
#                         if not extra_field.regex in [None, ""]:
#                             if not re.search(extra_field.regex, val):
#                                 msg = _("Lauka \"%(field)s\" vērtība \"%(value)s\" neatbilst izteiksmei \"%(regex)s\"") % {
#                                     "field": extra_field.name,
#                                     "value": val,
#                                     "regex": extra_field.regex,
#                                 }
#                                 self.add_error("category", msg)
#                     can_submit = False
#                     data[extra_field.id] = {
#                         "lv": self.request.POST["extra_field_" + str(extra_field.id) + "_lv"],
#                         "en": self.request.POST["extra_field_" + str(extra_field.id) + "_en"],
#                     }
#             elif extra_field.input_type == "textarea":
#                 data[extra_field.id] = {
#                     "lv": self.request.POST["extra_field_" + str(extra_field.id) + "_lv"],
#                     "en": self.request.POST["extra_field_" + str(extra_field.id) + "_en"],
#                 }
#             else:
#                 try:
#                     data[extra_field.id] = self.request.POST["extra_field_" + str(extra_field.id)]
#                 except:
#                     data[extra_field.id] = ""
        
#         if not can_submit:
#             self.request.session["ad_form_data"] = data

#         cleaned["data"] = data

#         return cleaned

#     def as_table(self):
#         rows = []
#         for bound_field in self.visible_fields():
#             tr_class = ""
#             tr_class = bound_field.field.widget.attrs.get('tr_class','')

#             errors_html = ""
#             if bound_field.errors:
#                 errors_html = f'<ul class="errorlist">{"".join(f"<li>{e}</li>" for e in bound_field.errors)}</ul>'

#             if bound_field.name in ["image"]:
#                 rows.append(f'<tr class="{tr_class}"><th>{bound_field.label_tag()}<br><span class="text-muted" style="font-size:0.85rem; font-weight: normal"><i>Max 1.5MB</i></span></th><td>{bound_field}{errors_html}</td></tr>')
#             else:
#                 rows.append(f'<tr class="{tr_class}"><th>{bound_field.label_tag()}</th><td>{bound_field}{errors_html}</td></tr>')
#         return mark_safe('\n'.join(rows))

#     def __init__(self, *args, **kwargs):
#         self.request = kwargs.pop('request', None)
#         super().__init__(*args, **kwargs)
#         self.fields["region"].queryset = Region.hierarchy()
#         self.fields['category'].queryset = CategoryTemplate.hierarchy(visibility=["ad", "both"])
#         if self.data:
#           self.data = self.data.copy()

#           if "region[]" in self.data:
#             self.data["region"] = self.data["region[]"]
#           if "category[]" in self.data:
#             self.data["category"] = self.data["category[]"]
    
#     def save(self, commit=True):
#         obj = super().save(commit=False)

#         obj.data = self.cleaned_data.get("data", {})

#         if commit:
#             obj.save()

#         return obj

# class CategoryTemplateVisibilityForm(forms.ModelForm):
#     class Meta:
#         model = CategoryTemplate
#         fields = [
#             'visibility',
#         ]
#         labels = {
#             'visibility': _('i18n.category_template.form.visibility'),
#         }
#         widgets = {
#             'visibility': forms.Select(attrs={'class': 'form-control'}),
#         }

#     def clean_is_hidden(self):
#         """Prevent owners from making blocked advertisements visible."""
#         is_hidden = self.cleaned_data.get('is_hidden')
#         instance = self.instance

#         # Check if trying to make advertisement visible (is_hidden=False) when blocked by admin
#         if instance and instance.pk and not is_hidden:
#             from reports.models import ReportThread
#             from django.contrib.contenttypes.models import ContentType

#             ct = ContentType.objects.get_for_model(Advertisement)
#             active_blocked_thread = ReportThread.objects.filter(
#                 content_type=ct,
#                 object_id=instance.pk,
#                 item_blocked=True,
#                 status__in=['item_blocked', 'restoration_requested', 'rejected']
#             ).first()

#             if active_blocked_thread:
#                 raise ValidationError(
#                     _('i18n.advertisement.form.error.blocked_by_admin'),
#                     code='blocked'
#                 )

#         return is_hidden

# class AdvertisementTimeForm(forms.ModelForm):
#     class Meta:
#         model = Advertisement
#         fields = [
#             'publish_start',
#             'publish_end',
#         ]
#         labels = {
#             'publish_start': _('i18n.advertisement.form.publish_start'),
#             'publish_end': _('i18n.advertisement.form.publish_end'),
#         }
#         widgets = {
#             'publish_start': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
#             'publish_end': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
#         }
    
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.fields['publish_start'].required = True
#         self.fields['publish_end'].required = True
    
#     def clean(self):
#         cleaned_data = super().clean()

#         start = cleaned_data.get('publish_start')
#         end = cleaned_data.get('publish_end')

#         # If either field failed validation already
#         if not start or not end:
#             return cleaned_data

#         # End must be after start
#         if end <= start:
#             raise ValidationError({
#                 'publish_end': _('End time must be after start time.')
#             })

#         duration = end - start

#         if duration < AdDuration.objects.first().duration_min:
#             raise ValidationError({
#                 'publish_start': _('Minimum duration is %(min)s.') % {'min': AdDuration.objects.first().duration_min_str}
#             })

#         if duration > AdDuration.objects.first().duration_max:
#             raise ValidationError({
#                 'publish_end': _('Maximum duration is %(min)s.') % {'min': AdDuration.objects.first().duration_max_str}
#             })

#         return cleaned_data
