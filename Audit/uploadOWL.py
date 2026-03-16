from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from Audit.models import QUESTION_TYPE, Category, Subthemes, Question, Condition, OWL_Upload_Configs
from owlready2 import *
from collections import defaultdict
from django.contrib import messages
import yaml

"""
Usage:
    python manage.py uploadOwl --filepath NewStarT.owl --language en
    python manage.py uploadOwl --filepath NewStarT.owl --language en --conf conf.yml
    python manage.py uploadOwl --filepath NewStarT.owl --language en --make_config --config_filename conf_output.yml
    python manage.py uploadOwl --filepath Example/NewStarT.owl --language en --make_config --config_filename Example/conf_output.yml --conf Example/conf.yml

This command is safe to run multiple times - it will:
- Update relationships between data using existing IRIs
- Make configurations for furure updates (IF IRIs DO NOT CHANGE) to make future updates faster and not require user input

"""

def get_label(entity, language="en"):
    for label in entity.label:
        try:
            if label.lang == language:
                return label
        except:
            CMD_LIGHT_GREY = "\033[0;30m"
            CMD_RESET = "\033[0m"
            print(f"{CMD_LIGHT_GREY}No translation for '{language}': {entity}, {CMD_RESET}")
            return label
    return ""

def uploadOWL(request, ontology_path, conf="", make_config=False):
    CONFIGS = yaml.safe_load(conf)

    world = World()
    ontology = owlready2.get_ontology(ontology_path).load(reload=True)

    QUESTION_TYPE_LIST = QUESTION_TYPE.choices
    OBJECT_PROPERTIES = list(ontology.object_properties())
    DATA_PROPERTIES = list(ontology.data_properties())
    USED_OBJECT_PROPERTIES = set()
    USED_DATA_PROPERTIES = set()

    LANGUAGE = "en"
    HAS_CATEGORY: set = None
    HAS_QUESTION_TYPE: bool = None
    DEFAULT_ANSWER_TYPE: QUESTION_TYPE = None
    USED_ANSWER_TYPES: set[QUESTION_TYPE] = set()
    QUESTION_TYPE_PROPERIES: set = None
    ANSWER_TYPE_MAP: dict = None
    LIKERT_CHOICES: set = None
    LIKERT_CHOICE_SEPERATOR: str = None
    LIKERT_ANSWER_PROPERTY: set = None
    MANDATORY_QUESTIONS: set = None

    MIN_RANGE: set = None
    MAX_RANGE: set = None

    HAS_GROUP: set = None
    HAS_HINT_TEXT: set = None
    
    if CONFIGS:
        LANGUAGE = CONFIGS["LANGUAGE"] if "LANGUAGE" in CONFIGS else "en"
        HAS_CATEGORY = set(ontology.search(iri=iri)[0] for iri in CONFIGS["HAS_CATEGORY"]) if "HAS_CATEGORY" in CONFIGS else HAS_CATEGORY
        HAS_GROUP = set(ontology.search(iri=iri)[0] for iri in CONFIGS["HAS_GROUP"]) if "HAS_GROUP" in CONFIGS else HAS_GROUP
        HAS_HINT_TEXT = set(ontology.search(iri=iri)[0] for iri in CONFIGS["HAS_HINT_TEXT"]) if "HAS_HINT_TEXT" in CONFIGS else HAS_HINT_TEXT
        HAS_QUESTION_TYPE = CONFIGS["HAS_QUESTION_TYPE"] if "HAS_QUESTION_TYPE" in CONFIGS else None
        if "QUESTION_TYPE" in CONFIGS:
            MANDATORY_QUESTIONS = set(ontology.search(iri=iri)[0] for iri in CONFIGS["QUESTION_TYPE"]["MANDATORY"]) if "MANDATORY" in CONFIGS["QUESTION_TYPE"] else None

        if HAS_QUESTION_TYPE and "QUESTION_TYPE" in CONFIGS:
            if "QUESTION_TYPE" in CONFIGS and "PROPERTIES" in CONFIGS["QUESTION_TYPE"]:
                QUESTION_TYPE_PROPERIES = set()
                for iri in CONFIGS["QUESTION_TYPE"]["PROPERTIES"]:
                    QUESTION_TYPE_PROPERIES.add(ontology.search(iri=iri)[0])
            else:
                QUESTION_TYPE_PROPERIES = None
            
            if "TYPES" in CONFIGS["QUESTION_TYPE"]:
                ANSWER_TYPE_MAP = {}
                for x in CONFIGS["QUESTION_TYPE"]["TYPES"]:
                    USED_ANSWER_TYPES.add(x)
                    for iri in CONFIGS["QUESTION_TYPE"]["TYPES"][x]:
                        ANSWER_TYPE_MAP[ontology.search(iri=iri)[0]] = x
        else:
            DEFAULT_ANSWER_TYPE = CONFIGS["DEFAULT_ANSWER_TYPE"] if "DEFAULT_ANSWER_TYPE" in CONFIGS else DEFAULT_ANSWER_TYPE
            USED_ANSWER_TYPES.add(DEFAULT_ANSWER_TYPE)
        
        if QUESTION_TYPE.LIKERTA in USED_ANSWER_TYPES and "QUESTION_TYPE" in CONFIGS and "LIKERT" in CONFIGS["QUESTION_TYPE"]:
            LIKERT_CHOICES = set(ontology.search(iri=iri)[0] for iri in CONFIGS["QUESTION_TYPE"]["LIKERT"]["LIKERT_CHOICES"]) if "LIKERT_CHOICES" in CONFIGS["QUESTION_TYPE"]["LIKERT"] else None
            LIKERT_ANSWER_PROPERTY = set(ontology.search(iri=iri)[0] for iri in CONFIGS["QUESTION_TYPE"]["LIKERT"]["LIKERT_ANSWER_PROPERTY"]) if "LIKERT_ANSWER_PROPERTY" in CONFIGS["QUESTION_TYPE"]["LIKERT"] else None
            LIKERT_CHOICE_SEPERATOR = CONFIGS["QUESTION_TYPE"]["LIKERT"]["SEPERATOR"] if "SEPERATOR" in CONFIGS["QUESTION_TYPE"]["LIKERT"] else None
            LIKERT_CHOICE_SEPERATOR = LIKERT_CHOICE_SEPERATOR.encode("utf-8").decode("unicode_escape")
        if QUESTION_TYPE.INTERVAL in USED_ANSWER_TYPES and "QUESTION_TYPE" in CONFIGS and "INTERVAL" in CONFIGS["QUESTION_TYPE"]:
            MAX_RANGE = set(ontology.search(iri=iri)[0] for iri in CONFIGS["QUESTION_TYPE"]["INTERVAL"]["MAX"]) if "MAX" in CONFIGS["QUESTION_TYPE"]["INTERVAL"] else MAX_RANGE
            MIN_RANGE = set(ontology.search(iri=iri)[0] for iri in CONFIGS["QUESTION_TYPE"]["INTERVAL"]["MIN"]) if "MIN" in CONFIGS["QUESTION_TYPE"]["INTERVAL"] else MIN_RANGE
    
    CATEGORY_SET = set()
    for cls in ontology.classes():
        for restriction in cls.is_a:
            if 'and' in restriction.__class__.__name__.lower():
                for part in restriction.is_a:
                    if hasattr(part, "property") and part.property in HAS_CATEGORY:
                        CATEGORY_SET.add(part.value)
                continue
            elif hasattr(restriction, "property") and restriction.property in HAS_CATEGORY:
                CATEGORY_SET.add(restriction.value)

    stack = list(CATEGORY_SET)
    while stack:
        val = stack.pop()
        for parent in val.is_a:
            if not parent in CATEGORY_SET:
                CATEGORY_SET.add(parent)
                stack.append(parent)
    CATEGORY_SET.remove(Thing)

    CATEGORY_PARENT_MAP = {}
    for category_entity in CATEGORY_SET:
        for superclass in category_entity.is_a:
            if superclass in CATEGORY_SET:
                CATEGORY_PARENT_MAP[category_entity] = superclass

    if HAS_QUESTION_TYPE:
        QUESTION_SET = set()

        uniqueAnswerTypes = set()
        for cls in ontology.classes():
            for restriction in cls.is_a:
                if hasattr(restriction, "property") and restriction.property in QUESTION_TYPE_PROPERIES:
                    uniqueAnswerTypes.add(restriction.value)
                    QUESTION_SET.add(cls)
    else:
        QUESTION_SET = set()
        for cls in ontology.classes():
            for restriction in cls.is_a:
                if 'and' in restriction.__class__.__name__.lower():
                    for part in restriction.is_a:
                        if hasattr(part, "property") and part.property in HAS_CATEGORY:
                            QUESTION_SET.add(cls)
                    continue
                elif hasattr(restriction, "property") and restriction.property in HAS_CATEGORY:
                    QUESTION_SET.add(cls)

    _created_categories, _updated_categories = 0, 0
    _created_question, _updated_question = 0, 0
    _created_question_category_condition = 0
    _created_subthemes, _updated_subthemes = 0, 0

    success = True
    with transaction.atomic():
        try:
            for category_entity in CATEGORY_SET:
                category_name = get_label(category_entity, LANGUAGE)
                category_obj, created = Category.objects.get_or_create(iri=category_entity.iri)
                category_obj.name = category_name
                category_obj.parent = None
                category_obj.save()
                if created:
                    _created_categories += 1
                else:
                    _updated_categories += 1
            for category_entity, parent_entity in CATEGORY_PARENT_MAP.items():
                category_obj = Category.objects.get(iri=category_entity.iri)
                parent_obj = Category.objects.get(iri=parent_entity.iri)
                category_obj.parent = parent_obj
                category_obj.save()
            
            stack = []
            for cat in Thing.subclasses():
                if cat in CATEGORY_SET and cat not in CATEGORY_PARENT_MAP:
                    stack.append((Category.objects.get(iri=cat.iri), 0))
            
            order = 0
            while stack:
                current_cat, depth = stack.pop()
                current_cat.order = order
                current_cat.depth = depth
                current_cat.save()
                subcats = Category.objects.filter(parent=current_cat).order_by('-name')
                for subcat in subcats:
                    stack.append((subcat, depth + 1))
                order += 1

            messages.add_message(request, messages.INFO, "Found categories succesfully.")
        except:
            messages.add_message(request, messages.ERROR, "Error creating categories. Make sure the ontology is valid and matches the configuration.")
            success = False
            raise ValueError("Abort transaction")
        try:
            SUBTHEME_MAP = defaultdict(list)
            SUBTHEME_SET = []

            for question in QUESTION_SET:
                question_text = get_label(question, LANGUAGE)
                question_obj, created = Question.objects.get_or_create(iri=question.iri)
                question_obj.question = question_text
                if not created:
                    question_obj.hint = ""
                    question_obj.group = ""
                if HAS_QUESTION_TYPE:
                    for restriction in question.is_a:
                        if hasattr(restriction, "property") and restriction.property in QUESTION_TYPE_PROPERIES:
                            answer_type = ANSWER_TYPE_MAP.get(restriction.value, QUESTION_TYPE.YES_NO)
                            question_obj.answerType = answer_type
                        if hasattr(restriction, "property") and restriction.property in HAS_GROUP:
                            question_obj.group = get_label(restriction.value, LANGUAGE)
                        if hasattr(restriction, "property") and restriction.property in HAS_HINT_TEXT:
                            question_obj.hint = get_label(restriction.value, LANGUAGE)
                else:
                    question_obj.answerType = DEFAULT_ANSWER_TYPE

                question_obj.save()
                if created:
                    _created_question += 1
                else:
                    _updated_question += 1
                    for x in question_obj.condition.all(): x.delete()

                if question_obj.answerType == QUESTION_TYPE.LIKERTA:
                    LIKERT_ANSWERS: list[str] = []
                    LIKERT_ANSWER_RANGE = {}
                    for restriction in question.is_a:
                        if hasattr(restriction, "property") and restriction.property in LIKERT_CHOICES:
                            answer_set: list[str] = restriction.value.split(LIKERT_CHOICE_SEPERATOR)
                            LIKERT_ANSWER_RANGE[restriction.property] = (len(LIKERT_ANSWERS), len(LIKERT_ANSWERS)+len(answer_set))
                            for i in range(len(LIKERT_ANSWERS), len(LIKERT_ANSWERS)+len(answer_set)):
                                LIKERT_ANSWER_RANGE[i] = len(LIKERT_ANSWERS)+len(answer_set)-1
                            LIKERT_ANSWERS.extend(answer_set)

                    question_obj.likerta = LIKERT_ANSWERS

                for restriction in question.is_a:
                    condition = Condition(question=question_obj)
                    if 'not' in part.__class__.__name__.lower():
                        restriction = restriction.Class
                        condition.inverse = True
                    if 'and' in restriction.__class__.__name__.lower():
                        for part in restriction.is_a:
                            if 'not' in part.__class__.__name__.lower():
                                part = part.Class
                                condition.inverse = True
                            if hasattr(part, "property") and part.property in HAS_CATEGORY:
                                category_obj = Category.objects.get(iri=part.value.iri)
                                condition.type = category_obj
                            if hasattr(part, "property") and part.property in MANDATORY_QUESTIONS:
                                condition.required = bool(part.value)
                            if QUESTION_TYPE.LIKERTA == question_obj.answerType:
                                if hasattr(part, "property") and part.property in LIKERT_ANSWER_PROPERTY:
                                    condition.min = LIKERT_ANSWERS.index(part.value)
                                    condition.max = LIKERT_ANSWER_RANGE[condition.min]
                            if QUESTION_TYPE.INTERVAL == question_obj.answerType:
                                if hasattr(part, "property") and part.property in MIN_RANGE:
                                    condition.min = float(part.value)
                                if hasattr(part, "property") and part.property in MAX_RANGE:
                                    condition.max = float(part.value)
                    elif hasattr(restriction, "property") and restriction.property in HAS_CATEGORY:
                        category_obj = Category.objects.get(iri=restriction.value.iri)
                        condition.type = category_obj
                    elif isinstance(restriction, ThingClass):
                        SUBTHEME_MAP[restriction].append(question_obj)
                        SUBTHEME_SET.append(restriction)
                    
                    try:
                        condition.type
                        condition.save()
                        question_obj.condition.add(condition)
                        _created_question_category_condition += 1
                    except:
                        continue

                question_obj.save()

            messages.add_message(request, messages.INFO, "Created questions succefully.")
        except:
            messages.add_message(request, messages.ERROR, "Error creating questions. Make sure the ontology is valid and matches the configuration.")
            success = False
            raise ValueError("Abort transaction")

        try:
            checked = set()
            while SUBTHEME_SET:
                subtheme = SUBTHEME_SET.pop()
                if subtheme.iri in checked: continue
                checked.add(subtheme.iri)

                new_subtheme, created = Subthemes.objects.get_or_create(iri=subtheme.iri)
                new_subtheme.name = get_label(subtheme, LANGUAGE)
                new_subtheme.save()
                if created: _created_subthemes += 1
                else:
                    _updated_subthemes += 1
                    new_subtheme.subtheme.clear()

                for restriction in subtheme.is_a:
                    if isinstance(restriction, ThingClass):
                        SUBTHEME_SET.append(restriction)
                        SUBTHEME_MAP[restriction].append(new_subtheme)

            del SUBTHEME_MAP[Thing]
            for subtheme, children in SUBTHEME_MAP.items():
                subtheme = Subthemes.objects.get(iri=subtheme.iri)
                for child in children:
                    child.subtheme.add(subtheme)
                    child.save()
            
            stack = [subtheme for subtheme in Subthemes.objects.filter(subthemes__isnull=True)]
            stack = []
            subtheme_count = {}
            processed = set()
            for x in Subthemes.objects.all():
                subtheme_count[x] = x.subthemes.all().count()
                if subtheme_count[x] == 0:
                    stack.append(x)
            while stack:
                current_subtheme = stack.pop()
                for question in current_subtheme.question_set.all():
                    for condition in question.condition.all():
                        current_subtheme.type.add(condition.type)
                current_subtheme.save()
                categories = current_subtheme.type.all()
                processed.add(current_subtheme)
                for parent_subtheme in current_subtheme.subtheme.all():
                    subtheme_count[parent_subtheme] -= 1
                    for category in categories:
                        parent_subtheme.type.add(category)
                    parent_subtheme.save()
                    if subtheme_count[parent_subtheme] == 0 and not parent_subtheme in processed: stack.append(parent_subtheme)
            messages.add_message(request, messages.INFO, "Added subthemes correctly.")
        except:
            messages.add_message(request, messages.ERROR, "Error creating subthemes. Make sure the ontology is valid and matches the configuration.")
            success = False
            raise ValueError("Abort transaction")
    
        if make_config:
            OWL_Upload_Configs(configs=CONFIGS).save()

    if success:
        messages.add_message(request, messages.SUCCESS, f"""Categories created: {_created_categories}, updated: {_updated_categories}
Questions created: {_created_question}, updated: {_updated_question}
Subthemes created: {_created_subthemes}, updated: {_updated_subthemes}
Conditions created: {_created_question_category_condition}
""")
    else:
        messages.add_message(request, messages.ERROR, "Couldn't upload OWL. Aborted all changes.")

    world.close()
